"""The CLI attributes mutations to the calling agent.

The client sends ``X-Openbase-Agent-Id`` on every request. An explicit
``OPENBASE_AGENT_ID`` wins; otherwise Codex's native ``CODEX_THREAD_ID`` is
used automatically. When neither is set the server records "human". The
``releases`` table surfaces the server-recorded attribution.
"""

from __future__ import annotations

import json

import httpx
import respx
from click.testing import CliRunner

from openbase_cli.cli import main
from tests.test_commands import API, _mock_dashboard

_AGENT_UUID = "cac5ccd4-2499-4784-a2a6-05e3b2caa98b"


def _mock_config_set():
    respx.get(f"{API}/resources/res-1/config-vars/").mock(return_value=httpx.Response(200, json=[]))
    return respx.post(f"{API}/resources/res-1/config-vars/").mock(
        return_value=httpx.Response(200, json={"key": "FOO", "value": "bar"})
    )


@respx.mock
def test_mutation_sends_agent_header_when_env_set(logged_in, monkeypatch):
    monkeypatch.setenv("OPENBASE_AGENT_ID", _AGENT_UUID)
    monkeypatch.setenv("CODEX_THREAD_ID", "11111111-1111-1111-1111-111111111111")
    _mock_dashboard()
    route = _mock_config_set()

    result = CliRunner().invoke(main, ["config", "set", "-a", "api", "FOO=bar"])

    assert result.exit_code == 0, result.output
    assert route.calls.last.request.headers["X-Openbase-Agent-Id"] == _AGENT_UUID


@respx.mock
def test_mutation_uses_codex_thread_id_automatically(logged_in, monkeypatch):
    monkeypatch.delenv("OPENBASE_AGENT_ID", raising=False)
    monkeypatch.setenv("CODEX_THREAD_ID", _AGENT_UUID)
    _mock_dashboard()
    route = _mock_config_set()

    result = CliRunner().invoke(main, ["config", "set", "-a", "api", "FOO=bar"])

    assert result.exit_code == 0, result.output
    assert route.calls.last.request.headers["X-Openbase-Agent-Id"] == _AGENT_UUID


@respx.mock
def test_mutation_omits_agent_header_when_env_unset(logged_in, monkeypatch):
    monkeypatch.delenv("OPENBASE_AGENT_ID", raising=False)
    monkeypatch.delenv("CODEX_THREAD_ID", raising=False)
    _mock_dashboard()
    route = _mock_config_set()

    result = CliRunner().invoke(main, ["config", "set", "-a", "api", "FOO=bar"])

    assert result.exit_code == 0, result.output
    assert "X-Openbase-Agent-Id" not in route.calls.last.request.headers


@respx.mock
def test_releases_shows_agent_column(logged_in):
    _mock_dashboard()
    respx.get(f"{API}/resources/res-1/runs/").mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "created_at": "2026-08-12T10:00:00Z",
                    "operation": "config_sync",
                    "status": "succeeded",
                    "commit_sha": "",
                    "git_ref": "",
                    "agent_id": _AGENT_UUID,
                    "summary": "ok",
                }
            ],
        )
    )
    result = CliRunner().invoke(main, ["releases", "-a", "api"])
    assert result.exit_code == 0, result.output
    assert "AGENT" in result.output
    # Rich may wrap the UUID across the column; assert on a stable prefix.
    assert "cac5ccd4" in result.output


@respx.mock
def test_releases_json_passes_through_agent_id(logged_in):
    _mock_dashboard()
    respx.get(f"{API}/resources/res-1/runs/").mock(
        return_value=httpx.Response(
            200,
            json=[{"operation": "deploy", "status": "succeeded", "agent_id": "human"}],
        )
    )
    result = CliRunner().invoke(main, ["releases", "-a", "api", "--json"])
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)[0]["agent_id"] == "human"
