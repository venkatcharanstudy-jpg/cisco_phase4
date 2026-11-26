from datetime import datetime, timezone

from app.models import AlertResponse
from app.repositories.contracts import DeviceRepository


def create_offline_alert(repository: DeviceRepository, device_id: str) -> None:
    alert = AlertResponse(
        device_id=device_id,
        message=f"Device {device_id} changed from online to offline",
        timestamp=datetime.now(timezone.utc),
    )
    repository.save_alert(alert)
