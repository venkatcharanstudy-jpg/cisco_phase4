from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.agents.single_agent import SingleAgent
from app.agents.tools import ToolContext
from app.exceptions import NotFoundError
from app.integrations.internal_api import InternalApi
from app.integrations.llm_base import Turn
from app.models.chat import ChatMessage, ChatSession, PendingAction, ToolRun
from app.models.enums import ChatMode, MessageRole
from app.models.user import User
from app.rag.retriever import LexicalRetriever
from app.services.pending_action_service import PendingActionService
from app.services.rate_limiter import SlidingWindowRateLimiter


class ChatService:
    """Orchestrates one chat turn: rate limit, persist, run the agent, persist the reply and tool runs."""

    def __init__(self, session: Session, agent: SingleAgent, api: InternalApi, limiter: SlidingWindowRateLimiter,
                 pending_ttl_minutes: int, history_turns: int) -> None:
        self._session = session
        self._agent = agent
        self._api = api
        self._limiter = limiter
        self._ttl = pending_ttl_minutes
        self._history_turns = history_turns

    def send(self, user: User, auth: str, message: str, session_id: int | None) -> dict[str, Any]:
        self._limiter.hit(user.id)
        chat = self._session_for(user, session_id, message)
        seq = self._next_seq(chat.id)
        self._session.add(ChatMessage(session_id=chat.id, seq_no=seq, role=MessageRole.USER, content=message))
        self._session.commit()

        ctx = ToolContext(
            user=user,
            auth=auth,
            chat_session_id=chat.id,
            retriever=LexicalRetriever(self._session),
            pending=PendingActionService(self._session, self._api, self._ttl),
        )
        history = self._history(chat.id, exclude_seq=seq)
        result = self._agent.run(history, message, ctx)

        mode = self._mode(ctx)
        citations = [{"document": c.document, "page": c.page, "excerpt": c.excerpt} for c in ctx.citations]
        assistant = ChatMessage(
            session_id=chat.id,
            seq_no=seq + 1,
            role=MessageRole.ASSISTANT,
            content=result.reply,
            meta={"mode": mode, "citations": citations, "tools": ctx.tools_used},
        )
        self._session.add(assistant)
        self._session.flush()
        for run in result.tool_runs:
            self._session.add(ToolRun(message_id=assistant.id, tool_name=run["tool"], args=run["args"],
                                      result=run["result"], status="error" if "error" in run["result"] else "ok"))
        self._session.commit()

        pending = self._session.get(PendingAction, ctx.pending_action_ids[-1]) if ctx.pending_action_ids else None
        return {
            "session_id": chat.id,
            "reply": result.reply,
            "mode": mode,
            "citations": citations,
            "pending_action": pending_action_out(pending),
        }

    def _session_for(self, user: User, session_id: int | None, message: str) -> ChatSession:
        if session_id is None:
            chat = ChatSession(user_id=user.id, title=message[:120])
            self._session.add(chat)
            self._session.commit()
            return chat
        chat = self._session.get(ChatSession, session_id)
        if chat is None or chat.user_id != user.id:
            raise NotFoundError("Chat session not found")
        return chat

    def _next_seq(self, session_id: int) -> int:
        current = self._session.scalar(
            select(func.max(ChatMessage.seq_no)).where(ChatMessage.session_id == session_id)
        )
        return (current or 0) + 1

    def _history(self, session_id: int, exclude_seq: int) -> list[Turn]:
        rows = self._session.scalars(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id, ChatMessage.seq_no < exclude_seq)
            .order_by(ChatMessage.seq_no.desc())
            .limit(self._history_turns)
        ).all()
        turns = []
        for row in reversed(rows):
            role = "user" if row.role == MessageRole.USER else "model"
            turns.append(Turn(role=role, text=row.content))
        return turns

    @staticmethod
    def _mode(ctx: ToolContext) -> str:
        read_tools = {"list_menu", "list_my_orders", "get_order"}
        used = set(ctx.tools_used)
        if ctx.pending_action_ids:
            return ChatMode.AGENT
        if ctx.citations and used - {"search_knowledge"}:
            return ChatMode.MIXED
        if ctx.citations:
            return ChatMode.RAG
        if used & read_tools:
            return ChatMode.AGENT
        return ChatMode.GENERAL


def pending_action_out(row: PendingAction | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return {
        "id": row.id,
        "action": row.action,
        "status": row.status,
        "preview": row.preview,
        "outcome": row.outcome,
        "expires_at": row.expires_at.isoformat(),
    }
