from fastapi import FastAPI

from app.repositories.device_repository import InMemoryDeviceRepository
from app.routes.devices import router as devices_router
from app.services.device_service import DeviceService


def create_app() -> FastAPI:
    app = FastAPI(title="NetPulse", version="1.0.0")
    app.state.device_service = DeviceService(InMemoryDeviceRepository())
    app.include_router(devices_router)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
