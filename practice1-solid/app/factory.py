from abc import ABC, abstractmethod
from app.models import OrderRequest, OrderResponse
from app.repository import OrderRepository
from app.calculator import PriceCalculator
from app.service import OrderService
from app.storage import OrderStorage, InMemoryOrderStorage
from app.calculator import StandardPriceCalculator


class ServiceFactory:
    """Factory pattern: Creates service instances with proper dependencies"""
    
    @staticmethod
    def create_order_service(storage: OrderStorage = None, calculator: PriceCalculator = None) -> OrderService:
        """Create OrderService with injected dependencies"""
        if storage is None:
            storage = InMemoryOrderStorage()
        
        if calculator is None:
            calculator = StandardPriceCalculator()
        
        repository = OrderRepository(storage)
        return OrderService(repository, calculator)


class ServiceProvider:
    """Singleton-like provider for services"""
    
    _instance = None
    _service = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_service(self) -> OrderService:
        if self._service is None:
            self._service = ServiceFactory.create_order_service()
        return self._service
    
    def set_service(self, service: OrderService) -> None:
        self._service = service
