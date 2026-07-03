from enum import StrEnum
from typing import Any

from fastapi import Request, status
from fastapi.responses import JSONResponse


class ErrorCode(StrEnum):
    LLM_TIMEOUT = "LLM_TIMEOUT"
    LLM_INVALID_OUTPUT = "LLM_INVALID_OUTPUT"
    ARTICLE_VALIDATION_FAILED = "ARTICLE_VALIDATION_FAILED"
    WORDPRESS_UNAVAILABLE = "WORDPRESS_UNAVAILABLE"
    WORDPRESS_AUTH_FAILED = "WORDPRESS_AUTH_FAILED"
    JOB_NOT_FOUND = "JOB_NOT_FOUND"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class AppError(Exception):
    def __init__(
        self,
        code: ErrorCode,
        message: str,
        *,
        status_code: int,
        retryable: bool = False,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        self.retryable = retryable
        self.details = details or {}


async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "retryable": exc.retryable,
                "details": exc.details,
            }
        },
    )


async def unhandled_error_handler(_: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": ErrorCode.INTERNAL_ERROR,
                "message": "系統發生未預期錯誤，請稍後再試。",
                "retryable": False,
                "details": {"type": exc.__class__.__name__},
            }
        },
    )
