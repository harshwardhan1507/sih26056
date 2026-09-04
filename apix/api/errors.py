"""
Shared error handling and exceptions for the APIx FastAPI application.

Enforces a consistent error response shape across all endpoints:
    {
        "error": "<machine_readable_code>",
        "detail": "<human_readable_explanation>"
    }
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class DataUnavailableError(Exception):
    """Raised when an underlying data artifact (CSV, weights) is absent or incomplete."""

    def __init__(
        self,
        detail: str = "Required data artifact is not available.",
        error_code: str = "data_unavailable",
        status_code: int = 503,
    ) -> None:
        super().__init__(detail)
        self.detail = detail
        self.error_code = error_code
        self.status_code = status_code


def register_error_handlers(app: FastAPI) -> None:
    """Register uniform ErrorResponse handlers on the FastAPI application."""

    @app.exception_handler(DataUnavailableError)
    async def data_unavailable_handler(request: Request, exc: DataUnavailableError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.error_code, "detail": exc.detail},
        )

    @app.exception_handler(FileNotFoundError)
    async def file_not_found_handler(request: Request, exc: FileNotFoundError) -> JSONResponse:
        return JSONResponse(
            status_code=503,
            content={"error": "data_unavailable", "detail": str(exc)},
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content={"error": "invalid_parameter", "detail": str(exc)},
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        error_code = "not_found" if exc.status_code == 404 else "http_error"
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": error_code, "detail": str(exc.detail)},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "error": "validation_error",
                "detail": "Request parameter validation failed: " + "; ".join(
                    f"{'.'.join(str(l) for l in err['loc'])}: {err['msg']}" for err in exc.errors()
                ),
            },
        )
