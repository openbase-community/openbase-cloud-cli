"""The 'app' abstraction.

Heroku addresses everything by app name (``-a NAME``). The Openbase Cloud
equivalent is a *deployment resource* (a deployed backend/frontend within a
project). This module flattens the dashboard into a list of apps and resolves a
name to one, raising friendly errors for the not-found and ambiguous cases.

Logs and status live on the resource's *stack*, so :class:`App` exposes both
the resource id and the stack id.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from openbase_cli.api import ApiError, Client


class AppResolutionError(Exception):
    """A requested app name could not be uniquely resolved."""


@dataclass(frozen=True)
class App:
    resource_id: str
    name: str
    project: str
    resource_type: str
    status: str
    stack: dict[str, Any] | None
    hostnames: list[str]
    latest_run: dict[str, Any] | None

    @property
    def stack_id(self) -> str | None:
        return (self.stack or {}).get("id")

    @property
    def primary_hostname(self) -> str | None:
        return self.hostnames[0] if self.hostnames else None

    @property
    def web_url(self) -> str | None:
        host = self.primary_hostname
        return f"https://{host}" if host else None


def _hostnames_for(resource: dict[str, Any]) -> list[str]:
    names: list[str] = []
    for entry in resource.get("hostnames", []) or []:
        host = entry.get("hostname") if isinstance(entry, dict) else None
        if host:
            names.append(host)
    for frontend in resource.get("frontends", []) or []:
        host = frontend.get("asset_hostname") if isinstance(frontend, dict) else None
        if host:
            names.append(host)
    # Preserve order, drop duplicates.
    return list(dict.fromkeys(names))


def _app_from_resource(project_title: str, resource: dict[str, Any]) -> App:
    return App(
        resource_id=resource.get("id", ""),
        name=resource.get("display_name", ""),
        project=project_title,
        resource_type=resource.get("resource_type", ""),
        status=resource.get("deployment_status", "") or "",
        stack=resource.get("stack"),
        hostnames=_hostnames_for(resource),
        latest_run=resource.get("latest_run"),
    )


def list_apps(client: Client) -> list[App]:
    """Return every app the logged-in user can see, across all projects."""
    dashboard = client.dashboard()
    apps: list[App] = []
    for project in dashboard.get("projects", []) or []:
        title = project.get("title") or project.get("identifier") or "—"
        for resource in project.get("resources", []) or []:
            apps.append(_app_from_resource(title, resource))
    return apps


def resolve_app(client: Client, name: str) -> App:
    """Resolve an app name to a single :class:`App`.

    Matching is case-insensitive on the resource display name. Raises
    :class:`AppResolutionError` with actionable text when there is no match or
    more than one.
    """
    if not name:
        raise AppResolutionError("No app specified. Pass -a/--app NAME or set OPENBASE_APP.")
    apps = list_apps(client)
    exact = [a for a in apps if a.name == name]
    if len(exact) == 1:
        return exact[0]
    lowered = name.lower()
    ci = [a for a in apps if a.name.lower() == lowered]
    if len(ci) == 1:
        return ci[0]
    matches = exact or ci
    if not matches:
        known = ", ".join(sorted(a.name for a in apps)) or "(none)"
        raise AppResolutionError(f"No app named '{name}'. Known apps: {known}")
    where = ", ".join(f"{a.name} (project {a.project})" for a in matches)
    raise AppResolutionError(
        f"App name '{name}' is ambiguous across projects: {where}. "
        "App names must be unique to address them by name."
    )


def require_stack_id(app: App) -> str:
    """Return the app's stack id or explain why logs/status are unavailable."""
    stack_id = app.stack_id
    if not stack_id:
        raise ApiError(
            f"App '{app.name}' has no provisioned stack yet, so it has no logs or "
            "status. Deploy it first."
        )
    return stack_id
