from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class DeviceRow(Base):
    __tablename__ = "devices"

    device_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    device_type: Mapped[str] = mapped_column(String(50))
    ip_address: Mapped[str] = mapped_column(String(45))
    status: Mapped[str] = mapped_column(String(20))


class AlertRow(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    device_id: Mapped[str] = mapped_column(String(64), index=True)
    message: Mapped[str] = mapped_column(String(255))
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))
