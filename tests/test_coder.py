from __future__ import annotations

from click.testing import CliRunner

from openbase_cli import coder
from openbase_cli.cli import main


def test_coder_passthrough_invokes_executable(monkeypatch):
    calls = {}

    def fake_run(args):
        calls["args"] = args
        return 0

    monkeypatch.setattr(coder, "run_coder", fake_run)
    # auth_commands imported run_coder by name; patch there too.
    monkeypatch.setattr("openbase_cli.commands.auth_commands.run_coder", fake_run)

    result = CliRunner().invoke(main, ["coder", "devspaces", "status"])
    assert result.exit_code == 0, result.output
    assert calls["args"] == ["devspaces", "status"]


def test_login_delegates_to_coder_login(monkeypatch):
    calls = {}

    def fake_run(args):
        calls["args"] = args
        return 0

    monkeypatch.setattr("openbase_cli.commands.auth_commands.run_coder", fake_run)
    result = CliRunner().invoke(main, ["login"])
    assert result.exit_code == 0, result.output
    assert calls["args"] == ["login"]


def test_login_forwards_extra_args(monkeypatch):
    calls = {}

    def fake_run(args):
        calls["args"] = args
        return 0

    monkeypatch.setattr("openbase_cli.commands.auth_commands.run_coder", fake_run)
    result = CliRunner().invoke(main, ["login", "--no-browser"])
    assert result.exit_code == 0, result.output
    assert calls["args"] == ["login", "--no-browser"]


def test_coder_not_installed_is_friendly(monkeypatch):
    def boom(args):
        raise coder.CoderNotInstalledError

    monkeypatch.setattr("openbase_cli.commands.auth_commands.run_coder", boom)
    result = CliRunner().invoke(main, ["coder", "whoami"])
    assert result.exit_code == 1
    assert "openbase-coder" in result.output


def test_run_coder_missing_executable(monkeypatch):
    monkeypatch.setattr(coder.shutil, "which", lambda _: None)
    try:
        coder.run_coder(["login"])
    except coder.CoderNotInstalledError as exc:
        assert "not installed" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected CoderNotInstalledError")


def _capture_exec(monkeypatch):
    calls = {}

    def fake_exec(args):
        calls["args"] = args
        return 0

    monkeypatch.setattr("openbase_cli.commands.agent_commands.exec_coder", fake_exec)
    return calls


def test_codex_forwards_every_argument_to_openbase_coder(monkeypatch):
    calls = _capture_exec(monkeypatch)

    result = CliRunner().invoke(main, ["codex", "--local", "-m", "o3", "--help"])

    assert result.exit_code == 0, result.output
    assert calls["args"] == ["codex", "--local", "-m", "o3", "--help"]


def test_claude_forwards_every_argument_to_openbase_coder(monkeypatch):
    calls = _capture_exec(monkeypatch)

    result = CliRunner().invoke(main, ["claude", "-c"])

    assert result.exit_code == 0, result.output
    assert calls["args"] == ["claude", "-c"]


def test_agent_launchers_are_listed_in_help():
    result = CliRunner().invoke(main, ["--help"])

    assert "codex" in result.output
    assert "claude" in result.output


def test_agent_launcher_without_openbase_coder_is_friendly(monkeypatch):
    monkeypatch.setattr(coder.shutil, "which", lambda _: None)

    result = CliRunner().invoke(main, ["codex"])

    assert result.exit_code == 1
    assert "openbase-coder" in result.output


def test_exec_coder_replaces_the_process(monkeypatch):
    calls = {}
    monkeypatch.setattr(coder.shutil, "which", lambda _: "/bin/openbase-coder")
    monkeypatch.setattr(coder.sys, "platform", "darwin")

    def fake_execv(path, argv):
        calls["exec"] = (path, argv)
        raise SystemExit(0)

    monkeypatch.setattr(coder.os, "execv", fake_execv)
    try:
        coder.exec_coder(["claude", "-c"])
    except SystemExit:
        pass
    assert calls["exec"] == (
        "/bin/openbase-coder",
        ["/bin/openbase-coder", "claude", "-c"],
    )
