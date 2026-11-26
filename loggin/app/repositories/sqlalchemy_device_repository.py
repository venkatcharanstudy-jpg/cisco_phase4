from datetime import timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import AlertRow, DeviceRow
from app.models import AlertResponse, DeviceResponse, DeviceStatus


class SQLAlchemyDeviceRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add_device(self, device: DeviceResponse) -> DeviceResponse:
        self._session.add(DeviceRow(**device.model_dump()))
        self._session.flush()
        return device.model_copy()

    def list_devices(self) -> list[DeviceResponse]:
        rows = self._session.scalars(select(DeviceRow).order_by(DeviceRow.device_id)).all()
        return [DeviceResponse.model_validate(row, from_attributes=True) for row in rows]

    def get_device(self, device_id: str) -> DeviceResponse | None:
        row = self._session.get(DeviceRow, device_id)
        if row is None:
            return None
        return DeviceResponse.model_validate(row, from_attributes=True)

    def update_status(self, device_id: str, status: DeviceStatus) -> DeviceResponse | None:
        row = self._session.get(DeviceRow, device_id)
        if row is None:
            return None
        row.status = status
        self._session.flush()
        return DeviceResponse.model_validate(row, from_attributes=True)

    def save_alert(self, alert: AlertResponse) -> None:
        self._session.add(
            AlertRow(
                device_id=alert.device_id,
                message=alert.message,
                timestamp=alert.timestamp,
            )
        )
        self._session.flush()

    def list_alerts(self) -> list[AlertResponse]:
        rows = self._session.scalars(select(AlertRow).order_by(AlertRow.id)).all()
        return [
            AlertResponse(
                device_id=row.device_id,
                message=row.message,
                timestamp=_as_utc(row.timestamp),
            )
            for row in rows
        ]


def _as_utc(value):
    # SQLite returns naive datetimes; the alerts were written in UTC.
    return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)
