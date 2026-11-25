from abc import ABC, abstractmethod
from app.models import OrderRequest, OrderResponse
from typing import List, Callable


class OrderObserver(ABC):
    """Observer pattern: Notified of order events"""
    
    @abstractmethod
    def on_order_created(self, order: OrderResponse) -> None:
        pass


class OrderLogger(OrderObserver):
    """Single Responsibility: Logs order events"""
    
    def on_order_created(self, order: OrderResponse) -> None:
        print(f"[LOG] Order created: ID={order.order_id}, Customer={order.customer_name}, Total={order.total}")


class OrderValidator(OrderObserver):
    """Single Responsibility: Validates created orders"""
    
    def on_order_created(self, order: OrderResponse) -> None:
        if order.total < 0:
            raise ValueError(f"Invalid order: negative total {order.total}")
        if not order.customer_name:
            raise ValueError("Invalid order: empty customer name")


class OrderServiceWithObservers:
    """Single Responsibility with Observer pattern"""
    
    def __init__(self, repository, calculator, observers: List[OrderObserver] = None):
        self._repository = repository
        self._calculator = calculator
        self._observers = observers or []
    
    def attach_observer(self, observer: OrderObserver) -> None:
        self._observers.append(observer)
    
    def detach_observer(self, observer: OrderObserver) -> None:
        self._observers.remove(observer)
    
    def _notify_observers(self, order: OrderResponse) -> None:
        for observer in self._observers:
            observer.on_order_created(order)
    
    def create_order(self, order_request: OrderRequest) -> OrderResponse:
        """Create order with observer notifications"""
        total = self._calculator.calculate_total(order_request.items)
        order_id = self._repository.save(order_request, total)
        
        order_response = OrderResponse(
            order_id=order_id,
            customer_name=order_request.customer_name,
            items=order_request.items,
            total=total
        )
        
        self._notify_observers(order_response)
        return order_response
    
    def list_orders(self) -> List[OrderResponse]:
        """List all orders"""
        return self._repository.list_all()
