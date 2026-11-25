from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from app.api.deps import Container, get_chat_service, get_container, get_current_user, get_db
from app.models.user import User
from app.schemas import ChatIn, ChatReplyOut, PendingActionOut
from app.services.chat_service import ChatService, pending_action_out
from app.services.pending_action_service import PendingActionService

router = APIRouter(prefix="/api/chat")


@router.post("", response_model=ChatReplyOut)
def chat(
    body: ChatIn,
    user: User = Depends(get_current_user),
    authorization: str = Header(default=""),
    service: ChatService = Depends(get_chat_service),
) -> dict:
    return service.send(user, authorization, body.message, body.session_id)


@router.post("/actions/{action_id}/confirm", response_model=PendingActionOut)
def confirm_action(
    action_id: int,
    user: User = Depends(get_current_user),
    authorization: str = Header(default=""),
    session: Session = Depends(get_db),
    container: Container = Depends(get_container),
) -> dict:
    service = PendingActionService(session, container.internal_api, container.settings.pending_action_ttl_minutes)
    return pending_action_out(service.confirm(user, action_id, authorization))


@router.post("/actions/{action_id}/reject", response_model=PendingActionOut)
def reject_action(
    action_id: int,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
    container: Container = Depends(get_container),
) -> dict:
    service = PendingActionService(session, container.internal_api, container.settings.pending_action_ttl_minutes)
    return pending_action_out(service.reject(user, action_id))
