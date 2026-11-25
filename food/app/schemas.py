from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class HealthOut(BaseModel):
    status: str


class LoginOut(BaseModel):
    username: str
    role: str


class MenuItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    category: str
    vegetarian: bool
    price: Decimal
    capacity: int


class OrderLineIn(BaseModel):
    item_id: int = Field(gt=0)
    quantity: int = Field(ge=1, le=50)


class CreateOrderIn(BaseModel):
    items: list[OrderLineIn] = Field(min_length=1, max_length=30)


class StatusUpdateIn(BaseModel):
    status: str = Field(pattern="^(PREPARING|READY|DELIVERED|CANCELLED)$")


class OrderLineOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    item_id: int
    quantity: int
    unit_price: Decimal


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    status: str
    total: Decimal
    lines: list[OrderLineOut]


class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    session_id: int | None = None


class PendingActionOut(BaseModel):
    id: int
    action: str
    status: str
    preview: dict
    outcome: dict | None = None
    expires_at: str


class ChatReplyOut(BaseModel):
    session_id: int
    reply: str
    mode: str
    citations: list[dict] = []
    pending_action: PendingActionOut | None = None


class DocumentOut(BaseModel):
    id: int
    filename: str
    version: int
    status: str
    chunks: int
