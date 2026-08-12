from __future__ import annotations

import pytest

from openbase_cli.apps import App, AppResolutionError, list_apps, resolve_app
from openbase_cli.commands.logs_commands import _new_lines


class FakeClient:
    def __init__(self, dashboard):
        self._dashboard = dashboard

    def dashboard(self):
        return self._dashboard


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
                    "stack": {"id": "stack-1", "status": "healthy"},
                    "hostnames": [{"hostname": "api.acme.com"}],
                    "latest_run": None,
                },
                {
                    "id": "res-2",
                    "display_name": "web",
                    "resource_type": "static-site",
                    "deployment_status": "deployed",
                    "stack": None,
                    "frontends": [{"asset_hostname": "cdn.acme.com"}],
                },
            ],
        },
        {
            "title": "Beta",
            "resources": [
                {
                    "id": "res-3",
                    "display_name": "api",  # duplicate name, different project
                    "resource_type": "server",
                    "deployment_status": "draft",
                    "stack": {"id": "stack-3"},
                },
            ],
        },
    ]
}


def test_list_apps_flattens_projects():
    apps = list_apps(FakeClient(DASHBOARD))
    assert {(a.name, a.project) for a in apps} == {
        ("api", "Acme"),
        ("web", "Acme"),
        ("api", "Beta"),
    }


def test_hostnames_and_url():
    apps = {a.resource_id: a for a in list_apps(FakeClient(DASHBOARD))}
    assert apps["res-1"].web_url == "https://api.acme.com"
    assert apps["res-2"].hostnames == ["cdn.acme.com"]


def test_resolve_unique_by_name():
    app = resolve_app(FakeClient(DASHBOARD), "web")
    assert app.resource_id == "res-2"


def test_resolve_case_insensitive():
    app = resolve_app(FakeClient(DASHBOARD), "WEB")
    assert app.resource_id == "res-2"


def test_resolve_ambiguous_raises():
    with pytest.raises(AppResolutionError, match="ambiguous"):
        resolve_app(FakeClient(DASHBOARD), "api")


def test_resolve_unknown_lists_known():
    with pytest.raises(AppResolutionError, match="Known apps"):
        resolve_app(FakeClient(DASHBOARD), "nope")


def test_resolve_empty_name():
    with pytest.raises(AppResolutionError, match="No app specified"):
        resolve_app(FakeClient(DASHBOARD), "")


def test_stack_id_and_web_url_helpers():
    app = App(
        resource_id="r",
        name="n",
        project="p",
        resource_type="server",
        status="deployed",
        stack={"id": "s"},
        hostnames=[],
        latest_run=None,
    )
    assert app.stack_id == "s"
    assert app.web_url is None


@pytest.mark.parametrize(
    "previous,current,expected",
    [
        ([], ["a", "b"], ["a", "b"]),
        (["a", "b"], ["a", "b"], []),
        (["a", "b"], ["a", "b", "c"], ["c"]),
        (["a", "b"], ["c", "d"], ["c", "d"]),  # no overlap -> whole window
        (["x", "a", "b"], ["a", "b", "c"], ["c"]),  # overlap not at window start
    ],
)
def test_new_lines(previous, current, expected):
    assert _new_lines(previous, current) == expected
