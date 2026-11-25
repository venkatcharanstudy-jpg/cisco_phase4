import logging
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api import admin_router, catalog_router, chat_router, order_router
from app.api.deps import Container
from app.config.database import Base, create_db_engine, create_session_factory
from app.config.settings import Settings, get_settings
from app.exceptions import AppError
from app.integrations.gemini_client import GeminiClient
from app.integrations.internal_api import InternalApiClient
from app.integrations.llm_base import LLMClient
from app.models import *  # noqa: F401,F403  (registers ORM models on Base.metadata)
from app.services.rate_limiter import SlidingWindowRateLimiter

logger = logging.getLogger("food")
ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = ROOT / "frontend"


def _error(request: Request, status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content={"code": code, "message": message, "request_id": getattr(request.state, "request_id", "")},
    )


def create_app(
    settings: Settings | None = None,
    llm_client: LLMClient | None = None,
    internal_http: httpx.Client | None = None,
) -> FastAPI:
    """Application factory. Tests pass fakes for the LLM and the internal HTTP client."""
    settings = settings or get_settings()
    engine = create_db_engine(settings.database_url)
    session_factory = create_session_factory(engine)
    llm = llm_client or GeminiClient(
        api_key=settings.gemini_api_key,
        model=settings.gemini_model,
        base_url=settings.gemini_base_url,
        timeout=settings.llm_timeout_seconds,
    )
    internal_api = InternalApiClient(settings.internal_api_base_url, http=internal_http)
    container = Container(
        settings=settings,
        session_factory=session_factory,
        llm=llm,
        internal_api=internal_api,
        rate_limiter=SlidingWindowRateLimiter(settings.chat_rate_limit_per_minute),
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        Base.metadata.create_all(engine)
        yield
        engine.dispose()

    app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)
    app.state.container = container

    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):
        request.state.request_id = uuid.uuid4().hex[:12]
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        return response

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        return _error(request, exc.status_code, exc.code, exc.message)

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError):
        first = exc.errors()[0] if exc.errors() else {}
        loc = ".".join(str(p) for p in first.get("loc", []))
        return _error(request, 422, "validation_error", f"Invalid input at '{loc}': {first.get('msg', '')}")

    @app.exception_handler(StarletteHTTPException)
    async def http_handler(request: Request, exc: StarletteHTTPException):
        code = {401: "unauthorized", 403: "forbidden", 404: "not_found", 405: "method_not_allowed"}.get(
            exc.status_code, "http_error")
        return _error(request, exc.status_code, code, str(exc.detail))

    @app.exception_handler(Exception)
    async def unhandled_handler(request: Request, exc: Exception):
        logger.exception("Unhandled error request_id=%s", getattr(request.state, "request_id", ""))
        return _error(request, 500, "internal_error", "Something went wrong. Please try again.")

    @app.get("/health", tags=["system"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(catalog_router.router, tags=["catalog"])
    app.include_router(order_router.router, tags=["orders"])
    app.include_router(chat_router.router, tags=["chat"])
    app.include_router(admin_router.router, tags=["admin"])

    if FRONTEND_DIR.exists():
        app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
    return app
