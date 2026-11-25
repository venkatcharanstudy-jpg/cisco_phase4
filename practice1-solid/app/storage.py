from abc import ABC, abstractmethod
from app.models import OrderRequest, OrderResponse
from typing import List


class OrderStorage(ABC):
    """Interface Segregation: Abstract interface for order storage"""
    
    @abstractmethod
    def save_order(self, order_id: int, customer_name: str, total: float, items: list) -> None:
        pass
    
    @abstractmethod
    def get_all_orders(self) -> List[dict]:
        pass
    
    @abstractmethod
    def get_next_order_id(self) -> int:
        pass


class InMemoryOrderStorage(OrderStorage):
    """Concrete implementation: In-memory storage"""
    
    def __init__(self):
        self._orders: List[dict] = []
        self._next_id = 1
    
    def save_order(self, order_id: int, customer_name: str, total: float, items: list) -> None:
        self._orders.append({
            'order_id': order_id,
            'customer_name': customer_name,
            'total': total,
            'items': items
        })
        self._next_id = order_id + 1
    
    def get_all_orders(self) -> List[dict]:
        return self._orders.copy()
    
    def get_next_order_id(self) -> int:
        order_id = self._next_id
        return order_id
