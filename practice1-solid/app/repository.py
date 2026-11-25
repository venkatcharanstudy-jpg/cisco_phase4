from app.models import OrderRequest, OrderResponse, OrderItem
from app.storage import OrderStorage
from typing import List


class OrderRepository:
    """Single Responsibility: Manages order persistence"""
    
    def __init__(self, storage: OrderStorage):
        self._storage = storage
    
    def save(self, order_request: OrderRequest, total: float) -> int:
        """Save order and return order_id"""
        order_id = self._storage.get_next_order_id()
        
        items_data = [
            {'name': item.name, 'quantity': item.quantity, 'unit_price': item.unit_price}
            for item in order_request.items
        ]
        
        self._storage.save_order(order_id, order_request.customer_name, total, items_data)
        return order_id
    
    def list_all(self) -> List[OrderResponse]:
        """Retrieve all orders"""
        orders_data = self._storage.get_all_orders()
        
        result = []
        for order in orders_data:
            items = [
                OrderItem(name=item['name'], quantity=item['quantity'], unit_price=item['unit_price'])
                for item in order['items']
            ]
            order_response = OrderResponse(
                order_id=order['order_id'],
                customer_name=order['customer_name'],
                items=items,
                total=order['total']
            )
            result.append(order_response)
        
        return result
