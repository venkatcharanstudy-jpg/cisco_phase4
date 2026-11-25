from pydantic import BaseModel, Field
from typing import List


class OrderItem(BaseModel):
    name: str
    quantity: int = Field(gt=0, description="Quantity must be greater than 0")
    unit_price: float = Field(ge=0, description="Unit price must be >= 0")


class OrderRequest(BaseModel):
    customer_name: str
    items: List[OrderItem] = Field(min_length=1, description="At least one item required")


class OrderResponse(BaseModel):
    order_id: int
    customer_name: str
    items: List[OrderItem]
    total: float
