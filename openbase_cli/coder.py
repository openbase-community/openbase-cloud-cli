"""Delegation to the Openbase Coder CLI.

The ``openbase-coder`` command is a separate, non-bundled tool that owns the
login flow and devspace/agent features. This CLI shares its credential store
(``~/.openbase/auth.json``), so rather than reimplement login here we simply
invoke ``openbase-coder`` when it is installed. ``openbase coder ...`` proxies
straight through to it.
"""

from __future__ import annotations

import shutil
import subprocess

CODER_EXECUTABLE = "openbase-coder"


class CoderNotInstalledError(Exception):
    """The openbase-coder executable was not found on PATH."""

    def __init__(self) -> None:
        super().__init__(
            "The 'openbase-coder' command is not installed or not on your PATH.\n"
            "Install it (e.g. `uv tool install openbase-coder`) and try again."
        )


def coder_path() -> str:
    path = shutil.which(CODER_EXECUTABLE)
    if not path:
        raise CoderNotInstalledError
    return path


def run_coder(args: list[str]) -> int:
    """Run ``openbase-coder <args>`` inheriting stdio; return its exit code."""
    completed = subprocess.run([coder_path(), *args], check=False)
    return completed.returncode
