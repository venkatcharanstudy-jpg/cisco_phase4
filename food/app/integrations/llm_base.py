from dataclasses import dataclass, field
from typing import Any, Literal, Protocol


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    parameters: dict[str, Any]


@dataclass(frozen=True)
class ToolCall:
    name: str
    args: dict[str, Any]
    signature: str | None = None


@dataclass(frozen=True)
class Turn:
    """Provider-neutral conversation turn. The adapter maps these to the vendor format."""

    role: Literal["user", "model", "tool"]
    text: str | None = None
    tool_call: ToolCall | None = None
    tool_result: dict[str, Any] | None = None


@dataclass
class LLMReply:
    text: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)


class LLMClient(Protocol):
    def generate(self, system: str, turns: list[Turn], tools: list[ToolSpec]) -> LLMReply: ...
