from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.models import AlertResponse, DeviceCreate, DeviceResponse, StatusUpdate
from app.services.device_service import (
    DeviceAlreadyExistsError,
    DeviceNotFoundError,
    DeviceService,
)

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
    try:
        return service.register(payload)
    except DeviceAlreadyExistsError as exc:
        raise HTTPException(status_code=409, detail=f"Device {exc} already exists") from exc


@router.get("/devices", response_model=list[DeviceResponse])
def list_devices(service: DeviceService = Depends(get_device_service)) -> list[DeviceResponse]:
    return service.list_devices()


@router.get("/devices/{device_id}", response_model=DeviceResponse, responses=NOT_FOUND)
def get_device(
    device_id: str,
    service: DeviceService = Depends(get_device_service),
) -> DeviceResponse:
    try:
        return service.get(device_id)
    except DeviceNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Device {exc} not found") from exc


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
    try:
        return service.update_status(device_id, payload.status)
    except DeviceNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Device {exc} not found") from exc


@router.get("/alerts", response_model=list[AlertResponse])
def list_alerts(service: DeviceService = Depends(get_device_service)) -> list[AlertResponse]:
    return service.list_alerts()
