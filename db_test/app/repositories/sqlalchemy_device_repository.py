from datetime import timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import AlertRow, DeviceRow
from app.models import AlertResponse, DeviceResponse, DeviceStatus


def _to_device(row: DeviceRow) -> DeviceResponse:
    return DeviceResponse(
        device_id=row.device_id,
        name=row.name,
        device_type=row.device_type,
        ip_address=row.ip_address,
        status=row.status,
    )


def _to_alert(row: AlertRow) -> AlertResponse:
    # MySQL DATETIME drops tzinfo on read; all alert timestamps are stored in UTC.
    timestamp = row.timestamp if row.timestamp.tzinfo else row.timestamp.replace(tzinfo=timezone.utc)
    return AlertResponse(device_id=row.device_id, message=row.message, timestamp=timestamp)


class SQLAlchemyDeviceRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add_device(self, device: DeviceResponse) -> DeviceResponse:
        self._session.add(DeviceRow(**device.model_dump()))
        self._session.flush()
        return device.model_copy()

    def list_devices(self) -> list[DeviceResponse]:
        rows = self._session.scalars(select(DeviceRow).order_by(DeviceRow.device_id))
        return [_to_device(row) for row in rows]

    def get_device(self, device_id: str) -> DeviceResponse | None:
        row = self._session.get(DeviceRow, device_id)
        return _to_device(row) if row is not None else None

    def update_status(self, device_id: str, status: DeviceStatus) -> DeviceResponse | None:
        row = self._session.get(DeviceRow, device_id)
        if row is None:
            return None
        row.status = status
        self._session.flush()
        return _to_device(row)

    def save_alert(self, alert: AlertResponse) -> None:
        self._session.add(
            AlertRow(device_id=alert.device_id, message=alert.message, timestamp=alert.timestamp)
        )
        self._session.flush()

    def list_alerts(self) -> list[AlertResponse]:
        rows = self._session.scalars(select(AlertRow).order_by(AlertRow.id))
        return [_to_alert(row) for row in rows]
