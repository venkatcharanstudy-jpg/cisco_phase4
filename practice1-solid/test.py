import sys
sys.path.insert(0, '/home/venkave7615/Desktop/cisco/practice1-solid')

from app.storage import InMemoryOrderStorage
from app.repository import OrderRepository
from app.calculator import StandardPriceCalculator
from app.service import OrderService
from app.models import OrderRequest, OrderItem

storage = InMemoryOrderStorage()
calculator = StandardPriceCalculator()
repository = OrderRepository(storage)
service = OrderService(repository, calculator)

order_request = OrderRequest(
    customer_name="Anu",
    items=[
        OrderItem(name="Notebook", quantity=2, unit_price=50),
        OrderItem(name="Pen", quantity=1, unit_price=20)
    ]
)

created_order = service.create_order(order_request)
print(f"✓ Order created: {created_order}")
print(f"✓ Order ID: {created_order.order_id}")
print(f"✓ Total: {created_order.total}")

all_orders = service.list_orders()
print(f"✓ Total orders: {len(all_orders)}")
print(f"✓ Orders: {all_orders}")

assert created_order.total == 120.0, f"Total should be 120.0, got {created_order.total}"
assert created_order.order_id == 1, f"Order ID should be 1, got {created_order.order_id}"
assert len(all_orders) == 1, f"Should have 1 order, got {len(all_orders)}"

print("\n✅ All tests passed!")
