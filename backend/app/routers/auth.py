from __future__ import annotations

import uuid
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.dependencies import AdminUser, CurrentUser
from app.core.security import create_access_token, hash_password, verify_password
from app.database import DbSession
from app.core.rate_limiter import limiter
from app.models.user import User, UserRole
from app.schemas.auth import LoginRequest, TokenResponse, UserCreate, UserOut, UserUpdate
from app.services import audit_logger

log = structlog.get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login(request: Request, body: LoginRequest, db: DbSession) -> TokenResponse:
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Compte désactivé")

    token = create_access_token({"sub": str(user.id), "email": user.email, "role": user.role})
    log.info("user_login", user_id=str(user.id), email=user.email)

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
    db: DbSession,
    _admin: Annotated[User, AdminUser],
    current_user: CurrentUser,
) -> User:
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email déjà utilisé")

    user = User(
        email=body.email,
        full_name=body.full_name,
        hashed_password=hash_password(body.password),
        role=body.role,
    )
    db.add(user)
    await db.flush()

    await audit_logger.log_action(
        db,
        actor=current_user,
        action="user.created",
        resource_type="user",
        resource_id=user.id,
        input_payload={"email": body.email, "role": body.role},
        output_summary={"user_id": str(user.id)},
    )

    log.info("user_created", user_id=str(user.id), email=user.email, role=user.role)
    return user


@router.patch("/users/{user_id}", response_model=UserOut)
async def update_user(
    user_id: uuid.UUID,
    body: UserUpdate,
    db: DbSession,
    _admin: Annotated[User, AdminUser],
    current_user: CurrentUser,
) -> User:
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur introuvable")

    update_data = body.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    await db.flush()
    await audit_logger.log_action(
        db,
        actor=current_user,
        action="user.updated",
        resource_type="user",
        resource_id=user_id,
        input_payload=update_data,
    )
    return user
