from __future__ import annotations

from typing import Annotated
from uuid import UUID

import structlog
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import decode_access_token
from app.database import DbSession
from app.models.user import User, UserRole

log = structlog.get_logger(__name__)

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    db: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> User:
    if not credentials:
        raise UnauthorizedError()

    try:
        payload = decode_access_token(credentials.credentials)
        user_id = UUID(payload["sub"])
    except (ValueError, KeyError) as e:
        log.warning("invalid_token", error=str(e))
        raise UnauthorizedError() from e

    user = await db.get(User, user_id)
    if not user or not user.is_active:
        raise UnauthorizedError()

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_role(*roles: UserRole):  # type: ignore[no-untyped-def]
    async def _check(current_user: CurrentUser) -> User:
        if current_user.role not in roles:
            raise ForbiddenError()
        return current_user

    return Depends(_check)


AdminUser = require_role(UserRole.ADMIN)
ReviewerOrAbove = require_role(UserRole.ADMIN, UserRole.REVIEWER)
