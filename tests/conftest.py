from __future__ import annotations

import base64
import json
import time

import pytest

TEST_HOST = "https://test.openbase.cloud"


def make_jwt(claims: dict) -> str:
    """Build an unsigned-looking JWT whose payload carries ``claims``."""

    def seg(obj: dict) -> str:
        raw = json.dumps(obj).encode()
        return base64.urlsafe_b64encode(raw).decode().rstrip("=")

    return f"{seg({'alg': 'none'})}.{seg(claims)}.sig"


@pytest.fixture
def auth_path(tmp_path, monkeypatch):
    """Point the shared credential store at a temp file for the test."""
    path = tmp_path / "auth.json"
    monkeypatch.setattr("openbase_cli.config.AUTH_JSON_PATH", path)
    monkeypatch.setenv("OPENBASE_HOST", TEST_HOST)
    return path


@pytest.fixture
def logged_in(auth_path):
    """Write valid, non-expiring credentials so no refresh is needed."""
    auth_path.write_text(
        json.dumps(
            {
                "access_token": make_jwt({"email": "dev@example.com"}),
                "refresh_token": "refresh-abc",
                "access_expires_at": time.time() + 3600,
                "refresh_rejected_at": 0,
            }
        )
    )
    return auth_path
