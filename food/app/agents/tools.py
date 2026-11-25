from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from app.exceptions import AppError
from app.integrations.llm_base import ToolCall, ToolSpec
from app.models.user import User
from app.rag.retriever import Citation, Retriever
from app.services.pending_action_service import PendingActionService


@dataclass
class ToolContext:
    """Per-request state. The auth header belongs to the signed-in user, never to the model."""

    user: User
    auth: str
    chat_session_id: int
    retriever: Retriever
    pending: PendingActionService
    citations: list[Citation] = field(default_factory=list)
    pending_action_ids: list[int] = field(default_factory=list)
    tools_used: list[str] = field(default_factory=list)


ToolHandler = Callable[[dict[str, Any], ToolContext], dict[str, Any]]


@dataclass(frozen=True)
class RegisteredTool:
    spec: ToolSpec
    handler: ToolHandler
    writes: bool = False


class ToolRegistry:
    """Registry pattern: tools are looked up by name and never invoked with model-supplied credentials."""

    def __init__(self) -> None:
        self._tools: dict[str, RegisteredTool] = {}

    def register(self, spec: ToolSpec, handler: ToolHandler, writes: bool = False) -> None:
        self._tools[spec.name] = RegisteredTool(spec, handler, writes)

    def specs(self) -> list[ToolSpec]:
        return [t.spec for t in self._tools.values()]

    def invoke(self, call: ToolCall, ctx: ToolContext) -> dict[str, Any]:
        tool = self._tools.get(call.name)
        if tool is None:
            return {"error": f"Unknown tool '{call.name}'"}
        ctx.tools_used.append(call.name)
        try:
            return tool.handler(call.args or {}, ctx)
        except AppError as exc:
            return {"error": exc.message, "code": exc.code}
