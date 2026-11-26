import asyncio

import pytest

from app.models import DeviceCreate
from app.repositories.device_repository import InMemoryDeviceRepository
from app.services.device_service import (
    DeviceAlreadyExistsError,
    DeviceNotFoundError,
    DeviceService,
)
from app.services.probe import simulate_device_probe


@pytest.fixture
def service() -> DeviceService:
    return DeviceService(InMemoryDeviceRepository())


def make_device(device_id: str, device_type: str = "router", status: str = "online") -> DeviceCreate:
    return DeviceCreate(
        device_id=device_id,
        name=f"Device {device_id}",
        device_type=device_type,
        ip_address="192.168.10.1",
        status=status,
    )


def test_summary_of_empty_fleet_is_zeroed(service: DeviceService) -> None:
    summary = service.get_device_summary()

    assert summary.total_devices == 0
    assert summary.online_count == 0
    assert summary.offline_count == 0
    assert summary.device_types == []


def test_summary_counts_statuses_and_unique_sorted_types(service: DeviceService) -> None:
    service.register(make_device("RTR-101", "router"))
    service.register(make_device("SW-102", "switch"))
    service.register(make_device("SW-103", "switch", status="offline"))

    summary = service.get_device_summary()

    assert summary.total_devices == 3
    assert summary.online_count == 2
    assert summary.offline_count == 1
    assert summary.device_types == ["router", "switch"]


def test_duplicate_device_raises(service: DeviceService) -> None:
    service.register(make_device("RTR-101"))

    with pytest.raises(DeviceAlreadyExistsError):
        service.register(make_device("RTR-101"))


def test_missing_device_raises(service: DeviceService) -> None:
    with pytest.raises(DeviceNotFoundError):
        service.get("missing")


def test_simulated_probe_returns_deterministic_result() -> None:
    result = asyncio.run(simulate_device_probe("RTR-101"))

    assert result == {"device_id": "RTR-101", "reachable": True, "simulated": True}
