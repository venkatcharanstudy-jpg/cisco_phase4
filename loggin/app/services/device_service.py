import structlog

from app.events import create_offline_alert
from app.models import (
    AlertResponse,
    DeviceCreate,
    DeviceResponse,
    DeviceStatus,
    DeviceSummaryResponse,
)
from app.repositories.contracts import DeviceRepository

log = structlog.get_logger("netpulse.service")


class DeviceAlreadyExistsError(Exception):
    pass


class DeviceNotFoundError(Exception):
    pass


class DeviceService:
    def __init__(self, repository: DeviceRepository) -> None:
        self._repository = repository

    def register(self, payload: DeviceCreate) -> DeviceResponse:
        log.info("device_registration_requested", device_id=payload.device_id)
        if self._repository.get_device(payload.device_id) is not None:
            raise DeviceAlreadyExistsError(payload.device_id)
        device = self._repository.add_device(DeviceResponse(**payload.model_dump()))
        log.info("device_registered", device_id=device.device_id, device_type=device.device_type)
        return device

    def list_devices(self) -> list[DeviceResponse]:
        return self._repository.list_devices()

    def get(self, device_id: str) -> DeviceResponse:
        device = self._repository.get_device(device_id)
        if device is None:
            raise DeviceNotFoundError(device_id)
        return device

    def update_status(self, device_id: str, status: DeviceStatus) -> DeviceResponse:
        current = self.get(device_id)
        updated = self._repository.update_status(device_id, status)
        if current.status != status:
            log.info(
                "device_status_changed",
                device_id=device_id,
                old_status=current.status,
                new_status=status,
            )
        if current.status == "online" and status == "offline":
            create_offline_alert(self._repository, device_id)
        return updated

    def list_alerts(self) -> list[AlertResponse]:
        return self._repository.list_alerts()

    def get_device_summary(self) -> DeviceSummaryResponse:
        devices = self._repository.list_devices()
        status_counts = {"online": 0, "offline": 0}
        for device in devices:
            status_counts[device.status] += 1
        device_types = sorted({device.device_type for device in devices})
        return DeviceSummaryResponse(
            total_devices=len(devices),
            online_count=status_counts["online"],
            offline_count=status_counts["offline"],
            device_types=device_types,
        )
