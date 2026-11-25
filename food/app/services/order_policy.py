from app.exceptions import ConflictError, ForbiddenError
from app.models.enums import OrderStatus, Role

_CUSTOMER_TRANSITIONS: dict[str, set[str]] = {
    OrderStatus.CONFIRMED: {OrderStatus.CANCELLED},
}

_ADMIN_TRANSITIONS: dict[str, set[str]] = {
    OrderStatus.CONFIRMED: {OrderStatus.PREPARING, OrderStatus.CANCELLED},
    OrderStatus.PREPARING: {OrderStatus.READY},
    OrderStatus.READY: {OrderStatus.DELIVERED},
}


class OrderPolicy:
    """Pure rules for who may move an order to which status."""

    def ensure_can_transition(self, role: str, current: str, target: str) -> None:
        table = _ADMIN_TRANSITIONS if role == Role.ADMIN else _CUSTOMER_TRANSITIONS
        if role != Role.ADMIN and target != OrderStatus.CANCELLED:
            raise ForbiddenError("Only admins can change this order status")
        if target not in table.get(current, set()):
            raise ConflictError(f"Cannot move order from {current} to {target}", code="invalid_transition")

    def can_view(self, user_id: int, role: str, owner_id: int) -> bool:
        return role == Role.ADMIN or user_id == owner_id
