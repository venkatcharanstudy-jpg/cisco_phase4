import logging
import time

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .api.employee_router import router as employee_router
from .core.exceptions import EmployeeAlreadyExistsError, EmployeeNotFoundError
from .core.logging_config import setup_logging

http_logger = logging.getLogger("employee_app.http")


def create_app() -> FastAPI:
    setup_logging()

    app = FastAPI(title="Employee Management API", version="1.0.0")

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000
        http_logger.info(
            "%s %s -> %s (%.2f ms)",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )
        return response

    @app.exception_handler(EmployeeNotFoundError)
    async def handle_not_found(request: Request, exc: EmployeeNotFoundError):
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(EmployeeAlreadyExistsError)
    async def handle_already_exists(request: Request, exc: EmployeeAlreadyExistsError):
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    app.include_router(employee_router)
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("employee_app.main:app", host="127.0.0.1", port=8000)
