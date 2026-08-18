from __future__ import annotations

import httpx
import respx
from click.testing import CliRunner

from openbase_cli.cli import main
from tests.conftest import TEST_HOST

API = f"{TEST_HOST}/api/openbase/deployment"

DASHBOARD = {
    "projects": [
        {
            "title": "Acme",
            "resources": [
                {
                    "id": "res-1",
                    "display_name": "api",
                    "resource_type": "server",
                    "deployment_status": "deployed",
                    "stack": {"id": "stack-1", "status": "healthy", "aws_region": "us-east-1"},
                    "hostnames": [{"hostname": "api.acme.com"}],
                },
            ],
        }
    ],
    "stacks": [],
}


def _mock_dashboard():
    respx.get(f"{API}/dashboard/").mock(return_value=httpx.Response(200, json=DASHBOARD))


@respx.mock
def test_apps_lists(logged_in):
    _mock_dashboard()
    result = CliRunner().invoke(main, ["apps"])
    assert result.exit_code == 0, result.output
    assert "api" in result.output
    assert "Acme" in result.output


@respx.mock
def test_apps_json(logged_in):
    _mock_dashboard()
    result = CliRunner().invoke(main, ["apps", "--json"])
    assert result.exit_code == 0, result.output
    assert '"stack_id": "stack-1"' in result.output


@respx.mock
def test_logs_snapshot(logged_in):
    _mock_dashboard()
    respx.get(f"{API}/stacks/stack-1/logs/").mock(
        return_value=httpx.Response(200, json={"lines": ["boom 1", "boom 2"]})
    )
    result = CliRunner().invoke(main, ["logs", "-a", "api"])
    assert result.exit_code == 0, result.output
    assert "boom 1" in result.output
    assert "boom 2" in result.output


@respx.mock
def test_logs_uses_since_minutes(logged_in):
    _mock_dashboard()
    route = respx.get(f"{API}/stacks/stack-1/logs/").mock(
        return_value=httpx.Response(200, json={"lines": []})
    )
    result = CliRunner().invoke(main, ["logs", "-a", "api", "-n", "42"])
    assert result.exit_code == 0, result.output
    assert route.calls.last.request.url.params["since_minutes"] == "42"


@respx.mock
def test_status(logged_in):
    _mock_dashboard()
    respx.get(f"{API}/stacks/stack-1/status/").mock(
        return_value=httpx.Response(
            200, json={"status": "healthy", "aws_region": "us-east-1", "latest_run": {}}
        )
    )
    result = CliRunner().invoke(main, ["ps", "-a", "api"])
    assert result.exit_code == 0, result.output
    assert "healthy" in result.output


@respx.mock
def test_config_hides_secrets(logged_in):
    _mock_dashboard()
    respx.get(f"{API}/resources/res-1/config-vars/").mock(
        return_value=httpx.Response(
            200,
            json=[
                {"key": "DEBUG", "is_secret": False, "value": "false"},
                {"key": "SECRET_KEY", "is_secret": True, "value": None},
            ],
        )
    )
    result = CliRunner().invoke(main, ["config", "-a", "api"])
    assert result.exit_code == 0, result.output
    assert "DEBUG" in result.output and "false" in result.output
    assert "secret" in result.output.lower()


@respx.mock
def test_releases(logged_in):
    _mock_dashboard()
    respx.get(f"{API}/resources/res-1/runs/").mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "created_at": "2026-08-12T10:00:00Z",
                    "operation": "deploy",
                    "status": "succeeded",
                    "commit_sha": "abcdef1234",
                    "git_ref": "main",
                    "summary": "ok",
                }
            ],
        )
    )
    result = CliRunner().invoke(main, ["releases", "-a", "api"])
    assert result.exit_code == 0, result.output
    assert "deploy" in result.output
    assert "main@abcdef1" in result.output


def test_whoami_requires_login(auth_path):
    # auth_path exists but no credentials file written -> not logged in.
    result = CliRunner().invoke(main, ["whoami"])
    assert result.exit_code == 1
    assert "Not logged in" in result.output


@respx.mock
def test_unknown_app_errors(logged_in):
    _mock_dashboard()
    result = CliRunner().invoke(main, ["logs", "-a", "ghost"])
    assert result.exit_code == 1
    assert "No app named 'ghost'" in result.output


@respx.mock
def test_health_check_shows_platform_default(logged_in):
    _mock_dashboard()
    respx.get(f"{API}/stacks/stack-1/status/").mock(
        return_value=httpx.Response(200, json={"web_health_check_path": ""})
    )
    result = CliRunner().invoke(main, ["health-check", "-a", "api"])
    assert result.exit_code == 0, result.output
    assert "/api/csrf/ (platform default)" in result.output


@respx.mock
def test_health_check_sets_path(logged_in):
    _mock_dashboard()
    route = respx.patch(f"{API}/stacks/stack-1/").mock(
        return_value=httpx.Response(200, json={"web_health_check_path": "/healthz"})
    )
    result = CliRunner().invoke(main, ["health-check", "/healthz", "-a", "api"])
    assert result.exit_code == 0, result.output
    assert route.called
    assert "set to /healthz" in result.output
    assert "next infrastructure apply" in result.output


@respx.mock
def test_health_check_unset(logged_in):
    _mock_dashboard()
    respx.patch(f"{API}/stacks/stack-1/").mock(
        return_value=httpx.Response(200, json={"web_health_check_path": ""})
    )
    result = CliRunner().invoke(main, ["health-check", "--unset", "-a", "api"])
    assert result.exit_code == 0, result.output
    assert "platform" in result.output
