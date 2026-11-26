from datetime import datetime, timezone

import structlog

from app.models import AlertResponse
from app.repositories.contracts import DeviceRepository

log = structlog.get_logger("netpulse.events")


def create_offline_alert(repository: DeviceRepository, device_id: str) -> None:
    alert = AlertResponse(
        device_id=device_id,
        message=f"Device {device_id} changed from online to offline",
        timestamp=datetime.now(timezone.utc),
    )
    repository.save_alert(alert)
    log.info("offline_alert_created", device_id=device_id)
