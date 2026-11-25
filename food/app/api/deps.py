from collections.abc import Iterator
from dataclasses import dataclass

from fastapi import Depends, Header, Request
from sqlalchemy.orm import Session, sessionmaker

from app.agents.chat_tools import build_registry
from app.agents.single_agent import SingleAgent
from app.config.settings import Settings
from app.exceptions import ForbiddenError, UnauthorizedError
from app.integrations.internal_api import InternalApi
from app.integrations.llm_base import LLMClient
from app.models.enums import Role
from app.models.user import User
from app.repositories.menu_repository import MenuRepository
from app.repositories.order_repository import OrderRepository
from app.repositories.user_repository import UserRepository
from app.security import parse_basic_auth, verify_password
from app.services.chat_service import ChatService
from app.services.document_service import DocumentService
from app.services.order_policy import OrderPolicy
from app.services.order_service import OrderService
from app.services.rate_limiter import SlidingWindowRateLimiter


@dataclass
class Container:
    """Composition root: every collaborator is built once here and injected into the request layer."""

    settings: Settings
    session_factory: sessionmaker[Session]
    llm: LLMClient
    internal_api: InternalApi
    rate_limiter: SlidingWindowRateLimiter

    def agent(self) -> SingleAgent:
        return SingleAgent(self.llm, build_registry(self.internal_api), self.settings.max_tool_iterations)


def get_container(request: Request) -> Container:
    return request.app.state.container


def get_db(container: Container = Depends(get_container)) -> Iterator[Session]:
    session = container.session_factory()
    try:
        yield session
    finally:
        session.close()


def get_authorization(authorization: str | None = Header(default=None)) -> str:
    if not authorization:
        raise UnauthorizedError("Missing Authorization header")
    return authorization


def get_current_user(
    authorization: str = Depends(get_authorization),
    session: Session = Depends(get_db),
) -> User:
    username, password = parse_basic_auth(authorization)
    user = UserRepository(session).get_by_username(username)
    if user is None or not verify_password(user.password_hash, password):
        raise UnauthorizedError("Invalid username or password")
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != Role.ADMIN:
        raise ForbiddenError("Admin role required")
    return user


def get_order_service(session: Session = Depends(get_db)) -> OrderService:
    return OrderService(session, OrderRepository(session), MenuRepository(session), OrderPolicy())


def get_menu_repository(session: Session = Depends(get_db)) -> MenuRepository:
    return MenuRepository(session)


def get_chat_service(
    session: Session = Depends(get_db),
    container: Container = Depends(get_container),
) -> ChatService:
    return ChatService(
        session=session,
        agent=container.agent(),
        api=container.internal_api,
        limiter=container.rate_limiter,
        pending_ttl_minutes=container.settings.pending_action_ttl_minutes,
        history_turns=container.settings.history_turns,
    )


def get_document_service(
    session: Session = Depends(get_db),
    container: Container = Depends(get_container),
) -> DocumentService:
    return DocumentService(session, container.settings)
