from app.exceptions import ServiceUnavailableError
from app.integrations.gemini_client import _to_contents
from app.integrations.llm_base import LLMReply, ToolCall, Turn
from tests.conftest import ScriptedLLM

ALICE = ("alice", "Alice123")
ADMIN = ("admin", "Admin123")


def _capacity(client, item_id):
    menu = client.get("/api/menu", auth=ALICE).json()
    return next(m["capacity"] for m in menu if m["id"] == item_id)


def test_out_of_capacity_order_is_rejected_without_partial_write(seeded):
    _, client, ids = seeded
    resp = client.post(
        "/api/orders",
        json={"items": [{"item_id": ids["biryani"], "quantity": 1}, {"item_id": ids["dosa"], "quantity": 3}]},
        headers={"Idempotency-Key": "too-many"},
        auth=ALICE,
    )
    assert resp.status_code == 409
    assert _capacity(client, ids["biryani"]) == 5
    assert client.get("/api/orders", auth=ALICE).json() == []


def test_idempotency_key_replays_same_order_and_rejects_different_payload(seeded):
    _, client, ids = seeded
    body = {"items": [{"item_id": ids["dosa"], "quantity": 1}]}
    first = client.post("/api/orders", json=body, headers={"Idempotency-Key": "k1"}, auth=ALICE)
    replay = client.post("/api/orders", json=body, headers={"Idempotency-Key": "k1"}, auth=ALICE)
    assert first.status_code == 201
    assert replay.status_code == 200
    assert replay.json()["id"] == first.json()["id"]
    assert _capacity(client, ids["dosa"]) == 1

    different = {"items": [{"item_id": ids["biryani"], "quantity": 1}]}
    conflict = client.post("/api/orders", json=different, headers={"Idempotency-Key": "k1"}, auth=ALICE)
    assert conflict.status_code == 409


def test_cancel_restores_capacity_exactly_once(seeded):
    _, client, ids = seeded
    order = client.post("/api/orders", json={"items": [{"item_id": ids["dosa"], "quantity": 2}]},
                        headers={"Idempotency-Key": "c1"}, auth=ALICE).json()
    assert _capacity(client, ids["dosa"]) == 0

    assert client.post(f"/api/orders/{order['id']}/cancel", auth=ALICE).status_code == 200
    assert _capacity(client, ids["dosa"]) == 2

    second = client.post(f"/api/orders/{order['id']}/cancel", auth=ALICE)
    assert second.status_code == 409
    assert _capacity(client, ids["dosa"]) == 2


def test_customer_cannot_change_order_status_but_admin_can(seeded):
    _, client, ids = seeded
    order = client.post("/api/orders", json={"items": [{"item_id": ids["dosa"], "quantity": 1}]},
                        headers={"Idempotency-Key": "s1"}, auth=ALICE).json()
    forbidden = client.patch(f"/api/orders/{order['id']}/status", json={"status": "PREPARING"}, auth=ALICE)
    assert forbidden.status_code == 403
    allowed = client.patch(f"/api/orders/{order['id']}/status", json={"status": "PREPARING"}, auth=ADMIN)
    assert allowed.status_code == 200
    assert allowed.json()["status"] == "PREPARING"


def test_chat_proposed_order_is_created_only_once_on_confirm(seeded):
    app, client, ids = seeded
    # Script: the model proposes an order via a tool call, then answers in text.
    app.state.container.llm = ScriptedLLM(
        LLMReply(text="", tool_calls=[ToolCall(name="propose_create_order",
                                               args={"items": [{"item_id": ids["dosa"], "quantity": 1}]})]),
        LLMReply(text="Please confirm the order.", tool_calls=[]),
    )

    chat = client.post("/api/chat", json={"message": "order a dosa"}, auth=ALICE).json()
    action = chat["pending_action"]
    assert action["status"] == "PENDING"
    assert client.get("/api/orders", auth=ALICE).json() == []

    confirmed = client.post(f"/api/chat/actions/{action['id']}/confirm", auth=ALICE)
    assert confirmed.status_code == 200
    assert confirmed.json()["status"] == "CONFIRMED"
    assert len(client.get("/api/orders", auth=ALICE).json()) == 1

    again = client.post(f"/api/chat/actions/{action['id']}/confirm", auth=ALICE)
    assert again.status_code == 409
    assert len(client.get("/api/orders", auth=ALICE).json()) == 1


def test_llm_outage_returns_503_error_envelope(seeded):
    app, client, _ = seeded
    app.state.container.llm = ScriptedLLM(ServiceUnavailableError("down", code="llm_unavailable"))
    resp = client.post("/api/chat", json={"message": "hello"}, auth=ALICE)
    assert resp.status_code == 503
    body = resp.json()
    assert body["code"] == "llm_unavailable"
    assert "request_id" in body


def test_parallel_tool_calls_share_one_model_turn_and_one_result_turn():
    first = ToolCall(name="propose_cancel_order", args={"order_id": 1}, signature="sig")
    second = ToolCall(name="propose_cancel_order", args={"order_id": 2})
    turns = [
        Turn(role="user", text="cancel all"),
        Turn(role="model", tool_call=first),
        Turn(role="model", tool_call=second),
        Turn(role="tool", tool_call=first, tool_result={"ok": True}),
        Turn(role="tool", tool_call=second, tool_result={"ok": False}),
    ]
    contents = _to_contents(turns)
    assert [c["role"] for c in contents] == ["user", "model", "user"]
    assert [list(p)[0] for p in contents[1]["parts"]] == ["functionCall", "functionCall"]
    assert contents[1]["parts"][0]["thoughtSignature"] == "sig"
    assert contents[1]["parts"][1]["thoughtSignature"] == "skip_thought_signature_validator"
    assert len(contents[2]["parts"]) == 2
