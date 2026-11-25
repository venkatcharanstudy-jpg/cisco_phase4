from app.models import OrderRequest, OrderResponse
from app.repository import OrderRepository
from app.calculator import PriceCalculator
from typing import List


class OrderService:
    """Single Responsibility: Orchestrates order creation and retrieval"""
    
    def __init__(self, repository: OrderRepository, calculator: PriceCalculator):
        self._repository = repository
        self._calculator = calculator
    
    def create_order(self, order_request: OrderRequest) -> OrderResponse:
        """Create order with calculated total"""
        total = self._calculator.calculate_total(order_request.items)
        order_id = self._repository.save(order_request, total)
        
        return OrderResponse(
            order_id=order_id,
            customer_name=order_request.customer_name,
            items=order_request.items,
            total=total
        )
    
    def list_orders(self) -> List[OrderResponse]:
        """List all orders"""
        return self._repository.list_all()
