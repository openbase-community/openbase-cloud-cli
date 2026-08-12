"""Runtime configuration: the Openbase Cloud host and shared credential paths.

The CLI deliberately shares its on-disk login with the Openbase Coder CLI: both
read ``~/.openbase/auth.json``, and ``openbase login`` delegates to
``openbase-coder login``. Logging in with either tool logs you in for both.
"""

from __future__ import annotations

import os
from pathlib import Path

# Default Openbase Cloud web/API host. Overridable for staging or local dev.
DEFAULT_HOST = "https://app.openbase.cloud"

# Shared credential store, identical to openbase-coder's paths.py.
OPENBASE_BASE_DIR = Path.home() / ".openbase"
AUTH_JSON_PATH = OPENBASE_BASE_DIR / "auth.json"


def host() -> str:
    """Return the Openbase Cloud base URL, honouring env overrides.

    ``OPENBASE_API_URL`` (full URL) wins; ``OPENBASE_HOST`` is a convenience
    alias. Falls back to production.
    """
    raw = os.environ.get("OPENBASE_API_URL") or os.environ.get("OPENBASE_HOST") or DEFAULT_HOST
    return raw.rstrip("/")


def default_app() -> str | None:
    """App name from the environment, mirroring Heroku's ``HEROKU_APP``."""
    value = os.environ.get("OPENBASE_APP", "").strip()
    return value or None
