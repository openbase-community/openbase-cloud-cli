"""Browser-based OAuth (PKCE) login against Openbase Cloud.

Mirrors the Openbase Coder CLI flow so the resulting ``~/.openbase/auth.json``
is interchangeable between the two tools:

1. Open the browser to ``/o/authorize/`` with a PKCE challenge.
2. Receive the code on a localhost callback and exchange it at ``/o/token/``.
3. Trade that OAuth token for the long-lived JWT refresh pair used by the API.
"""

from __future__ import annotations

import base64
import hashlib
import html
import json
import os
import secrets
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlencode, urljoin, urlparse

import httpx

from openbase_cli import config


def create_pkce_verifier() -> str:
    return base64.urlsafe_b64encode(os.urandom(40)).decode("ascii").rstrip("=")


def create_pkce_challenge(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")


_SUCCESS_HTML = b"""<!doctype html>
<html><head><meta charset="utf-8"><title>Openbase login complete</title>
<style>body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
margin:0;padding:48px;color:#18181b}main{margin:0 auto;max-width:560px}</style></head>
<body><main><h1>Logged in successfully</h1>
<p>The Openbase CLI has received your login. You can return to the terminal.</p>
</main></body></html>
"""


class _CallbackHandler(BaseHTTPRequestHandler):
    server_version = "OpenbaseCLIOAuth/1.0"

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != getattr(self.server, "callback_path", "/oauth/callback"):
            self._respond(404, b"Not found", content_type="text/plain; charset=utf-8")
            return
        params = {k: v[0] for k, v in parse_qs(parsed.query).items()}
        if "code" not in params and "error" not in params:
            self._respond(
                400, b"Missing OAuth callback parameters", content_type="text/plain; charset=utf-8"
            )
            return
        expected_state = getattr(self.server, "expected_state", "")
        if expected_state and params.get("state") != expected_state:
            self._respond(409, b"<h1>Older login attempt ignored</h1>")
            return
        self.server.result = params  # type: ignore[attr-defined]
        self._respond(200, _SUCCESS_HTML)
        self.server.done.set()  # type: ignore[attr-defined]

    def _respond(
        self, status: int, body: bytes, *, content_type: str = "text/html; charset=utf-8"
    ) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args) -> None:  # silence stdlib request logging
        return


class _CallbackServer(HTTPServer):
    allow_reuse_address = True


def _wait_for_callback(redirect_uri: str, *, expected_state: str) -> dict[str, str]:
    parsed = urlparse(redirect_uri)
    server = _CallbackServer((parsed.hostname or "127.0.0.1", parsed.port or 80), _CallbackHandler)
    server.timeout = 1
    server.done = threading.Event()  # type: ignore[attr-defined]
    server.result = {}  # type: ignore[attr-defined]
    server.callback_path = parsed.path or "/oauth/callback"  # type: ignore[attr-defined]
    server.expected_state = expected_state  # type: ignore[attr-defined]
    try:
        while not server.done.wait(timeout=0):  # type: ignore[attr-defined]
            server.handle_request()
    finally:
        server.server_close()
    return server.result  # type: ignore[attr-defined]


def _exchange_code_for_oauth_token(
    *, host: str, code: str, redirect_uri: str, verifier: str
) -> str:
    resp = httpx.post(
        f"{host}/o/token/",
        data={
            "grant_type": "authorization_code",
            "client_id": config.oauth_client_id(),
            "code": code,
            "redirect_uri": redirect_uri,
            "code_verifier": verifier,
        },
        timeout=30,
    )
    resp.raise_for_status()
    token = resp.json().get("access_token", "")
    if not token:
        raise RuntimeError("OAuth login succeeded but returned no access token.")
    return token


def _exchange_oauth_for_jwts(*, host: str, oauth_token: str) -> tuple[str, str, int]:
    resp = httpx.post(
        f"{host}/api/openbase/auth/cli/token-exchange/",
        headers={"Authorization": f"Bearer {oauth_token}"},
        timeout=30,
    )
    resp.raise_for_status()
    payload = resp.json()
    access = payload.get("access_token", "")
    refresh = payload.get("refresh_token", "")
    expires_in = int(payload.get("access_token_expires_in") or 300)
    if not access or not refresh:
        raise RuntimeError("Token exchange returned no JWT access/refresh pair.")
    return access, refresh, expires_in


def build_authorize_url(*, host: str, redirect_uri: str, state: str, challenge: str) -> str:
    query = urlencode(
        {
            "response_type": "code",
            "client_id": config.oauth_client_id(),
            "redirect_uri": redirect_uri,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            "state": state,
        }
    )
    return f"{urljoin(host + '/', 'o/authorize/')}?{query}"


def run_browser_login(*, host: str, echo, open_browser: bool = True) -> tuple[str, str, int]:
    """Drive the full browser login and return ``(access, refresh, expires_in)``.

    ``echo`` is a callable (e.g. ``click.echo``) used for user-facing output so
    this module stays free of a hard Click dependency.
    """
    redirect_uri = config.oauth_redirect_uri()
    state = secrets.token_hex(24)
    verifier = create_pkce_verifier()
    auth_url = build_authorize_url(
        host=host,
        redirect_uri=redirect_uri,
        state=state,
        challenge=create_pkce_challenge(verifier),
    )

    echo("Opening browser for Openbase login...")
    echo(auth_url)
    if open_browser:
        webbrowser.open(auth_url)
    echo("Waiting for you to finish logging in (Ctrl-C to abort)...")

    callback = _wait_for_callback(redirect_uri, expected_state=state)
    if callback.get("error"):
        raise RuntimeError(
            f"OAuth login failed: {callback.get('error_description') or callback['error']}"
        )
    code = callback.get("code")
    if not code or callback.get("state") != state:
        raise RuntimeError("OAuth login failed: missing or mismatched authorization code.")

    oauth_token = _exchange_code_for_oauth_token(
        host=host, code=code, redirect_uri=redirect_uri, verifier=verifier
    )
    return _exchange_oauth_for_jwts(host=host, oauth_token=oauth_token)


def format_http_error(exc: httpx.HTTPStatusError) -> str:
    detail = exc.response.text
    try:
        detail = json.dumps(exc.response.json())
    except ValueError:
        pass
    return f"{exc.response.status_code} — {html.unescape(detail)}"
