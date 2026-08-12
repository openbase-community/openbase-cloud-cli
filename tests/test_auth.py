from __future__ import annotations

import json
import time

import httpx
import pytest
import respx

from openbase_cli.auth import (
    LoginRequiredError,
    TokenManager,
    decode_jwt_claims_unverified,
)
from tests.conftest import TEST_HOST, make_jwt

REFRESH_URL = f"{TEST_HOST}/_allauth/app/v1/tokens/refresh"


def test_decode_jwt_reads_claims():
    token = make_jwt({"email": "a@b.com"})
    assert decode_jwt_claims_unverified(token)["email"] == "a@b.com"


def test_decode_jwt_garbage_is_empty():
    assert decode_jwt_claims_unverified("not-a-jwt") == {}


def test_store_and_load_roundtrip(auth_path):
    mgr = TokenManager()
    mgr.store_tokens(access_token="acc", refresh_token="ref", expires_in=999)
    assert json.loads(auth_path.read_text())["refresh_token"] == "ref"
    assert TokenManager().is_logged_in is True


def test_valid_access_token_no_refresh(logged_in):
    # logged_in writes a non-expiring access token; no HTTP should occur.
    with respx.mock:
        token = TokenManager().get_access_token()
    assert decode_jwt_claims_unverified(token)["email"] == "dev@example.com"


@respx.mock
def test_refresh_when_expired(auth_path):
    auth_path.write_text(
        json.dumps(
            {
                "access_token": "old",
                "refresh_token": "ref-1",
                "access_expires_at": time.time() - 10,  # expired
            }
        )
    )
    respx.post(REFRESH_URL).mock(
        return_value=httpx.Response(
            200,
            json={
                "meta": {
                    "access_token": "new-access",
                    "refresh_token": "ref-2",
                    "access_token_expires_in": 300,
                }
            },
        )
    )
    mgr = TokenManager()
    assert mgr.get_access_token() == "new-access"
    # New refresh token persisted for next time.
    assert json.loads(auth_path.read_text())["refresh_token"] == "ref-2"


@respx.mock
def test_refresh_rejected_requires_login(auth_path):
    auth_path.write_text(
        json.dumps({"access_token": "old", "refresh_token": "dead", "access_expires_at": 0})
    )
    respx.post(REFRESH_URL).mock(return_value=httpx.Response(401, json={}))
    with pytest.raises(LoginRequiredError):
        TokenManager().get_access_token()


def test_not_logged_in_requires_login(auth_path):
    with pytest.raises(LoginRequiredError):
        TokenManager().get_access_token()


def test_clear_removes_file(logged_in):
    assert logged_in.is_file()
    TokenManager().clear()
    assert not logged_in.is_file()
