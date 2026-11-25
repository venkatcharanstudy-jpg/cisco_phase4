from dataclasses import dataclass, field
from typing import Any

from app.agents.tools import ToolContext, ToolRegistry
from app.exceptions import ServiceUnavailableError
from app.integrations.llm_base import LLMClient, Turn

SYSTEM_PROMPT = (
    "You are the assistant for a restaurant ordering app. Answer briefly. "
    "Use the tools for menu, order, and policy questions; never invent prices, stock, or policies. "
    "To place or cancel an order, call the propose tools: the customer must confirm in the app before anything is "
    "changed. Never say an order is placed until a tool result says it was confirmed."
)


@dataclass
class AgentResult:
    reply: str
    tool_runs: list[dict[str, Any]] = field(default_factory=list)


class SingleAgent:
    """One agent with a bounded tool loop. The LLM is injected behind the LLMClient interface."""

    def __init__(self, llm: LLMClient, registry: ToolRegistry, max_iterations: int) -> None:
        self._llm = llm
        self._registry = registry
        self._max = max_iterations

    def run(self, history: list[Turn], user_text: str, ctx: ToolContext) -> AgentResult:
        turns = [*history, Turn(role="user", text=user_text)]
        tool_runs: list[dict[str, Any]] = []
        specs = self._registry.specs()
        for _ in range(self._max):
            reply = self._llm.generate(SYSTEM_PROMPT, turns, specs)
            if not reply.tool_calls:
                return AgentResult(reply=reply.text.strip() or "I could not produce an answer.", tool_runs=tool_runs)
            for call in reply.tool_calls:
                turns.append(Turn(role="model", tool_call=call))
                result = self._registry.invoke(call, ctx)
                tool_runs.append({"tool": call.name, "args": call.args, "result": result})
                turns.append(Turn(role="tool", tool_call=call, tool_result=result))
        raise ServiceUnavailableError("The assistant needed too many steps. Please rephrase.", code="agent_loop_limit")
