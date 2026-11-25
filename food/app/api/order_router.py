from fastapi import APIRouter, Depends, Header, Response

from app.api.deps import get_current_user, get_order_service, require_admin
from app.models.user import User
from app.schemas import CreateOrderIn, OrderOut, StatusUpdateIn
from app.services.order_service import OrderRequestLine, OrderService

router = APIRouter(prefix="/api/orders")


@router.get("", response_model=list[OrderOut])
def list_orders(
    limit: int = 20,
    offset: int = 0,
    user: User = Depends(get_current_user),
    service: OrderService = Depends(get_order_service),
) -> list[OrderOut]:
    limit = max(1, min(limit, 100))
    orders = service.list_orders(user, limit, max(offset, 0))
    return [OrderOut.model_validate(o) for o in orders]


@router.get("/{order_id}", response_model=OrderOut)
def get_order(
    order_id: int,
    user: User = Depends(get_current_user),
    service: OrderService = Depends(get_order_service),
) -> OrderOut:
    return OrderOut.model_validate(service.get_for_viewer(user, order_id))


@router.post("", response_model=OrderOut, status_code=201)
def create_order(
    body: CreateOrderIn,
    response: Response,
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=1, max_length=80),
    user: User = Depends(get_current_user),
    service: OrderService = Depends(get_order_service),
) -> OrderOut:
    lines = [OrderRequestLine(item_id=i.item_id, quantity=i.quantity) for i in body.items]
    order, created = service.create_order(user, lines, idempotency_key)
    if not created:
        response.status_code = 200
    return OrderOut.model_validate(order)


@router.post("/{order_id}/cancel", response_model=OrderOut)
def cancel_order(
    order_id: int,
    user: User = Depends(get_current_user),
    service: OrderService = Depends(get_order_service),
) -> OrderOut:
    return OrderOut.model_validate(service.cancel_order(user, order_id))


@router.patch("/{order_id}/status", response_model=OrderOut)
def update_status(
    order_id: int,
    body: StatusUpdateIn,
    admin: User = Depends(require_admin),
    service: OrderService = Depends(get_order_service),
) -> OrderOut:
    return OrderOut.model_validate(service.update_status(admin, order_id, body.status))
