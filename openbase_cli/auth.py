"""Authentication: a small token store that piggybacks on Openbase Coder.

Credentials live in the shared ``~/.openbase/auth.json`` written by the
Openbase Coder CLI. This module reads that file, refreshes the short-lived JWT
access token against Openbase Cloud's allauth endpoint when needed, and (for
``openbase-deploy login``) runs the same browser OAuth+PKCE flow the coder CLI uses so
either tool can establish the shared session.

Only the subset needed by a read-mostly PaaS client is implemented here; the
full lifecycle (machine tokens, device registration) stays in the coder CLI.
"""

from __future__ import annotations

import base64
import json
import os
import time
from typing import Any

import httpx

from openbase_cli import config

# Refresh a little before expiry so in-flight requests never race the clock.
_REFRESH_MARGIN_SECONDS = 60


class AuthError(Exception):
    """Base class for authentication failures."""


class LoginRequiredError(AuthError):
    """No usable credentials; the user must run ``openbase-deploy login``."""


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
    """Load/refresh the shared Openbase Cloud JWT credentials."""

    def __init__(self, host: str | None = None):
        self._host = (host or config.host()).rstrip("/")
        self._access_token = ""
        self._refresh_token = ""
        self._access_expires_at = 0.0

    # -- persistence -------------------------------------------------------

    def load(self) -> None:
        path = config.AUTH_JSON_PATH
        if not path.is_file():
            self._access_token = self._refresh_token = ""
            self._access_expires_at = 0.0
            return
        try:
            data = json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            return  # torn read; keep whatever we have in memory
        self._access_token = data.get("access_token", "")
        self._refresh_token = data.get("refresh_token", "")
        self._access_expires_at = data.get("access_expires_at", 0) or 0

    def save(self) -> None:
        path = config.AUTH_JSON_PATH
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(
            {
                "access_token": self._access_token,
                "refresh_token": self._refresh_token,
                "access_expires_at": self._access_expires_at,
                "refresh_rejected_at": 0,
            },
            indent=2,
        )
        tmp = path.with_suffix(f".json.tmp{os.getpid()}")
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as fh:
            fh.write(payload)
        os.replace(tmp, path)

    def clear(self) -> None:
        self._access_token = self._refresh_token = ""
        self._access_expires_at = 0.0
        if config.AUTH_JSON_PATH.is_file():
            config.AUTH_JSON_PATH.unlink()

    def store_tokens(self, *, access_token: str, refresh_token: str, expires_in: int = 300) -> None:
        self._access_token = access_token
        self._refresh_token = refresh_token
        self._access_expires_at = time.time() + expires_in
        self.save()

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
        """Return a valid access token, refreshing from the backend if needed."""
        self.load()
        if self._access_is_valid():
            return self._access_token
        if not self._refresh_token:
            raise LoginRequiredError("Not logged in. Run 'openbase-deploy login' first.")
        self._refresh()
        return self._access_token

    def _refresh(self) -> None:
        url = f"{self._host}/_allauth/app/v1/tokens/refresh"
        try:
            resp = httpx.post(url, json={"refresh_token": self._refresh_token}, timeout=15)
        except httpx.HTTPError as exc:
            raise AuthTransientError(f"Token refresh failed: {exc}") from exc

        if resp.status_code in (400, 401, 403):
            raise LoginRequiredError("Login expired. Run 'openbase-deploy login' again.")
        if resp.status_code >= 500:
            raise AuthTransientError(f"Token refresh failed (status {resp.status_code}).")
        resp.raise_for_status()

        data = resp.json() if resp.content else {}
        meta = data.get("meta", {}) if isinstance(data, dict) else {}
        payload = data.get("data", {}) if isinstance(data, dict) else {}
        self._access_token = (
            meta.get("access_token") or payload.get("access_token") or data.get("access_token", "")
        )
        new_refresh = (
            meta.get("refresh_token") or payload.get("refresh_token") or data.get("refresh_token")
        )
        if new_refresh:
            self._refresh_token = new_refresh
        expires_in = (
            meta.get("access_token_expires_in") or payload.get("access_token_expires_in") or 300
        )
        self._access_expires_at = time.time() + expires_in
        self.save()
