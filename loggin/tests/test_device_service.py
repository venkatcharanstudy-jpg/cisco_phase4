import pytest

from app.models import DeviceCreate
from app.repositories.device_repository import InMemoryDeviceRepository
from app.services.device_service import (
    DeviceAlreadyExistsError,
    DeviceNotFoundError,
    DeviceService,
)


@pytest.fixture
def service() -> DeviceService:
    return DeviceService(InMemoryDeviceRepository())


def make_device(device_id: str = "RTR-101", status: str = "online") -> DeviceCreate:
    return DeviceCreate(
        device_id=device_id,
        name="Branch Router",
        device_type="router",
        ip_address="192.168.10.1",
        status=status,
    )


def test_register_stores_device(service: DeviceService) -> None:
    device = service.register(make_device())

    assert device.device_id == "RTR-101"
    assert service.get("RTR-101") == device


def test_register_duplicate_raises(service: DeviceService) -> None:
    service.register(make_device())

    with pytest.raises(DeviceAlreadyExistsError):
        service.register(make_device())


def test_get_missing_device_raises(service: DeviceService) -> None:
    with pytest.raises(DeviceNotFoundError):
        service.get("missing")


def test_initial_offline_registration_creates_no_alert(service: DeviceService) -> None:
    service.register(make_device(status="offline"))

    assert service.list_alerts() == []


def test_online_to_offline_creates_one_alert(service: DeviceService) -> None:
    service.register(make_device())

    service.update_status("RTR-101", "offline")

    alerts = service.list_alerts()
    assert len(alerts) == 1
    assert alerts[0].device_id == "RTR-101"


def test_repeated_offline_update_creates_no_second_alert(service: DeviceService) -> None:
    service.register(make_device())
    service.update_status("RTR-101", "offline")

    service.update_status("RTR-101", "offline")

    assert len(service.list_alerts()) == 1
