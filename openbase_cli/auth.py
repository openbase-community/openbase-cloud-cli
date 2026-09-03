"""Authentication: a read-only token store that delegates refresh to Openbase Coder.

Credentials live in the shared ``~/.openbase/auth.json`` written by the
Openbase Coder CLI. This module only ever READS that file: when the cached
access token is still valid it is used directly, and when it is expired (or
the on-disk ``refresh_rejected_at`` marker says the login is dead) refresh is
delegated to ``openbase-coder auth access-token --json`` as a subprocess.

The coder CLI owns all writes to auth.json and serializes refresh across
processes with a file lock. Refreshing in-process here would race it: allauth
refresh tokens are single-use, so two processes refreshing the same token
milliseconds apart get one winner and one 401 — and an unlocked loser can
clobber the winner's rotated token on disk, logging the user out.

Only the subset needed by a read-mostly PaaS client is implemented here; the
full lifecycle (login, refresh, machine tokens, device registration) stays in
the coder CLI.
"""

from __future__ import annotations

import base64
import json
import subprocess
import time
from typing import Any

from openbase_cli import config
from openbase_cli.coder import CoderNotInstalledError, coder_path

# Treat the cached access token as expired a little early so in-flight
# requests never race the clock.
_REFRESH_MARGIN_SECONDS = 60

# `openbase-coder auth access-token` exits with this code when only a new
# login can produce a token (see its docstring in the coder CLI).
_CODER_LOGIN_REQUIRED_EXIT_CODE = 4


class AuthError(Exception):
    """Base class for authentication failures."""


class LoginRequiredError(AuthError):
    """No usable credentials; the user must run ``openbase login``."""


class AuthTransientError(AuthError):
    """A retryable failure (network error or backend 5xx)."""


def decode_jwt_claims_unverified(token: str) -> dict[str, Any]:
    """Read identity claims from a token we already trust (our own on disk).

    Never use this for authorizing an inbound token — there is no signature
    check here.
    """
    parts = token.split(".")
    if len(parts) != 3:
        return {}
    segment = parts[1]
    padded = segment + "=" * (-len(segment) % 4)
    try:
        claims = json.loads(base64.urlsafe_b64decode(padded))
    except (ValueError, json.JSONDecodeError):
        return {}
    return claims if isinstance(claims, dict) else {}


class TokenManager:
    """Load the shared Openbase Cloud JWT credentials; delegate refresh."""

    def __init__(self, host: str | None = None):
        self._host = (host or config.host()).rstrip("/")
        self._access_token = ""
        self._refresh_token = ""
        self._access_expires_at = 0.0
        self._refresh_rejected_at = 0.0

    # -- persistence -------------------------------------------------------

    def load(self) -> None:
        path = config.AUTH_JSON_PATH
        if not path.is_file():
            self._access_token = self._refresh_token = ""
            self._access_expires_at = 0.0
            self._refresh_rejected_at = 0.0
            return
        try:
            data = json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            return  # torn read; keep whatever we have in memory
        self._access_token = data.get("access_token", "")
        self._refresh_token = data.get("refresh_token", "")
        self._access_expires_at = data.get("access_expires_at", 0) or 0
        self._refresh_rejected_at = data.get("refresh_rejected_at", 0) or 0

    def clear(self) -> None:
        self._access_token = self._refresh_token = ""
        self._access_expires_at = 0.0
        self._refresh_rejected_at = 0.0
        if config.AUTH_JSON_PATH.is_file():
            config.AUTH_JSON_PATH.unlink()

    # -- token state -------------------------------------------------------

    @property
    def is_logged_in(self) -> bool:
        self.load()
        return bool(self._refresh_token)

    def owner_email(self) -> str:
        """Best-effort email from the stored access token (may be empty)."""
        self.load()
        return decode_jwt_claims_unverified(self._access_token).get("email", "")

    def _access_is_valid(self) -> bool:
        return bool(self._access_token) and time.time() < (
            self._access_expires_at - _REFRESH_MARGIN_SECONDS
        )

    def get_access_token(self) -> str:
        """Return a valid access token, delegating refresh to openbase-coder."""
        self.load()
        if self._refresh_rejected_at:
            # The coder CLI recorded a definitive refresh rejection on disk;
            # no refresh attempt can recover, only a new login.
            raise LoginRequiredError("Login expired. Run 'openbase login' again.")
        if self._access_is_valid():
            return self._access_token
        if not self._refresh_token:
            raise LoginRequiredError("Not logged in. Run 'openbase login' first.")
        self._delegate_refresh_to_coder()
        return self._access_token

    def _delegate_refresh_to_coder(self) -> None:
        """Obtain a fresh access token via ``openbase-coder auth access-token``.

        The coder CLI performs the actual refresh under its cross-process
        file lock and writes the rotated tokens to auth.json itself; we only
        capture the token it prints. This module must never write auth.json.
        """
        try:
            executable = coder_path()
        except CoderNotInstalledError as exc:
            raise LoginRequiredError(
                "The 'openbase-coder' CLI is required to refresh the shared "
                "Openbase login but was not found on your PATH.\n"
                "Install it (e.g. `uv tool install openbase-coder`) and run "
                "'openbase login'."
            ) from exc

        try:
            completed = subprocess.run(
                [executable, "auth", "access-token", "--json"],
                capture_output=True,
                text=True,
                check=False,
                timeout=60,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise AuthTransientError(f"Token refresh failed: {exc}") from exc

        if completed.returncode == _CODER_LOGIN_REQUIRED_EXIT_CODE:
            raise LoginRequiredError("Not logged in. Run 'openbase login' first.")
        if completed.returncode != 0:
            detail = completed.stderr.strip() or completed.stdout.strip()
            raise AuthTransientError(
                f"Token refresh via openbase-coder failed"
                f" (exit {completed.returncode})" + (f": {detail}" if detail else ".")
            )

        try:
            payload = json.loads(completed.stdout)
            access_token = payload["access_token"]
        except (json.JSONDecodeError, TypeError, KeyError) as exc:
            raise AuthTransientError(
                "Token refresh via openbase-coder returned unparseable output."
            ) from exc
        if not access_token:
            raise AuthTransientError("Token refresh via openbase-coder returned an empty token.")
        self._access_token = access_token
        self._access_expires_at = payload.get("access_expires_at", 0) or 0
        self._refresh_rejected_at = 0.0
