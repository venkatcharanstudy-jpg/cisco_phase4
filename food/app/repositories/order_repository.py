from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.order import Order


class OrderRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, order: Order) -> Order:
        self._session.add(order)
        self._session.flush()
        return order

    def get(self, order_id: int) -> Order | None:
        return self._session.get(Order, order_id)

    def get_for_update(self, order_id: int) -> Order | None:
        return self._session.scalar(select(Order).where(Order.id == order_id).with_for_update())

    def get_by_idempotency(self, user_id: int, key: str) -> Order | None:
        stmt = select(Order).where(Order.user_id == user_id, Order.idempotency_key == key)
        return self._session.scalar(stmt)

    def list_for_user(self, user_id: int, limit: int, offset: int) -> list[Order]:
        stmt = select(Order).where(Order.user_id == user_id).order_by(Order.id.desc()).limit(limit).offset(offset)
        return list(self._session.scalars(stmt))

    def list_all(self, limit: int, offset: int) -> list[Order]:
        stmt = select(Order).order_by(Order.id.desc()).limit(limit).offset(offset)
        return list(self._session.scalars(stmt))

    def count_for_user(self, user_id: int) -> int:
        return self._session.scalar(select(func.count()).select_from(Order).where(Order.user_id == user_id)) or 0
