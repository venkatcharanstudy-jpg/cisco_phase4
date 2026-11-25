from app.db import Database
from app.models import OrderItem, OrderRequest, OrderResponse
from typing import List


class OrderRepository:
    def __init__(self, db: Database):
        self.db = db

    def save(self, order_request: OrderRequest, total: float) -> int:
        """Save an order to the database and return the order_id"""
        insert_order_query = """
        INSERT INTO orders (customer_name, total) 
        VALUES (%s, %s)
        """
        
        cursor = self.db.execute_query(
            insert_order_query, 
            (order_request.customer_name, total)
        )
        
        # Get the last inserted order_id
        last_id_query = "SELECT LAST_INSERT_ID() as order_id"
        result = self.db.fetch_one(last_id_query)
        order_id = result['order_id']
        
        # Insert order items
        insert_items_query = """
        INSERT INTO order_items (order_id, name, quantity, unit_price) 
        VALUES (%s, %s, %s, %s)
        """
        
        for item in order_request.items:
            self.db.execute_query(
                insert_items_query,
                (order_id, item.name, item.quantity, item.unit_price)
            )
        
        return order_id

    def list_all(self) -> List[OrderResponse]:
        """Retrieve all orders from the database"""
        orders_query = "SELECT order_id, customer_name, total FROM orders ORDER BY order_id"
        orders = self.db.fetch_query(orders_query)
        
        result = []
        for order in orders:
            order_id = order['order_id']
            
            # Fetch items for this order
            items_query = "SELECT name, quantity, unit_price FROM order_items WHERE order_id = %s"
            items_data = self.db.fetch_query(items_query, (order_id,))
            
            items = [
                OrderItem(
                    name=item['name'],
                    quantity=item['quantity'],
                    unit_price=item['unit_price']
                )
                for item in items_data
            ]
            
            order_response = OrderResponse(
                order_id=order_id,
                customer_name=order['customer_name'],
                items=items,
                total=order['total']
            )
            result.append(order_response)
        
        return result
