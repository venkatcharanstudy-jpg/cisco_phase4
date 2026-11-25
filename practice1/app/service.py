from app.repository import OrderRepository
from app.models import OrderRequest, OrderResponse
from typing import List


class OrderService:
    def __init__(self, repository: OrderRepository):
        self.repository = repository

    def create_order(self, order_request: OrderRequest) -> OrderResponse:
        """Create an order, calculate total, and save to database"""
        # Calculate total: sum of (quantity * unit_price) for all items
        total = sum(item.quantity * item.unit_price for item in order_request.items)
        total = round(total, 2)
        
        # Save order to database and get order_id
        order_id = self.repository.save(order_request, total)
        
        # Return the created order
        return OrderResponse(
            order_id=order_id,
            customer_name=order_request.customer_name,
            items=order_request.items,
            total=total
        )

    def list_orders(self) -> List[OrderResponse]:
        """Retrieve all orders from the database"""
        return self.repository.list_all()
