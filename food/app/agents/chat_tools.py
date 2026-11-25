from typing import Any

from app.agents.tools import ToolContext, ToolRegistry
from app.integrations.internal_api import InternalApi
from app.integrations.llm_base import ToolSpec
from app.models.enums import ActionType

_ITEMS_SCHEMA = {
    "type": "array",
    "description": "Menu items to order",
    "items": {
        "type": "object",
        "properties": {
            "item_id": {"type": "integer", "description": "Menu item id from list_menu"},
            "quantity": {"type": "integer", "description": "Number of portions, 1-50"},
        },
        "required": ["item_id", "quantity"],
    },
}


def _get_json(api: InternalApi, path: str, ctx: ToolContext) -> dict[str, Any]:
    resp = api.request("GET", path, ctx.auth)
    if resp.status_code != 200:
        return {"error": f"Lookup failed with status {resp.status_code}"}
    return {"data": resp.json()}


def build_registry(api: InternalApi) -> ToolRegistry:
    """Registry of chat tools. Read tools call the REST API; write tools only create pending actions."""
    registry = ToolRegistry()

    registry.register(
        ToolSpec("list_menu", "List the active menu items with prices and remaining portions.",
                 {"type": "object", "properties": {}}),
        lambda args, ctx: _get_json(api, "/api/menu", ctx),
    )
    registry.register(
        ToolSpec("list_my_orders", "List the signed-in user's recent orders.",
                 {"type": "object", "properties": {}}),
        lambda args, ctx: _get_json(api, "/api/orders", ctx),
    )
    registry.register(
        ToolSpec("get_order", "Get one order by id.",
                 {"type": "object", "properties": {"order_id": {"type": "integer"}}, "required": ["order_id"]}),
        lambda args, ctx: _get_json(api, f"/api/orders/{int(args['order_id'])}", ctx),
    )

    def search_knowledge(args: dict[str, Any], ctx: ToolContext) -> dict[str, Any]:
        hits = ctx.retriever.search(str(args.get("query", "")))
        ctx.citations.extend(hits)
        return {"passages": [{"document": h.document, "page": h.page, "excerpt": h.excerpt} for h in hits]}

    registry.register(
        ToolSpec("search_knowledge", "Search restaurant policy documents (hours, delivery, refunds, allergens).",
                 {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}),
        search_knowledge,
    )

    def propose_order(args: dict[str, Any], ctx: ToolContext) -> dict[str, Any]:
        items = [{"item_id": int(i["item_id"]), "quantity": int(i["quantity"])} for i in args.get("items", [])]
        row = ctx.pending.propose(ctx.user, ctx.chat_session_id, ActionType.CREATE_ORDER, {"items": items}, ctx.auth)
        ctx.pending_action_ids.append(row.id)
        return {"status": "pending_confirmation", "pending_action_id": row.id, "preview": row.preview}

    registry.register(
        ToolSpec("propose_create_order", "Prepare an order for the customer to confirm. Does not place it.",
                 {"type": "object", "properties": {"items": _ITEMS_SCHEMA}, "required": ["items"]}),
        propose_order,
        writes=True,
    )

    def propose_cancel(args: dict[str, Any], ctx: ToolContext) -> dict[str, Any]:
        row = ctx.pending.propose(ctx.user, ctx.chat_session_id, ActionType.CANCEL_ORDER,
                                  {"order_id": int(args["order_id"])}, ctx.auth)
        ctx.pending_action_ids.append(row.id)
        return {"status": "pending_confirmation", "pending_action_id": row.id, "preview": row.preview}

    registry.register(
        ToolSpec("propose_cancel_order", "Prepare cancelling an order for the customer to confirm. Does not cancel it.",
                 {"type": "object", "properties": {"order_id": {"type": "integer"}}, "required": ["order_id"]}),
        propose_cancel,
        writes=True,
    )
    return registry
