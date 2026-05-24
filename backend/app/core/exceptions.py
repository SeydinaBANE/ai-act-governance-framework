from __future__ import annotations

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse


class AppError(HTTPException):
    pass


class NotFoundError(AppError):
    def __init__(self, resource: str, resource_id: str | None = None) -> None:
        detail = f"{resource} introuvable"
        if resource_id:
            detail = f"{resource} '{resource_id}' introuvable"
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class ForbiddenError(AppError):
    def __init__(self, action: str = "effectuer cette action") -> None:
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Vous n'êtes pas autorisé à {action}",
        )


class UnauthorizedError(AppError):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentification requise",
            headers={"WWW-Authenticate": "Bearer"},
        )


class ConflictError(AppError):
    def __init__(self, detail: str) -> None:
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class UnprocessableError(AppError):
    def __init__(self, detail: str) -> None:
        super().__init__(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "status_code": exc.status_code},
    )
