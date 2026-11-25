from dataclasses import dataclass
from typing import Any, Protocol

import httpx
from sqlalchemy.orm import Session

from app.exceptions import ConflictError, NotFoundError, ServiceUnavailableError
from app.integrations.internal_api import InternalApi
from app.models.enums import ActionStatus, ActionType
from app.models.user import User


@dataclass(frozen=True)
class ExecutionResult:
    ok: bool
    outcome: dict[str, Any]


class ActionExecutor(Protocol):
    """Command: knows how to re-validate and execute one kind of pending write."""

    def fresh_preview(self, payload: dict[str, Any], auth: str, api: InternalApi) -> dict[str, Any]: ...

    def execute(self, payload: dict[str, Any], auth: str, api: InternalApi, idempotency_key: str) -> ExecutionResult: ...


def _money(value: Any) -> str:
    return f"{float(value):.2f}"


class CreateOrderExecutor:
    def fresh_preview(self, payload: dict[str, Any], auth: str, api: InternalApi) -> dict[str, Any]:
        resp = api.request("GET", "/api/menu", auth)
        if resp.status_code != 200:
            raise ServiceUnavailableError("Could not verify menu prices", code="internal_unavailable")
        menu = {m["id"]: m for m in resp.json()}
        lines = []
        total = 0.0
        for line in payload["items"]:
            item = menu.get(line["item_id"])
            if item is None:
                raise ConflictError(f"Menu item {line['item_id']} is no longer available", code="item_unavailable")
            subtotal = float(item["price"]) * line["quantity"]
            total += subtotal
            lines.append({"item_id": item["id"], "title": item["title"], "quantity": line["quantity"],
                          "unit_price": _money(item["price"])})
        return {"items": lines, "total": _money(total)}

    def execute(self, payload: dict[str, Any], auth: str, api: InternalApi, idempotency_key: str) -> ExecutionResult:
        body = {"items": [{"item_id": i["item_id"], "quantity": i["quantity"]} for i in payload["items"]]}
        resp = api.request("POST", "/api/orders", auth, json=body, headers={"Idempotency-Key": idempotency_key})
        if resp.status_code in (200, 201):
            return ExecutionResult(True, {"order_id": resp.json()["id"]})
        return ExecutionResult(False, {"http_status": resp.status_code, "error": resp.text[:300]})


class CancelOrderExecutor:
    def fresh_preview(self, payload: dict[str, Any], auth: str, api: InternalApi) -> dict[str, Any]:
        resp = api.request("GET", f"/api/orders/{payload['order_id']}", auth)
        if resp.status_code != 200:
            raise NotFoundError("Order not found")
        order = resp.json()
        if order["status"] != "CONFIRMED":
            raise ConflictError(f"Order is {order['status']} and cannot be cancelled", code="invalid_transition")
        return {"order_id": order["id"], "status": order["status"], "total": _money(order["total"])}

    def execute(self, payload: dict[str, Any], auth: str, api: InternalApi, idempotency_key: str) -> ExecutionResult:
        resp = api.request("POST", f"/api/orders/{payload['order_id']}/cancel", auth)
        if resp.status_code == 200:
            return ExecutionResult(True, {"order_id": payload["order_id"], "status": "CANCELLED"})
        return ExecutionResult(False, {"http_status": resp.status_code, "error": resp.text[:300]})


EXECUTORS: dict[str, ActionExecutor] = {
    ActionType.CREATE_ORDER: CreateOrderExecutor(),
    ActionType.CANCEL_ORDER: CancelOrderExecutor(),
}
