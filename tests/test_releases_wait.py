from __future__ import annotations

import httpx
import respx
from click.testing import CliRunner

from openbase_cli.cli import main
from openbase_cli.commands.releases_commands import _rollout_verification
from tests.test_commands import API, _mock_dashboard

COMMIT_SHA = "a" * 40


def _run(status: str, **overrides) -> dict:
    return {
        "id": "run-1",
        "commit_sha": COMMIT_SHA,
        "git_ref": "refs/heads/main",
        "operation": "deploy",
        "status": status,
        "summary": "Deployment finished successfully." if status == "succeeded" else "",
        **overrides,
    }


def _invoke(*extra: str):
    return CliRunner().invoke(
        main,
        [
            "releases",
            "wait",
            "-a",
            "api",
            "--commit",
            COMMIT_SHA,
            "--operation",
            "deploy",
            "--poll-interval",
            "0.1",
            *extra,
        ],
    )


@respx.mock
def test_wait_tracks_run_until_success(logged_in, monkeypatch):
    _mock_dashboard()
    monkeypatch.setattr("openbase_cli.commands.releases_commands.time.sleep", lambda _delay: None)
    respx.get(f"{API}/resources/res-1/runs/").mock(
        side_effect=[
            httpx.Response(200, json=[]),
            httpx.Response(200, json=[_run("pending")]),
            httpx.Response(200, json=[_run("started")]),
            httpx.Response(200, json=[_run("succeeded")]),
        ]
    )

    result = _invoke()

    assert result.exit_code == 0, result.output
    assert "waiting for the webhook-created run" in result.output
    assert "is pending" in result.output
    assert "is started" in result.output
    assert "succeeded (deploy)" in result.output


@respx.mock
def test_wait_fails_with_release_summary(logged_in):
    _mock_dashboard()
    respx.get(f"{API}/resources/res-1/runs/").mock(
        return_value=httpx.Response(
            200,
            json=[_run("failed", summary="\x1b]0;spoofed\x07CodeBuild failed during BUILD")],
        )
    )

    result = _invoke()

    assert result.exit_code == 1
    assert "CodeBuild failed during BUILD" in result.output
    assert "\x1b" not in result.output
    assert "\x07" not in result.output


@respx.mock
def test_wait_fails_when_target_was_overtaken(logged_in):
    _mock_dashboard()
    newer_sha = "b" * 40
    respx.get(f"{API}/resources/res-1/runs/").mock(
        return_value=httpx.Response(
            200,
            json=[
                _run("started", id="run-2", commit_sha=newer_sha),
                _run("succeeded"),
            ],
        )
    )

    result = _invoke()

    assert result.exit_code == 1
    assert "overtaken" in result.output
    assert newer_sha[:12] in result.output


@respx.mock
def test_wait_verifies_live_ecs_rollout(logged_in):
    _mock_dashboard()
    runs = respx.get(f"{API}/resources/res-1/runs/").mock(
        return_value=httpx.Response(200, json=[_run("succeeded")])
    )
    status = respx.get(f"{API}/stacks/stack-1/status/").mock(
        return_value=httpx.Response(
            200,
            json={
                "status": "succeeded",
                "expected_image_tag": "new-tag",
                "last_status_payload": {
                    "services": [
                        {
                            "component": "web",
                            "rollout_state": "COMPLETED",
                            "running": 1,
                            "desired": 1,
                            "pending": 0,
                            "image_tag": "new-tag",
                        },
                        {
                            "component": "worker",
                            "rollout_state": "COMPLETED",
                            "running": 1,
                            "desired": 1,
                            "pending": 0,
                            "image_tag": "new-tag",
                        },
                    ]
                },
            },
        )
    )

    result = _invoke("--verify-rollout")

    assert result.exit_code == 0, result.output
    assert "ECS rollout is stable" in result.output
    assert runs.call_count == 2
    assert status.called


@respx.mock
def test_wait_fails_on_ecs_rollout_failure(logged_in):
    _mock_dashboard()
    respx.get(f"{API}/resources/res-1/runs/").mock(
        return_value=httpx.Response(200, json=[_run("succeeded")])
    )
    respx.get(f"{API}/stacks/stack-1/status/").mock(
        return_value=httpx.Response(
            200,
            json={
                "status": "failed",
                "expected_image_tag": "new-tag",
                "last_status_payload": {
                    "services": [
                        {
                            "component": "web",
                            "rollout_state": "FAILED",
                            "running": 1,
                            "desired": 1,
                            "pending": 0,
                            "image_tag": "old-tag",
                        }
                    ]
                },
            },
        )
    )

    result = _invoke("--verify-rollout")

    assert result.exit_code == 1
    assert "ECS web rollout failed" in result.output


def test_rollout_waits_until_live_image_matches_expected_tag():
    state, detail = _rollout_verification(
        {
            "expected_image_tag": "new-tag",
            "last_status_payload": {
                "services": [
                    {
                        "component": "web",
                        "rollout_state": "COMPLETED",
                        "running": 1,
                        "desired": 1,
                        "pending": 0,
                        "image_tag": "old-tag",
                    }
                ]
            },
        }
    )

    assert state == "waiting"
    assert "waiting for new-tag" in detail


def test_wait_requires_full_commit_sha():
    result = CliRunner().invoke(
        main,
        [
            "releases",
            "wait",
            "-a",
            "api",
            "--commit",
            "abc123",
            "--operation",
            "deploy",
        ],
    )

    assert result.exit_code == 2
    assert "full 40-character" in result.output


def test_rollout_verification_rejects_frontend_operation():
    result = CliRunner().invoke(
        main,
        [
            "releases",
            "wait",
            "-a",
            "api",
            "--commit",
            COMMIT_SHA,
            "--operation",
            "frontend_deploy",
            "--verify-rollout",
        ],
    )

    assert result.exit_code == 2
    assert "only valid with --operation deploy" in result.output
