import uuid
from datetime import timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config.database import utcnow
from app.exceptions import ConflictError, NotFoundError
from app.integrations.internal_api import InternalApi
from app.models.chat import PendingAction
from app.models.enums import ActionStatus
from app.models.user import User
from app.services.action_executors import EXECUTORS


class PendingActionService:
    """Stores chat-initiated writes as PENDING until the user confirms them in the UI."""

    def __init__(self, session: Session, api: InternalApi, ttl_minutes: int) -> None:
        self._session = session
        self._api = api
        self._ttl = timedelta(minutes=ttl_minutes)

    def propose(self, user: User, chat_session_id: int, action: str, payload: dict[str, Any], auth: str) -> PendingAction:
        preview = EXECUTORS[action].fresh_preview(payload, auth, self._api)
        row = PendingAction(
            session_id=chat_session_id,
            user_id=user.id,
            action=action,
            payload=payload,
            preview=preview,
            status=ActionStatus.PENDING,
            expires_at=utcnow() + self._ttl,
            idempotency_key=f"chat-action-{uuid.uuid4().hex}",
        )
        self._session.add(row)
        self._session.commit()
        return row

    def get_owned(self, user: User, action_id: int) -> PendingAction:
        row = self._session.scalar(select(PendingAction).where(PendingAction.id == action_id).with_for_update())
        if row is None or row.user_id != user.id:
            self._session.rollback()
            raise NotFoundError("Pending action not found")
        return row

    def reject(self, user: User, action_id: int) -> PendingAction:
        row = self.get_owned(user, action_id)
        if row.status != ActionStatus.PENDING:
            self._session.rollback()
            raise ConflictError(f"Action is {row.status}", code="invalid_state")
        row.status = ActionStatus.REJECTED
        self._session.commit()
        return row

    def confirm(self, user: User, action_id: int, auth: str) -> PendingAction:
        row = self.get_owned(user, action_id)
        if row.status != ActionStatus.PENDING:
            self._session.rollback()
            raise ConflictError(f"Action is {row.status}", code="invalid_state")
        if row.expires_at < utcnow():
            row.status = ActionStatus.EXPIRED
            self._session.commit()
            raise ConflictError("This action has expired. Please ask again.", code="action_expired")

        executor = EXECUTORS[row.action]
        row.status = ActionStatus.PROCESSING
        self._session.commit()

        fresh = executor.fresh_preview(row.payload, auth, self._api)
        if fresh != row.preview:
            row.status = ActionStatus.EXPIRED
            row.outcome = {"reason": "details_changed", "new_preview": fresh}
            self._session.commit()
            replacement = self.propose(user, row.session_id, row.action, row.payload, auth)
            replacement.outcome = {"reason": "replaced_after_change", "replaced": row.id}
            self._session.commit()
            raise ConflictError("Prices or availability changed. A new confirmation is required.",
                                code="details_changed")

        result = executor.execute(row.payload, auth, self._api, row.idempotency_key)
        row.status = ActionStatus.CONFIRMED if result.ok else ActionStatus.FAILED
        row.outcome = result.outcome
        self._session.commit()
        return row
