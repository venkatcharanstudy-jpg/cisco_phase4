import json

import structlog
from fastapi.testclient import TestClient

from app.logging_config import configure_logging
from app.main import create_app
import app.db.database as database
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.database import Base

import pytest

FAKE_TOKEN = "DEMO-DO-NOT-USE"


@pytest.fixture
def isolated_db(tmp_path, monkeypatch):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'log.db'}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    monkeypatch.setattr(database, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False))
    yield
    engine.dispose()


def _json_lines(captured: str) -> list[dict]:
    return [json.loads(line) for line in captured.splitlines() if line.startswith("{")]


def test_request_id_is_echoed_or_replaced(isolated_db, capfd):
    client = TestClient(create_app())

    echoed = client.get("/health", headers={"X-Request-ID": "lab-trace-401"})
    assert echoed.headers["X-Request-ID"] == "lab-trace-401"

    replaced = client.get("/health", headers={"X-Request-ID": "bad id with spaces!"})
    assert replaced.headers["X-Request-ID"] != "bad id with spaces!"
    assert len(replaced.headers["X-Request-ID"]) == 32


def test_request_completed_and_business_events_are_json(isolated_db, capfd):
    client = TestClient(create_app())
    client.post(
        "/devices",
        json={"device_id": "RTR-1", "name": "r", "device_type": "router", "ip_address": "10.0.0.1"},
        headers={"X-Request-ID": "lab-trace-401"},
    )
    client.patch(
        "/devices/RTR-1/status",
        json={"status": "offline"},
        headers={"X-Request-ID": "lab-trace-401"},
    )
    client.get("/devices/MISSING", headers={"X-Request-ID": "lab-trace-401"})

    events = _json_lines(capfd.readouterr().err)
    names = [e["event"] for e in events]
    assert "device_registration_requested" in names
    assert "device_registered" in names
    assert "device_status_changed" in names
    assert "offline_alert_created" in names

    completed = [e for e in events if e["event"] == "request_completed"]
    assert {e["request_id"] for e in completed} == {"lab-trace-401"}
    patch_done = next(e for e in completed if e["method"] == "PATCH")
    assert patch_done["path"] == "/devices/{device_id}/status"
    assert patch_done["status_code"] == 200
    assert isinstance(patch_done["duration_ms"], float)

    not_found = next(e for e in events if e["event"] == "device_not_found")
    assert not_found["level"] == "warning"
    assert not_found["device_id"] == "MISSING"
    assert not_found["error_type"] == "DeviceNotFoundError"


def test_sensitive_fields_are_redacted(isolated_db, capfd):
    configure_logging()
    structlog.get_logger("netpulse.test").info("probe_sent", token=FAKE_TOKEN, api_key="x")

    out = capfd.readouterr().err
    assert FAKE_TOKEN not in out
    event = _json_lines(out)[-1]
    assert event["token"] == "***"
    assert event["api_key"] == "***"
