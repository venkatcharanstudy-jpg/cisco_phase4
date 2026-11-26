from fastapi import APIRouter, Depends, Request, status

from app.models import (
    AlertResponse,
    DeviceCreate,
    DeviceResponse,
    DeviceSummaryResponse,
    ProbeResponse,
    StatusUpdate,
)
from app.services.device_service import DeviceService
from app.services.probe import simulate_device_probe

router = APIRouter()

NOT_FOUND = {404: {"description": "Device not found"}}
CONFLICT = {409: {"description": "Device already exists"}}


def get_device_service(request: Request) -> DeviceService:
    return request.app.state.device_service


@router.post(
    "/devices",
    response_model=DeviceResponse,
    status_code=status.HTTP_201_CREATED,
    responses=CONFLICT,
)
def register_device(
    payload: DeviceCreate,
    service: DeviceService = Depends(get_device_service),
) -> DeviceResponse:
    return service.register(payload)


@router.get("/devices", response_model=list[DeviceResponse])
def list_devices(service: DeviceService = Depends(get_device_service)) -> list[DeviceResponse]:
    return service.list_devices()


# Declared before /devices/{device_id} so "summary" is not treated as a device ID.
@router.get("/devices/summary", response_model=DeviceSummaryResponse)
def get_device_summary(
    service: DeviceService = Depends(get_device_service),
) -> DeviceSummaryResponse:
    return service.get_device_summary()


@router.get("/devices/{device_id}", response_model=DeviceResponse, responses=NOT_FOUND)
def get_device(
    device_id: str,
    service: DeviceService = Depends(get_device_service),
) -> DeviceResponse:
    return service.get(device_id)


@router.patch(
    "/devices/{device_id}/status",
    response_model=DeviceResponse,
    responses=NOT_FOUND,
)
def update_device_status(
    device_id: str,
    payload: StatusUpdate,
    service: DeviceService = Depends(get_device_service),
) -> DeviceResponse:
    return service.update_status(device_id, payload.status)


@router.get(
    "/devices/{device_id}/probe",
    response_model=ProbeResponse,
    responses=NOT_FOUND,
)
async def probe_device(
    device_id: str,
    service: DeviceService = Depends(get_device_service),
) -> ProbeResponse:
    service.get(device_id)
    result = await simulate_device_probe(device_id)
    return ProbeResponse(**result)


@router.get("/alerts", response_model=list[AlertResponse])
def list_alerts(service: DeviceService = Depends(get_device_service)) -> list[AlertResponse]:
    return service.list_alerts()
