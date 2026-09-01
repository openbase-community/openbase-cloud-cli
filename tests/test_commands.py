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
def test_run_command_posts_oneoff_command(logged_in):
    _mock_dashboard()
    route = respx.post(f"{API}/stacks/stack-1/run/").mock(
        return_value=httpx.Response(
            200,
            json={
                "task_arn": "arn:aws:ecs:us-east-1:123:task/projects/run",
                "exit_code": 0,
                "stopped_reason": "",
                "lines": ["System check identified no issues."],
            },
        )
    )

    result = CliRunner().invoke(
        main,
        ["run", "-a", "api", "python", "manage.py", "check"],
    )

    assert result.exit_code == 0, result.output
    assert "System check identified no issues." in result.output
    assert route.calls.last.request.content == (
        b'{"command":["python","manage.py","check"],"shell_bin":"/bin/sh","memory":256}'
    )


@respx.mock
def test_run_command_options_after_command_pass_through(logged_in):
    # Flags that appear after COMMAND starts belong to the remote command, not
    # the CLI: --memory here must reach the app, not resize the task.
    _mock_dashboard()
    route = respx.post(f"{API}/stacks/stack-1/run/").mock(
        return_value=httpx.Response(
            200,
            json={"task_arn": "arn", "exit_code": 0, "stopped_reason": "", "lines": []},
        )
    )

    result = CliRunner().invoke(
        main,
        ["run", "-a", "api", "./script.sh", "--memory", "512", "--shell-bin", "x"],
    )

    assert result.exit_code == 0, result.output
    body = json.loads(route.calls.last.request.content)
    assert body["command"] == ["./script.sh", "--memory", "512", "--shell-bin", "x"]
    assert body["memory"] == 256
    assert body["shell_bin"] == "/bin/sh"


@respx.mock
def test_run_command_missing_exit_code_is_failure(logged_in):
    # A task that never ran to completion reports no exit code; that must not
    # look like success.
    _mock_dashboard()
    respx.post(f"{API}/stacks/stack-1/run/").mock(
        return_value=httpx.Response(
            200,
            json={
                "task_arn": "arn",
                "exit_code": None,
                "stopped_reason": "RESOURCE:MEMORY",
                "lines": [],
            },
        )
    )

    result = CliRunner().invoke(main, ["run", "-a", "api", "true"])

    assert result.exit_code != 0
    assert "did not run to completion" in result.output
    assert "RESOURCE:MEMORY" in result.output


@respx.mock
def test_logs_strips_terminal_escape_sequences(logged_in):
    _mock_dashboard()
    respx.get(f"{API}/stacks/stack-1/logs/").mock(
        return_value=httpx.Response(
            200,
            json={"lines": ["web: \x1b]0;pwned\x07\x1b[2Jhello\tworld"]},
        )
    )

    result = CliRunner().invoke(main, ["logs", "-a", "api"])

    assert result.exit_code == 0, result.output
    assert "\x1b" not in result.output
    assert "\x07" not in result.output
    # Tabs survive (Rich renders them as spaces); the text is intact.
    assert "hello" in result.output
    assert "world" in result.output


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
def test_config_set_creates_new_var(logged_in):
    _mock_dashboard()
    respx.get(f"{API}/resources/res-1/config-vars/").mock(return_value=httpx.Response(200, json=[]))
    route = respx.post(f"{API}/resources/res-1/config-vars/").mock(
        return_value=httpx.Response(200, json={"key": "FOO", "value": "bar"})
    )

    result = CliRunner().invoke(main, ["config", "set", "-a", "api", "FOO=bar"])

    assert result.exit_code == 0, result.output
    body = json.loads(route.calls.last.request.content)
    assert body == {"key": "FOO", "value": "bar", "is_secret": False}


@respx.mock
def test_config_set_overwrites_existing_var(logged_in):
    _mock_dashboard()
    respx.get(f"{API}/resources/res-1/config-vars/").mock(
        return_value=httpx.Response(
            200, json=[{"key": "FOO", "id": "cv-1", "is_secret": False, "value": "old"}]
        )
    )
    delete = respx.delete(f"{API}/config-vars/cv-1/").mock(return_value=httpx.Response(204))
    post = respx.post(f"{API}/resources/res-1/config-vars/").mock(
        return_value=httpx.Response(200, json={"key": "FOO", "value": "new"})
    )

    result = CliRunner().invoke(main, ["config", "set", "-a", "api", "FOO=new"])

    assert result.exit_code == 0, result.output
    assert delete.called  # old var removed before recreate
    assert json.loads(post.calls.last.request.content)["value"] == "new"


@respx.mock
def test_config_set_rejects_bad_pair(logged_in):
    _mock_dashboard()
    result = CliRunner().invoke(main, ["config", "set", "-a", "api", "NOEQUALS"])
    assert result.exit_code != 0
    assert "Invalid KEY=VALUE" in result.output


@respx.mock
def test_config_set_reads_secret_from_stdin_without_echoing_it(logged_in):
    _mock_dashboard()
    respx.get(f"{API}/resources/res-1/config-vars/").mock(
        return_value=httpx.Response(200, json=[])
    )
    route = respx.post(f"{API}/resources/res-1/config-vars/").mock(
        return_value=httpx.Response(200, json={"key": "TOKEN", "value": None})
    )

    result = CliRunner().invoke(
        main,
        ["config", "set", "-a", "api", "--secret-stdin", "TOKEN"],
        input="stdin-only-secret\n",
    )

    assert result.exit_code == 0, result.output
    assert "stdin-only-secret" not in result.output
    assert json.loads(route.calls.last.request.content) == {
        "key": "TOKEN",
        "value": "stdin-only-secret",
        "is_secret": True,
    }


@respx.mock
def test_config_set_rejects_ambiguous_secret_stdin(logged_in):
    _mock_dashboard()

    result = CliRunner().invoke(
        main,
        ["config", "set", "-a", "api", "--secret-stdin", "TOKEN", "OTHER=value"],
        input="stdin-only-secret\n",
    )

    assert result.exit_code != 0
    assert "cannot be combined" in result.output


@respx.mock
def test_webhook_set(logged_in):
    _mock_dashboard()
    route = respx.put(f"{API}/stacks/stack-1/webhook/").mock(
        return_value=httpx.Response(200, json={"url": "https://h.example/x", "secret": "abc123"})
    )
    result = CliRunner().invoke(main, ["webhook", "set", "-a", "api", "https://h.example/x"])
    assert result.exit_code == 0, result.output
    assert json.loads(route.calls.last.request.content) == {"url": "https://h.example/x"}
    assert "abc123" in result.output  # secret shown so the user can verify signatures


@respx.mock
def test_webhook_set_with_explicit_secret(logged_in):
    _mock_dashboard()
    route = respx.put(f"{API}/stacks/stack-1/webhook/").mock(
        return_value=httpx.Response(200, json={"url": "https://h.example/x", "secret": "mine"})
    )
    result = CliRunner().invoke(
        main, ["webhook", "set", "-a", "api", "https://h.example/x", "--secret", "mine"]
    )
    assert result.exit_code == 0, result.output
    assert json.loads(route.calls.last.request.content) == {
        "url": "https://h.example/x",
        "secret": "mine",
    }


@respx.mock
def test_webhook_show(logged_in):
    _mock_dashboard()
    respx.get(f"{API}/stacks/stack-1/webhook/").mock(
        return_value=httpx.Response(200, json={"url": "https://h.example/x", "secret": "abc123"})
    )
    result = CliRunner().invoke(main, ["webhook", "-a", "api"])
    assert result.exit_code == 0, result.output
    assert "https://h.example/x" in result.output


@respx.mock
def test_webhook_unset(logged_in):
    _mock_dashboard()
    route = respx.delete(f"{API}/stacks/stack-1/webhook/").mock(
        return_value=httpx.Response(200, json={"detail": "Release webhook removed."})
    )
    result = CliRunner().invoke(main, ["webhook", "unset", "-a", "api"])
    assert result.exit_code == 0, result.output
    assert route.called


@respx.mock
def test_config_unset_removes_var(logged_in):
    _mock_dashboard()
    respx.get(f"{API}/resources/res-1/config-vars/").mock(
        return_value=httpx.Response(
            200, json=[{"key": "FOO", "id": "cv-1", "is_secret": False, "value": "bar"}]
        )
    )
    delete = respx.delete(f"{API}/config-vars/cv-1/").mock(return_value=httpx.Response(204))

    result = CliRunner().invoke(main, ["config", "unset", "-a", "api", "FOO"])

    assert result.exit_code == 0, result.output
    assert delete.called


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
