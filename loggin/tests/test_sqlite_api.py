import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.db.database as database
from app.db import models  # noqa: F401  (registers tables on Base.metadata)
from app.db.database import Base, get_session
from app.db.models import DeviceRow
from app.main import create_app


@pytest.fixture
def test_sessionmaker(tmp_path, monkeypatch):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'test.db'}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    maker = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    monkeypatch.setattr(database, "SessionLocal", maker)
    yield maker
    engine.dispose()


@pytest.fixture
def client(test_sessionmaker):
    # No "with" block: lifespan (init_db on netpulse.db) is not run.
    return TestClient(create_app())


DEVICE = {
    "device_id": "RTR-101",
    "name": "Branch Router",
    "device_type": "router",
    "ip_address": "192.168.10.1",
    "status": "online",
}


def test_crud_and_single_alert_on_online_to_offline(client, test_sessionmaker):
    assert client.post("/devices", json=DEVICE).status_code == 201
    assert client.get("/devices/RTR-101").json()["status"] == "online"

    assert client.patch("/devices/RTR-101/status", json={"status": "offline"}).status_code == 200
    # Repeating the same status must not create a second alert.
    client.patch("/devices/RTR-101/status", json={"status": "offline"})

    alerts = client.get("/alerts").json()
    assert len(alerts) == 1
    assert alerts[0]["device_id"] == "RTR-101"
    assert alerts[0]["timestamp"].endswith(("Z", "+00:00"))


def test_duplicate_and_missing_devices_return_409_and_404(client):
    client.post("/devices", json=DEVICE)
    assert client.post("/devices", json=DEVICE).status_code == 409
    assert client.get("/devices/NOPE").status_code == 404
    assert client.patch("/devices/NOPE/status", json={"status": "offline"}).status_code == 404


def test_rollback_discards_status_change_and_alert(test_sessionmaker):
    with test_sessionmaker() as session:
        session.add(DeviceRow(device_id="SW-1", name="s", device_type="switch",
                              ip_address="10.0.0.1", status="online"))
        session.commit()

    from app.repositories.sqlalchemy_device_repository import SQLAlchemyDeviceRepository
    from app.models import AlertResponse
    from datetime import datetime, timezone

    gen = get_session()
    session = next(gen)
    repo = SQLAlchemyDeviceRepository(session)
    repo.update_status("SW-1", "offline")
    repo.save_alert(AlertResponse(device_id="SW-1", message="m", timestamp=datetime.now(timezone.utc)))
    with pytest.raises(RuntimeError):
        gen.throw(RuntimeError("boom"))

    with test_sessionmaker() as check:
        assert check.get(DeviceRow, "SW-1").status == "online"
        assert SQLAlchemyDeviceRepository(check).list_alerts() == []
