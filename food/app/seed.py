"""Idempotent seed: python -m app.seed"""

import logging
from pathlib import Path

from sqlalchemy import func, select

from app.config.database import Base
from app.config.settings import get_settings
from app.config.database import create_db_engine, create_session_factory
from app.models.enums import Role
from app.models.menu_item import MenuItem
from app.models.order import Order
from app.models.user import User
from app.repositories.menu_repository import MenuRepository
from app.repositories.order_repository import OrderRepository
from app.repositories.user_repository import UserRepository
from app.security import hash_password
from app.services.document_service import DocumentService
from app.services.order_policy import OrderPolicy
from app.services.order_service import OrderRequestLine, OrderService

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("seed")
ROOT = Path(__file__).resolve().parent.parent

MENU = [
    ("Masala Dosa", "Breakfast", True, "90.00", 20),
    ("Idli Sambar", "Breakfast", True, "60.00", 25),
    ("Chicken Sandwich", "Breakfast", False, "120.00", 15),
    ("Paneer Biryani", "Main course", True, "180.00", 10),
    ("Chicken Biryani", "Main course", False, "220.00", 12),
    ("Dal Tadka", "Main course", True, "140.00", 15),
    ("Veg Fried Rice", "Main course", True, "130.00", 18),
    ("Garlic Naan", "Breads", True, "40.00", 30),
    ("Gulab Jamun", "Desserts", True, "70.00", 20),
    ("Mango Lassi", "Beverages", True, "80.00", 25),
]


def seed() -> None:
    settings = get_settings()
    engine = create_db_engine(settings.database_url)
    Base.metadata.create_all(engine)
    session_factory = create_session_factory(engine)

    with session_factory() as session:
        users = UserRepository(session)
        if users.get_by_username("admin") is None:
            users.add(User(username="admin", password_hash=hash_password("Admin123"), role=Role.ADMIN))
            log.info("created admin user")
        customer = users.get_by_username("customer")
        if customer is None:
            customer = users.add(User(username="customer", password_hash=hash_password("Customer123"), role=Role.CUSTOMER))
            log.info("created demo customer (customer / Customer123)")

        if session.scalar(select(func.count()).select_from(MenuItem)) == 0:
            for title, category, veg, price, capacity in MENU:
                session.add(MenuItem(title=title, category=category, vegetarian=veg,
                                     price=price, capacity=capacity))
            session.commit()
            log.info("seeded %d menu items", len(MENU))

        if session.scalar(select(func.count()).select_from(Order)) == 0:
            orders = OrderService(session, OrderRepository(session), MenuRepository(session), OrderPolicy())
            menu = {m.title: m.id for m in MenuRepository(session).list_active()}
            samples = [
                [OrderRequestLine(menu["Masala Dosa"], 2), OrderRequestLine(menu["Mango Lassi"], 1)],
                [OrderRequestLine(menu["Paneer Biryani"], 1), OrderRequestLine(menu["Garlic Naan"], 2)],
                [OrderRequestLine(menu["Gulab Jamun"], 1)],
            ]
            for i, lines in enumerate(samples, start=1):
                orders.create_order(customer, lines, idempotency_key=f"seed-order-{i}")
            session.commit()
            log.info("seeded %d sample orders", len(samples))

        admin = users.get_by_username("admin")
        docs = DocumentService(session, settings)
        existing = {d["filename"] for d in docs.list_documents()}
        for path in sorted((ROOT / "knowledge_base").glob("*.txt")):
            if path.name in existing:
                continue
            docs.ingest(admin, path.name, path.read_bytes())
            log.info("ingested knowledge base file %s", path.name)
        session.commit()
    engine.dispose()
    log.info("seed complete")


if __name__ == "__main__":
    seed()
