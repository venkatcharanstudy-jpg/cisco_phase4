import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import sessionmaker

import app.db.models  # noqa: F401  registers tables on Base.metadata
from app.db.database import Base, build_engine, ensure_database
from app.routes.devices import router as devices_router
from app.services.device_service import (
    DeviceAlreadyExistsError,
    DeviceNotFoundError,
)

# The password is supplied via NETPULSE_DATABASE_URL, never stored in the repo.
DEFAULT_DATABASE_URL = os.environ.get(
    "NETPULSE_DATABASE_URL", "mysql+pymysql://admin@127.0.0.1:3306/netpulse"
)


def create_app(database_url: str = DEFAULT_DATABASE_URL) -> FastAPI:
    engine = build_engine(database_url)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        ensure_database(database_url)
        Base.metadata.create_all(bind=engine)
        yield
        engine.dispose()

    app = FastAPI(title="NetPulse", version="1.0.0", lifespan=lifespan)
    app.state.session_factory = session_factory
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
