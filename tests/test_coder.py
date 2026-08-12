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
