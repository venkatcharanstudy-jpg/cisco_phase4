import pytest
from fastapi.testclient import TestClient

from app.db.database import unit_of_work
from app.main import create_app
from app.repositories.sqlalchemy_device_repository import SQLAlchemyDeviceRepository
from app.services.device_service import DeviceService


def device_payload(device_id: str = "RTR-101", status: str = "online") -> dict[str, str]:
    return {
        "device_id": device_id,
        "name": "Branch Router",
        "device_type": "router",
        "ip_address": "192.168.10.1",
        "status": status,
    }


def test_create_read_update_and_summary(client) -> None:
    assert client.post("/devices", json=device_payload()).status_code == 201
    client.post("/devices", json=device_payload("SW-102") | {"device_type": "switch"})

    assert client.get("/devices/RTR-101").json()["status"] == "online"
    assert client.patch("/devices/RTR-101/status", json={"status": "offline"}).status_code == 200
    assert client.get("/devices/RTR-101").json()["status"] == "offline"

    summary = client.get("/devices/summary").json()
    assert summary == {
        "total_devices": 2,
        "online_count": 1,
        "offline_count": 1,
        "device_types": ["router", "switch"],
    }


def test_error_contracts_are_preserved(client) -> None:
    client.post("/devices", json=device_payload())

    assert client.post("/devices", json=device_payload()).status_code == 409
    assert client.get("/devices/missing").status_code == 404
    assert client.patch("/devices/missing/status", json={"status": "offline"}).status_code == 404
    assert client.post("/devices", json=device_payload("BAD-1") | {"ip_address": "999.1.1.1"}).status_code == 422


def test_online_to_offline_creates_one_alert_and_probe_changes_nothing(client) -> None:
    client.post("/devices", json=device_payload())

    client.patch("/devices/RTR-101/status", json={"status": "offline"})
    client.patch("/devices/RTR-101/status", json={"status": "offline"})
    probe = client.get("/devices/RTR-101/probe")

    alerts = client.get("/alerts").json()
    assert probe.json() == {"device_id": "RTR-101", "reachable": True, "simulated": True}
    assert len(alerts) == 1
    assert alerts[0]["device_id"] == "RTR-101"
    assert client.get("/devices/RTR-101").json()["status"] == "offline"


def test_data_survives_app_restart(db_url: str) -> None:
    with TestClient(create_app(db_url)) as first:
        first.post("/devices", json=device_payload())
        first.patch("/devices/RTR-101/status", json={"status": "offline"})

    with TestClient(create_app(db_url)) as second:
        assert [d["device_id"] for d in second.get("/devices").json()] == ["RTR-101"]
        assert len(second.get("/alerts").json()) == 1


def test_failed_unit_of_work_saves_neither_status_nor_alert(client) -> None:
    client.post("/devices", json=device_payload())
    session_factory = client.app.state.session_factory

    unit = unit_of_work(session_factory)
    session = next(unit)
    DeviceService(SQLAlchemyDeviceRepository(session)).update_status("RTR-101", "offline")
    with pytest.raises(RuntimeError, match="injected"):
        unit.throw(RuntimeError("injected"))

    with session_factory() as fresh:
        repo = SQLAlchemyDeviceRepository(fresh)
        assert repo.get_device("RTR-101").status == "online"
        assert repo.list_alerts() == []
