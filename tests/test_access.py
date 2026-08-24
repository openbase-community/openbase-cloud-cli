from __future__ import annotations

import json

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
                    "stack": {
                        "id": "stack-1",
                        "status": "healthy",
                        "aws_region": "us-east-1",
                        "owner_email": "owner@acme.com",
                    },
                    "hostnames": [{"hostname": "api.acme.com"}],
                },
            ],
        }
    ],
    "stacks": [],
}

ACCESS = {
    "collaborators": [{"id": "col-1", "email": "dev@acme.com"}],
    "invitations": [{"id": "inv-1", "email": "new@acme.com"}],
}


def _mock_dashboard():
    respx.get(f"{API}/dashboard/").mock(return_value=httpx.Response(200, json=DASHBOARD))


@respx.mock
def test_access_lists_owner_collaborators_and_invitations(logged_in):
    _mock_dashboard()
    respx.get(f"{API}/stacks/stack-1/collaborators/").mock(
        return_value=httpx.Response(200, json=ACCESS)
    )

    result = CliRunner().invoke(main, ["access", "-a", "api"])

    assert result.exit_code == 0, result.output
    assert "owner@acme.com" in result.output and "owner" in result.output
    assert "dev@acme.com" in result.output
    assert "new@acme.com" in result.output and "invited" in result.output


@respx.mock
def test_access_json(logged_in):
    _mock_dashboard()
    respx.get(f"{API}/stacks/stack-1/collaborators/").mock(
        return_value=httpx.Response(200, json=ACCESS)
    )

    result = CliRunner().invoke(main, ["access", "-a", "api", "--json"])

    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["owner"] == "owner@acme.com"
    assert data["collaborators"][0]["email"] == "dev@acme.com"


@respx.mock
def test_access_add_sends_invitation(logged_in):
    _mock_dashboard()
    route = respx.post(f"{API}/stacks/stack-1/collaborator-invitations/").mock(
        return_value=httpx.Response(201, json={"id": "inv-2", "email": "erik@acme.com"})
    )

    result = CliRunner().invoke(main, ["access", "add", "-a", "api", "erik@acme.com"])

    assert result.exit_code == 0, result.output
    assert json.loads(route.calls.last.request.content) == {"email": "erik@acme.com"}
    assert "Invited erik@acme.com" in result.output


@respx.mock
def test_access_remove_collaborator(logged_in):
    _mock_dashboard()
    respx.get(f"{API}/stacks/stack-1/collaborators/").mock(
        return_value=httpx.Response(200, json=ACCESS)
    )
    delete = respx.delete(f"{API}/collaborators/col-1/").mock(return_value=httpx.Response(204))

    result = CliRunner().invoke(main, ["access", "remove", "-a", "api", "DEV@acme.com"])

    assert result.exit_code == 0, result.output
    assert delete.called
    assert "Removed collaborator" in result.output


@respx.mock
def test_access_remove_revokes_pending_invitation(logged_in):
    _mock_dashboard()
    respx.get(f"{API}/stacks/stack-1/collaborators/").mock(
        return_value=httpx.Response(200, json=ACCESS)
    )
    delete = respx.delete(f"{API}/collaborator-invitations/inv-1/").mock(
        return_value=httpx.Response(204)
    )

    result = CliRunner().invoke(main, ["access", "remove", "-a", "api", "new@acme.com"])

    assert result.exit_code == 0, result.output
    assert delete.called
    assert "Revoked pending invitation" in result.output


@respx.mock
def test_access_remove_unknown_email_fails(logged_in):
    _mock_dashboard()
    respx.get(f"{API}/stacks/stack-1/collaborators/").mock(
        return_value=httpx.Response(200, json=ACCESS)
    )

    result = CliRunner().invoke(main, ["access", "remove", "-a", "api", "ghost@acme.com"])

    assert result.exit_code != 0
    assert "no access or pending invitation" in result.output


@respx.mock
def test_config_set_secret(logged_in):
    _mock_dashboard()
    respx.get(f"{API}/resources/res-1/config-vars/").mock(return_value=httpx.Response(200, json=[]))
    route = respx.post(f"{API}/resources/res-1/config-vars/").mock(
        return_value=httpx.Response(200, json={"key": "API_KEY", "is_secret": True})
    )

    result = CliRunner().invoke(main, ["config", "set", "--secret", "-a", "api", "API_KEY=shh"])

    assert result.exit_code == 0, result.output
    body = json.loads(route.calls.last.request.content)
    assert body == {"key": "API_KEY", "value": "shh", "is_secret": True}
    assert "secret" in result.output.lower()
