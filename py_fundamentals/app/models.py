import ipaddress
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

DeviceType = Literal["router", "switch", "server"]
DeviceStatus = Literal["online", "offline"]


def _validate_ipv4(value: str) -> str:
    try:
        ipaddress.IPv4Address(value)
    except ValueError as exc:
        raise ValueError("ip_address must be a valid IPv4 address") from exc
    return value


class DeviceCreate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "device_id": "RTR-101",
                    "name": "Branch Router",
                    "device_type": "router",
                    "ip_address": "192.168.10.1",
                    "status": "online",
                }
            ]
        }
    )

    device_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    device_type: DeviceType
    ip_address: str
    status: DeviceStatus = "online"

    @field_validator("ip_address")
    @classmethod
    def check_ipv4(cls, value: str) -> str:
        return _validate_ipv4(value)


class DeviceResponse(BaseModel):
    device_id: str
    name: str
    device_type: DeviceType
    ip_address: str
    status: DeviceStatus


class StatusUpdate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"examples": [{"status": "offline"}]}
    )

    status: DeviceStatus


class AlertResponse(BaseModel):
    device_id: str
    message: str
    timestamp: datetime


class DeviceSummaryResponse(BaseModel):
    total_devices: int
    online_count: int
    offline_count: int
    device_types: list[str]


class ProbeResponse(BaseModel):
    device_id: str
    reachable: bool
    simulated: bool
