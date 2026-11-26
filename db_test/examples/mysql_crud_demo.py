"""Demonstrate Create, Read, Update and Delete against the MySQL database.

Set NETPULSE_DATABASE_URL first, then run from the project root with:
    python -m examples.mysql_crud_demo
"""

from sqlalchemy import delete
from sqlalchemy.orm import sessionmaker

from app.db.database import Base, build_engine, ensure_database
from app.db.models import AlertRow, DeviceRow
from app.main import DEFAULT_DATABASE_URL
from app.models import DeviceCreate
from app.repositories.sqlalchemy_device_repository import SQLAlchemyDeviceRepository
from app.services.device_service import DeviceService


def main() -> None:
    ensure_database(DEFAULT_DATABASE_URL)
    engine = build_engine(DEFAULT_DATABASE_URL)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)

    print("CREATE: register RTR-101 (online)")
    with session_factory() as session, session.begin():
        DeviceService(SQLAlchemyDeviceRepository(session)).register(
            DeviceCreate(
                device_id="RTR-101",
                name="Branch Router",
                device_type="router",
                ip_address="192.168.10.1",
            )
        )

    print("READ: fetch RTR-101 in a new session")
    with session_factory() as session:
        device = DeviceService(SQLAlchemyDeviceRepository(session)).get("RTR-101")
        print(f"  {device.model_dump()}")

    print("UPDATE: set RTR-101 offline (creates one alert in the same transaction)")
    with session_factory() as session, session.begin():
        DeviceService(SQLAlchemyDeviceRepository(session)).update_status("RTR-101", "offline")

    with session_factory() as session:
        alerts = DeviceService(SQLAlchemyDeviceRepository(session)).list_alerts()
        print(f"  alerts: {[alert.message for alert in alerts]}")

    print("DELETE: remove RTR-101 and its alerts with session.delete()")
    with session_factory() as session, session.begin():
        session.execute(delete(AlertRow).where(AlertRow.device_id == "RTR-101"))
        session.delete(session.get(DeviceRow, "RTR-101"))

    with session_factory() as session:
        remaining = DeviceService(SQLAlchemyDeviceRepository(session)).list_devices()
        print(f"  devices remaining: {len(remaining)}")

    engine.dispose()


if __name__ == "__main__":
    main()
