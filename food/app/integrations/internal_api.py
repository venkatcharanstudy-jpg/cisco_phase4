from typing import Any, Protocol

import httpx

from app.exceptions import ServiceUnavailableError


class InternalApi(Protocol):
    def request(self, method: str, path: str, auth_header: str, json: Any = None,
                headers: dict[str, str] | None = None) -> httpx.Response: ...


class InternalApiClient:
    """Calls this app's own REST API so chat tools obey the same auth and rules as the UI."""

    def __init__(self, base_url: str, timeout: float = 10.0, http: httpx.Client | None = None) -> None:
        self._base = base_url.rstrip("/")
        self._http = http or httpx.Client(timeout=timeout)

    def request(self, method: str, path: str, auth_header: str, json: Any = None,
                headers: dict[str, str] | None = None) -> httpx.Response:
        merged = {"Authorization": auth_header, **(headers or {})}
        try:
            return self._http.request(method, f"{self._base}{path}", json=json, headers=merged)
        except httpx.HTTPError as exc:
            raise ServiceUnavailableError("Internal API unreachable", code="internal_unavailable") from exc
