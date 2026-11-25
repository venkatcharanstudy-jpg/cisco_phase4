from http import HTTPStatus


class AppError(Exception):
    """Domain-level error that maps to a stable JSON error envelope."""

    status_code: int = HTTPStatus.BAD_REQUEST
    code: str = "bad_request"

    def __init__(self, message: str, code: str | None = None, status_code: int | None = None) -> None:
        super().__init__(message)
        self.message = message
        if code is not None:
            self.code = code
        if status_code is not None:
            self.status_code = status_code


class NotFoundError(AppError):
    status_code = HTTPStatus.NOT_FOUND
    code = "not_found"


class ForbiddenError(AppError):
    status_code = HTTPStatus.FORBIDDEN
    code = "forbidden"


class UnauthorizedError(AppError):
    status_code = HTTPStatus.UNAUTHORIZED
    code = "unauthorized"


class ConflictError(AppError):
    status_code = HTTPStatus.CONFLICT
    code = "conflict"


class ValidationFailedError(AppError):
    status_code = HTTPStatus.UNPROCESSABLE_ENTITY
    code = "validation_error"


class RateLimitedError(AppError):
    status_code = HTTPStatus.TOO_MANY_REQUESTS
    code = "rate_limited"


class ServiceUnavailableError(AppError):
    status_code = HTTPStatus.SERVICE_UNAVAILABLE
    code = "service_unavailable"
