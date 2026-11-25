import sys
sys.path.insert(0, '/home/venkave7615/Desktop/cisco/practice1-solid')

from app.storage import InMemoryOrderStorage
from app.repository import OrderRepository
from app.calculator import StandardPriceCalculator
from app.service import OrderService
from app.service_observer import OrderServiceWithObservers, OrderLogger, OrderValidator
from app.factory import ServiceFactory, ServiceProvider
from app.calculator_strategies import DiscountedPriceCalculator, ProgressiveDiscountCalculator
from app.repository_decorator import CachedOrderRepository
from app.models import OrderRequest, OrderItem

print("=" * 70)
print("TESTING SOLID PRINCIPLES & DESIGN PATTERNS")
print("=" * 70)

print("\n1️⃣  BASIC SERVICE (Single Responsibility)")
print("-" * 70)
storage = InMemoryOrderStorage()
calculator = StandardPriceCalculator()
repository = OrderRepository(storage)
service = OrderService(repository, calculator)

order_data = OrderRequest(
    customer_name="Anu",
    items=[OrderItem(name="Notebook", quantity=2, unit_price=50)]
)
order = service.create_order(order_data)
print(f"✓ Order created: ID={order.order_id}, Total={order.total}")
assert order.total == 100.0

print("\n2️⃣  FACTORY PATTERN (Dependency Inversion)")
print("-" * 70)
service_from_factory = ServiceFactory.create_order_service()
order_data2 = OrderRequest(
    customer_name="Bob",
    items=[OrderItem(name="Pen", quantity=5, unit_price=10)]
)
order2 = service_from_factory.create_order(order_data2)
print(f"✓ Order from factory: ID={order2.order_id}, Total={order2.total}")
assert order2.total == 50.0

print("\n3️⃣  STRATEGY PATTERN (Open/Closed Principle)")
print("-" * 70)
storage3 = InMemoryOrderStorage()
repository3 = OrderRepository(storage3)

discount_calc = DiscountedPriceCalculator(discount_percentage=10)
service_discount = OrderService(repository3, discount_calc)
order_data3 = OrderRequest(
    customer_name="Charlie",
    items=[OrderItem(name="Books", quantity=10, unit_price=20)]
)
order3 = service_discount.create_order(order_data3)
print(f"✓ Order with 10% discount: Total={order3.total} (original: 200)")
assert order3.total == 180.0

print("\n4️⃣  PROGRESSIVE DISCOUNT STRATEGY")
print("-" * 70)
storage4 = InMemoryOrderStorage()
repository4 = OrderRepository(storage4)
progressive_calc = ProgressiveDiscountCalculator()
service_progressive = OrderService(repository4, progressive_calc)

order_data4 = OrderRequest(
    customer_name="Diana",
    items=[OrderItem(name="Supplies", quantity=20, unit_price=12)]
)
order4 = service_progressive.create_order(order_data4)
print(f"✓ Order with progressive discount: Total={order4.total} (original: 240, 10% discount)")
assert order4.total == 216.0

print("\n5️⃣  OBSERVER PATTERN (Single Responsibility)")
print("-" * 70)
storage5 = InMemoryOrderStorage()
repository5 = OrderRepository(storage5)
calculator5 = StandardPriceCalculator()

service_obs = OrderServiceWithObservers(repository5, calculator5)
logger = OrderLogger()
validator = OrderValidator()
service_obs.attach_observer(logger)
service_obs.attach_observer(validator)

order_data5 = OrderRequest(
    customer_name="Eve",
    items=[OrderItem(name="Items", quantity=3, unit_price=25)]
)
order5 = service_obs.create_order(order_data5)
print(f"✓ Order with observers: ID={order5.order_id}, Total={order5.total}")
print("  (Logger and Validator were notified)")
assert order5.total == 75.0

print("\n6️⃣  DECORATOR PATTERN (Open/Closed Principle)")
print("-" * 70)
storage6 = InMemoryOrderStorage()
repository6 = OrderRepository(storage6)
cached_repository = CachedOrderRepository(repository6)
service_cached = OrderService(cached_repository, StandardPriceCalculator())

order_data6a = OrderRequest(
    customer_name="Frank",
    items=[OrderItem(name="A", quantity=1, unit_price=10)]
)
order6a = service_cached.create_order(order_data6a)

order_data6b = OrderRequest(
    customer_name="Grace",
    items=[OrderItem(name="B", quantity=2, unit_price=15)]
)
order6b = service_cached.create_order(order_data6b)

orders_cached = cached_repository.list_all()
print(f"✓ Cached repository: {len(orders_cached)} orders retrieved from cache")
assert len(orders_cached) == 2

print("\n7️⃣  SINGLETON SERVICE PROVIDER")
print("-" * 70)
provider1 = ServiceProvider()
provider2 = ServiceProvider()
print(f"✓ Both providers are same instance: {provider1 is provider2}")
assert provider1 is provider2

service_p1 = provider1.get_service()
service_p2 = provider2.get_service()
print(f"✓ Both services are same instance: {service_p1 is service_p2}")
assert service_p1 is service_p2

print("\n" + "=" * 70)
print("✅ ALL TESTS PASSED - SOLID PRINCIPLES VERIFIED")
print("=" * 70)
print("""
SOLID Principles Demonstrated:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

S - Single Responsibility Principle
  ✓ OrderService: handles order orchestration
  ✓ OrderRepository: handles persistence
  ✓ PriceCalculator: handles calculations
  ✓ OrderLogger: handles logging
  ✓ OrderValidator: handles validation

O - Open/Closed Principle
  ✓ PriceCalculator is open for extension
  ✓ StandardPriceCalculator, DiscountedPriceCalculator, ProgressiveDiscountCalculator
  ✓ OrderRepository is wrapped with CachedOrderRepository decorator

L - Liskov Substitution Principle
  ✓ All calculator implementations can replace PriceCalculator
  ✓ All observers implement OrderObserver interface

I - Interface Segregation Principle
  ✓ OrderStorage interface: focused storage operations
  ✓ PriceCalculator interface: focused calculation
  ✓ OrderObserver interface: focused notifications

D - Dependency Inversion Principle
  ✓ OrderService depends on abstractions (OrderRepository, PriceCalculator)
  ✓ ServiceFactory creates instances with proper dependencies
  ✓ ServiceProvider manages service lifecycle

Design Patterns Implemented:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ Strategy Pattern: Multiple pricing calculators
✓ Factory Pattern: ServiceFactory for object creation
✓ Singleton Pattern: ServiceProvider for shared instances
✓ Observer Pattern: Notify observers on order creation
✓ Decorator Pattern: CachedOrderRepository wraps repository

""")
