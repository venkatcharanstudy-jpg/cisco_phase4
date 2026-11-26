from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.repositories.device_repository import InMemoryDeviceRepository
from app.routes.devices import router as devices_router
from app.services.device_service import (
    DeviceAlreadyExistsError,
    DeviceNotFoundError,
    DeviceService,
)


def create_app() -> FastAPI:
    app = FastAPI(title="NetPulse", version="1.0.0")
    app.state.device_service = DeviceService(InMemoryDeviceRepository())
    app.include_router(devices_router)

    @app.exception_handler(DeviceAlreadyExistsError)
    async def handle_already_exists(request: Request, exc: DeviceAlreadyExistsError):
        return JSONResponse(status_code=409, content={"detail": f"Device {exc} already exists"})

    @app.exception_handler(DeviceNotFoundError)
    async def handle_not_found(request: Request, exc: DeviceNotFoundError):
        return JSONResponse(status_code=404, content={"detail": f"Device {exc} not found"})

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
