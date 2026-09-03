from __future__ import annotations

import json
import subprocess
import time

import pytest

from openbase_cli import auth as auth_module
from openbase_cli.auth import (
    AuthTransientError,
    LoginRequiredError,
    TokenManager,
    decode_jwt_claims_unverified,
)
from openbase_cli.coder import CoderNotInstalledError


def _forbid_subprocess(monkeypatch):
    """Fail the test if the coder delegation subprocess is ever spawned."""

    def boom(*args, **kwargs):  # pragma: no cover - failure path
        raise AssertionError("subprocess.run must not be called")

    monkeypatch.setattr(auth_module.subprocess, "run", boom)
    monkeypatch.setattr(auth_module, "coder_path", lambda: "/fake/openbase-coder")


def _mock_coder(monkeypatch, *, returncode=0, stdout="", stderr=""):
    """Mock `openbase-coder auth access-token --json` and record invocations."""
    calls: list[list[str]] = []

    def fake_run(argv, **kwargs):
        calls.append(argv)
        return subprocess.CompletedProcess(argv, returncode, stdout=stdout, stderr=stderr)

    monkeypatch.setattr(auth_module, "coder_path", lambda: "/fake/openbase-coder")
    monkeypatch.setattr(auth_module.subprocess, "run", fake_run)
    return calls


def test_decode_jwt_reads_claims():
    from tests.conftest import make_jwt

    jwt = make_jwt({"email": "a@b.com"})
    assert decode_jwt_claims_unverified(jwt)["email"] == "a@b.com"


def test_decode_jwt_garbage_is_empty():
    assert decode_jwt_claims_unverified("not-a-jwt") == {}


def test_valid_access_token_uses_cache_without_subprocess(logged_in, monkeypatch):
    # logged_in writes a non-expiring access token; no delegation may occur.
    _forbid_subprocess(monkeypatch)
    token = TokenManager().get_access_token()
    assert decode_jwt_claims_unverified(token)["email"] == "dev@example.com"


def test_rejected_login_short_circuits_without_subprocess(auth_path, monkeypatch):
    auth_path.write_text(
        json.dumps(
            {
                "access_token": "still-valid-looking",
                "refresh_token": "ref-1",
                "access_expires_at": time.time() + 3600,
                "refresh_rejected_at": time.time() - 5,
            }
        )
    )
    _forbid_subprocess(monkeypatch)
    with pytest.raises(LoginRequiredError):
        TokenManager().get_access_token()


def test_expired_token_delegates_refresh_to_coder(auth_path, monkeypatch):
    before = json.dumps(
        {
            "access_token": "old",
            "refresh_token": "ref-1",
            "access_expires_at": time.time() - 10,  # expired
            "refresh_rejected_at": 0,
        }
    )
    auth_path.write_text(before)
    calls = _mock_coder(
        monkeypatch,
        stdout=json.dumps({"access_token": "new-access", "access_expires_at": time.time() + 300}),
    )

    mgr = TokenManager()
    assert mgr.get_access_token() == "new-access"
    assert calls == [["/fake/openbase-coder", "auth", "access-token", "--json"]]
    # The coder CLI owns auth.json writes; this CLI must not touch the file.
    assert auth_path.read_text() == before


def test_coder_login_required_exit_maps_to_login_required(auth_path, monkeypatch):
    auth_path.write_text(
        json.dumps({"access_token": "old", "refresh_token": "dead", "access_expires_at": 0})
    )
    _mock_coder(monkeypatch, returncode=4, stderr="Refresh token was rejected.")
    with pytest.raises(LoginRequiredError, match="openbase login"):
        TokenManager().get_access_token()


def test_coder_other_failure_is_transient(auth_path, monkeypatch):
    auth_path.write_text(
        json.dumps({"access_token": "old", "refresh_token": "ref-1", "access_expires_at": 0})
    )
    _mock_coder(monkeypatch, returncode=1, stderr="backend 503")
    with pytest.raises(AuthTransientError, match="backend 503"):
        TokenManager().get_access_token()


def test_coder_unparseable_output_is_transient(auth_path, monkeypatch):
    auth_path.write_text(
        json.dumps({"access_token": "old", "refresh_token": "ref-1", "access_expires_at": 0})
    )
    _mock_coder(monkeypatch, stdout="not json")
    with pytest.raises(AuthTransientError, match="unparseable"):
        TokenManager().get_access_token()


def test_coder_missing_binary_maps_to_login_required(auth_path, monkeypatch):
    auth_path.write_text(
        json.dumps({"access_token": "old", "refresh_token": "ref-1", "access_expires_at": 0})
    )

    def missing():
        raise CoderNotInstalledError

    monkeypatch.setattr(auth_module, "coder_path", missing)
    with pytest.raises(LoginRequiredError, match="openbase-coder"):
        TokenManager().get_access_token()


def test_not_logged_in_requires_login(auth_path, monkeypatch):
    _forbid_subprocess(monkeypatch)
    with pytest.raises(LoginRequiredError):
        TokenManager().get_access_token()


def test_clear_removes_file(logged_in):
    assert logged_in.is_file()
    TokenManager().clear()
    assert not logged_in.is_file()
