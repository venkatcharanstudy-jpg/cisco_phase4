from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

import structlog

from app.db.database import init_db
from app.logging_config import configure_logging
from app.middleware.request_id import register_request_id_middleware
from app.routes.devices import router as devices_router
from app.services.device_service import (
    DeviceAlreadyExistsError,
    DeviceNotFoundError,
)

log = structlog.get_logger("netpulse.http")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(title="NetPulse", version="1.0.0", lifespan=lifespan)
    register_request_id_middleware(app)
    app.include_router(devices_router)

    @app.exception_handler(DeviceAlreadyExistsError)
    async def handle_already_exists(request: Request, exc: DeviceAlreadyExistsError):
        log.warning("device_already_exists", error_type="DeviceAlreadyExistsError", device_id=str(exc))
        return JSONResponse(status_code=409, content={"detail": f"Device {exc} already exists"})

    @app.exception_handler(DeviceNotFoundError)
    async def handle_not_found(request: Request, exc: DeviceNotFoundError):
        log.warning("device_not_found", error_type="DeviceNotFoundError", device_id=str(exc))
        return JSONResponse(status_code=404, content={"detail": f"Device {exc} not found"})

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
