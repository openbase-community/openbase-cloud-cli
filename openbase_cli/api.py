"""Thin HTTP client for the Openbase Cloud deployment API.

Wraps the ``/api/openbase/deployment/*`` endpoints with bearer auth sourced
from :class:`openbase_cli.auth.TokenManager`. Only the read-mostly surface the
CLI needs is exposed here.
"""

from __future__ import annotations

from typing import Any

import httpx

from openbase_cli import config
from openbase_cli.auth import LoginRequiredError, TokenManager

_BASE_PATH = "/api/openbase/deployment"


class ApiError(Exception):
    """A non-success response from the Openbase Cloud API."""

    def __init__(self, message: str, *, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class Client:
    """Authenticated JSON client for the deployment API."""

    def __init__(self, token_manager: TokenManager | None = None, host: str | None = None):
        self._host = (host or config.host()).rstrip("/")
        self._tokens = token_manager or TokenManager(self._host)

    def _request(
        self,
        method: str,
        path: str,
        *,
        timeout: float | httpx.Timeout = 30,
        **kwargs: Any,
    ) -> Any:
        token = self._tokens.get_access_token()
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
        url = f"{self._host}{path}"
        try:
            resp = httpx.request(method, url, headers=headers, timeout=timeout, **kwargs)
        except httpx.HTTPError as exc:
            raise ApiError(f"Could not reach Openbase Cloud: {exc}") from exc

        if resp.status_code == 401:
            raise LoginRequiredError("Login expired. Run 'openbase login' again.")
        if resp.status_code == 403:
            raise ApiError("You do not have access to that resource.", status_code=403)
        if resp.status_code == 404:
            raise ApiError("Not found.", status_code=404)
        if resp.status_code >= 400:
            raise ApiError(_error_detail(resp), status_code=resp.status_code)
        if not resp.content:
            return None
        return resp.json()

    # -- endpoints ---------------------------------------------------------

    def dashboard(self) -> dict[str, Any]:
        return self._request("GET", f"{_BASE_PATH}/dashboard/")

    def stack_logs(
        self,
        stack_id: str,
        *,
        since_minutes: int = 15,
        lines: int = 100,
        errors: bool = False,
    ) -> list[str]:
        data = self._request(
            "GET",
            f"{_BASE_PATH}/stacks/{stack_id}/logs/",
            params={"since_minutes": since_minutes, "lines": lines, "errors": str(errors).lower()},
        )
        return list(data.get("lines", [])) if isinstance(data, dict) else []

    def stack_run(
        self,
        stack_id: str,
        *,
        command: list[str],
        shell_bin: str = "/bin/sh",
        memory: int = 256,
    ) -> dict[str, Any]:
        # The backend holds this request open while the one-off ECS task runs
        # to completion, which routinely takes minutes (migrations, imports).
        # Read timeout sits just past the server's 30-minute hard cap on the
        # task so the CLI waits for the real outcome instead of abandoning a
        # command that is still running server-side — re-running after a
        # spurious client timeout could execute a non-idempotent command twice.
        return self._request(
            "POST",
            f"{_BASE_PATH}/stacks/{stack_id}/run/",
            json={"command": command, "shell_bin": shell_bin, "memory": memory},
            timeout=httpx.Timeout(30, read=1860),
        )

    def stack_status(self, stack_id: str) -> dict[str, Any]:
        return self._request("GET", f"{_BASE_PATH}/stacks/{stack_id}/status/")

    def stack_update(self, stack_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("PATCH", f"{_BASE_PATH}/stacks/{stack_id}/", json=payload)

    def get_stack_webhook(self, stack_id: str) -> dict[str, Any]:
        return self._request("GET", f"{_BASE_PATH}/stacks/{stack_id}/webhook/") or {}

    def set_stack_webhook(
        self, stack_id: str, *, url: str, secret: str | None = None
    ) -> dict[str, Any]:
        body: dict[str, Any] = {"url": url}
        if secret:
            body["secret"] = secret
        return self._request("PUT", f"{_BASE_PATH}/stacks/{stack_id}/webhook/", json=body)

    def unset_stack_webhook(self, stack_id: str) -> None:
        self._request("DELETE", f"{_BASE_PATH}/stacks/{stack_id}/webhook/")

    def resource_runs(self, resource_id: str) -> list[dict[str, Any]]:
        data = self._request("GET", f"{_BASE_PATH}/resources/{resource_id}/runs/")
        return data if isinstance(data, list) else data.get("results", [])

    def resource_config_vars(self, resource_id: str) -> list[dict[str, Any]]:
        data = self._request("GET", f"{_BASE_PATH}/resources/{resource_id}/config-vars/")
        return data if isinstance(data, list) else data.get("results", [])

    def set_config_var(self, resource_id: str, *, key: str, value: str) -> dict[str, Any]:
        """Create a plaintext (non-secret) config var. Secrets are managed in
        the dashboard; the CLI only handles readable Heroku-style vars."""
        return self._request(
            "POST",
            f"{_BASE_PATH}/resources/{resource_id}/config-vars/",
            json={"key": key, "value": value, "is_secret": False},
        )

    def delete_config_var(self, config_var_id: str) -> None:
        self._request("DELETE", f"{_BASE_PATH}/config-vars/{config_var_id}/")

    # -- account / workspace / usage --------------------------------------

    def me(self) -> dict[str, Any]:
        return self._request("GET", "/api/users/me/")

    def usage(self) -> dict[str, Any]:
        return self._request("GET", "/api/openbase/usage/")

    def devspaces(self) -> list[dict[str, Any]]:
        data = self._request("GET", "/api/openbase/devspaces/")
        return data if isinstance(data, list) else data.get("results", [])

    def projects(self) -> list[dict[str, Any]]:
        data = self._request("GET", "/api/openbase/projects/")
        return data if isinstance(data, list) else data.get("results", [])


def _error_detail(resp: httpx.Response) -> str:
    try:
        body = resp.json()
    except ValueError:
        return f"Openbase Cloud returned status {resp.status_code}."
    if isinstance(body, dict):
        for key in ("detail", "error", "message"):
            if body.get(key):
                return str(body[key])
    return f"Openbase Cloud returned status {resp.status_code}."
