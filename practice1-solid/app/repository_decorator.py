from app.storage import OrderStorage
from app.models import OrderRequest, OrderResponse
from typing import List


class CachedOrderRepository:
    """Decorator pattern: Adds caching to OrderRepository"""
    
    def __init__(self, repository):
        self._repository = repository
        self._cache: List[OrderResponse] = []
        self._cache_valid = False
    
    def save(self, order_request: OrderRequest, total: float) -> int:
        """Save and invalidate cache"""
        order_id = self._repository.save(order_request, total)
        self._cache_valid = False
        return order_id
    
    def list_all(self) -> List[OrderResponse]:
        """Return cached results if valid"""
        if not self._cache_valid:
            self._cache = self._repository.list_all()
            self._cache_valid = True
        return self._cache.copy()
