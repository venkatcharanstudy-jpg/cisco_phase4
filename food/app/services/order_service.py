from collections import Counter
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.exceptions import ConflictError, ForbiddenError, NotFoundError, ValidationFailedError
from app.models.enums import OrderStatus, Role
from app.models.menu_item import MenuItem
from app.models.order import Order, OrderLine
from app.models.user import User
from app.repositories.menu_repository import MenuRepository
from app.repositories.order_repository import OrderRepository
from app.services.order_policy import OrderPolicy


@dataclass(frozen=True)
class OrderRequestLine:
    item_id: int
    quantity: int


class OrderService:
    """Places, cancels and transitions orders. All inventory writes happen under row locks."""

    def __init__(self, session: Session, orders: OrderRepository, menu: MenuRepository, policy: OrderPolicy) -> None:
        self._session = session
        self._orders = orders
        self._menu = menu
        self._policy = policy

    def create_order(self, user: User, lines: list[OrderRequestLine], idempotency_key: str) -> tuple[Order, bool]:
        """Returns (order, created). An identical replay returns the existing order with created=False."""
        existing = self._orders.get_by_idempotency(user.id, idempotency_key)
        if existing is not None:
            return self._replay_or_conflict(existing, lines), False

        try:
            order = self._place(user, lines, idempotency_key)
            self._session.commit()
            return order, True
        except IntegrityError as exc:
            self._session.rollback()
            existing = self._orders.get_by_idempotency(user.id, idempotency_key)
            if existing is None:
                raise ConflictError("Could not place order, please retry") from exc
            return self._replay_or_conflict(existing, lines), False
        except Exception:
            self._session.rollback()
            raise

    def _place(self, user: User, lines: list[OrderRequestLine], idempotency_key: str) -> Order:
        requested: dict[int, int] = Counter()
        for line in lines:
            requested[line.item_id] += line.quantity
        locked = self._menu.get_for_update(list(requested))

        missing = [item_id for item_id in requested if item_id not in locked]
        if missing:
            raise NotFoundError(f"Menu item(s) not found: {sorted(missing)}")
        inactive = [item.id for item in locked.values() if not item.active]
        if inactive:
            raise ValidationFailedError(f"Menu item(s) not available: {sorted(inactive)}")
        short = [
            f"{locked[item_id].title} (requested {qty}, available {locked[item_id].capacity})"
            for item_id, qty in requested.items()
            if locked[item_id].capacity < qty
        ]
        if short:
            raise ConflictError("Insufficient capacity: " + "; ".join(short), code="insufficient_capacity")

        order_lines: list[OrderLine] = []
        total = Decimal("0.00")
        for item_id, qty in requested.items():
            item = locked[item_id]
            item.capacity -= qty
            order_lines.append(OrderLine(item_id=item_id, quantity=qty, unit_price=item.price))
            total += item.price * qty

        order = Order(
            user_id=user.id,
            status=OrderStatus.CONFIRMED,
            total=total,
            idempotency_key=idempotency_key,
            lines=order_lines,
        )
        return self._orders.add(order)

    @staticmethod
    def _replay_or_conflict(existing: Order, lines: list[OrderRequestLine]) -> Order:
        requested = Counter()
        for line in lines:
            requested[line.item_id] += line.quantity
        stored = Counter()
        for line in existing.lines:
            stored[line.item_id] += line.quantity
        if stored != requested:
            raise ConflictError("Idempotency-Key was already used with a different order", code="idempotency_conflict")
        return existing

    def cancel_order(self, actor: User, order_id: int) -> Order:
        order = self._orders.get_for_update(order_id)
        if order is None:
            self._session.rollback()
            raise NotFoundError("Order not found")
        if not self._policy.can_view(actor.id, actor.role, order.user_id):
            self._session.rollback()
            raise ForbiddenError("You cannot cancel this order")
        try:
            self._policy.ensure_can_transition(actor.role, order.status, OrderStatus.CANCELLED)
            self._restore_capacity(order)
            order.status = OrderStatus.CANCELLED
            self._session.commit()
            return order
        except Exception:
            self._session.rollback()
            raise

    def update_status(self, actor: User, order_id: int, target: str) -> Order:
        order = self._orders.get_for_update(order_id)
        if order is None:
            self._session.rollback()
            raise NotFoundError("Order not found")
        try:
            self._policy.ensure_can_transition(actor.role, order.status, target)
            if target == OrderStatus.CANCELLED:
                self._restore_capacity(order)
            order.status = target
            self._session.commit()
            return order
        except Exception:
            self._session.rollback()
            raise

    def _restore_capacity(self, order: Order) -> None:
        restore: Counter[int] = Counter()
        for line in order.lines:
            restore[line.item_id] += line.quantity
        locked = self._menu.get_for_update(list(restore))
        for item_id, qty in restore.items():
            item: MenuItem | None = locked.get(item_id)
            if item is not None:
                item.capacity += qty

    def get_for_viewer(self, viewer: User, order_id: int) -> Order:
        order = self._orders.get(order_id)
        if order is None or not self._policy.can_view(viewer.id, viewer.role, order.user_id):
            raise NotFoundError("Order not found")
        return order

    def list_orders(self, viewer: User, limit: int, offset: int) -> list[Order]:
        if viewer.role == Role.ADMIN:
            return self._orders.list_all(limit, offset)
        return self._orders.list_for_user(viewer.id, limit, offset)
