from __future__ import annotations

import httpx
import respx
from click.testing import CliRunner

from openbase_cli.cli import main
from tests.conftest import TEST_HOST


@respx.mock
def test_account(logged_in):
    respx.get(f"{TEST_HOST}/api/users/me/").mock(
        return_value=httpx.Response(
            200,
            json={
                "email": "dev@example.com",
                "first_name": "Dev",
                "last_name": "Eloper",
                "balance": "12.50",
                "active_subscription": True,
                "email_verified": True,
            },
        )
    )
    result = CliRunner().invoke(main, ["account"])
    assert result.exit_code == 0, result.output
    assert "dev@example.com" in result.output
    assert "active" in result.output


@respx.mock
def test_usage(logged_in):
    respx.get(f"{TEST_HOST}/api/openbase/usage/").mock(
        return_value=httpx.Response(
            200,
            json={
                "monthly_limit_cents": 2000,
                "usage_month_start": "2026-08-01",
                "sandbox_spend_cents": 500,
                "sandbox_remaining_cents": 1500,
                "sandbox_spend_percent": 25,
                "deployment_spend_cents": 100,
                "deployment_remaining_cents": 1900,
                "deployment_spend_percent": 5,
                "llm_spend_cents": 0,
                "llm_remaining_cents": 2000,
                "llm_spend_percent": 0,
                "payg_enabled": False,
                "payg_supported": True,
            },
        )
    )
    result = CliRunner().invoke(main, ["usage"])
    assert result.exit_code == 0, result.output
    assert "$20.00" in result.output  # monthly limit
    assert "$5.00" in result.output  # sandbox spend
    assert "Sandbox" in result.output


@respx.mock
def test_usage_json(logged_in):
    respx.get(f"{TEST_HOST}/api/openbase/usage/").mock(
        return_value=httpx.Response(200, json={"monthly_limit_cents": 2000})
    )
    result = CliRunner().invoke(main, ["usage", "--json"])
    assert result.exit_code == 0, result.output
    assert "monthly_limit_cents" in result.output


@respx.mock
def test_workspaces(logged_in):
    respx.get(f"{TEST_HOST}/api/openbase/devspaces/").mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "id": "ws-1",
                    "kind": "standard",
                    "status": "running",
                    "instance_type": "t3.large",
                    "monthly_usage_hours": 12.3,
                    "monthly_spend_cents": 456,
                }
            ],
        )
    )
    result = CliRunner().invoke(main, ["workspaces"])
    assert result.exit_code == 0, result.output
    assert "ws-1" in result.output
    assert "$4.56" in result.output


@respx.mock
def test_projects(logged_in):
    respx.get(f"{TEST_HOST}/api/openbase/projects/").mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "identifier": "acme",
                    "title": "Acme",
                    "github_repo_name": "acme-api",
                    "created_at": "2026-01-01",
                }
            ],
        )
    )
    result = CliRunner().invoke(main, ["projects"])
    assert result.exit_code == 0, result.output
    assert "acme" in result.output
    assert "Acme" in result.output
