import uuid
from typing import Annotated

import structlog
from fastapi import APIRouter, Request, status

from app.composition import AuthenticateUserDep, CreateUserDep, UpdateUserDep
from app.config import settings
from app.core.dependencies import AdminUser, CurrentUser
from app.core.rate_limiter import limiter
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse, UserCreate, UserOut, UserUpdate

log = structlog.get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login(
    request: Request, body: LoginRequest, use_case: AuthenticateUserDep
) -> TokenResponse:
    _user, token = await use_case.execute(body.email, body.password)
    return TokenResponse(
        access_token=token,
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.get("/me", response_model=UserOut)
async def get_me(current_user: CurrentUser) -> User:
    return current_user


@router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
@limiter.limit("20/hour")
async def create_user(
    request: Request,
    body: UserCreate,
    _admin: Annotated[User, AdminUser],
    current_user: CurrentUser,
    use_case: CreateUserDep,
) -> User:
    return await use_case.execute(body.model_dump(), actor=current_user)


@router.patch("/users/{user_id}", response_model=UserOut)
async def update_user(
    user_id: uuid.UUID,
    body: UserUpdate,
    _admin: Annotated[User, AdminUser],
    current_user: CurrentUser,
    use_case: UpdateUserDep,
) -> User:
    return await use_case.execute(user_id, body.model_dump(exclude_none=True), actor=current_user)
