from __future__ import annotations

import uuid
from typing import Any

import structlog

from app.core.exceptions import (
    AccountDisabledError,
    ConflictError,
    InvalidCredentialsError,
    NotFoundError,
)
from app.core.security import create_access_token, hash_password, verify_password
from app.domain.audit_log.ports import AuditLogPort
from app.domain.user.ports import UserRepository
from app.models.user import User

log = structlog.get_logger(__name__)


class AuthenticateUser:
    def __init__(self, users: UserRepository) -> None:
        self._users = users

    async def execute(self, email: str, password: str) -> tuple[User, str]:
        user = await self._users.get_by_email(email)
        if user is None or not verify_password(password, user.hashed_password):
            raise InvalidCredentialsError()
        if not user.is_active:
            raise AccountDisabledError()

        token = create_access_token({"sub": str(user.id), "email": user.email, "role": user.role})
        log.info("user_login", user_id=str(user.id), email=user.email)
        return user, token


class CreateUser:
    def __init__(self, users: UserRepository, audit_logs: AuditLogPort) -> None:
        self._users = users
        self._audit_logs = audit_logs

    async def execute(self, data: dict[str, Any], *, actor: User) -> User:
        existing = await self._users.get_by_email(data["email"])
        if existing is not None:
            raise ConflictError("Email déjà utilisé")

        user = User(
            email=data["email"],
            full_name=data["full_name"],
            hashed_password=hash_password(data["password"]),
            role=data["role"],
        )
        await self._users.add(user)

        await self._audit_logs.record(
            actor=actor,
            action="user.created",
            resource_type="user",
            resource_id=user.id,
            input_payload={"email": data["email"], "role": data["role"]},
            output_summary={"user_id": str(user.id)},
        )
        log.info("user_created", user_id=str(user.id), email=user.email, role=user.role)
        return user


class UpdateUser:
    def __init__(self, users: UserRepository, audit_logs: AuditLogPort) -> None:
        self._users = users
        self._audit_logs = audit_logs

    async def execute(self, user_id: uuid.UUID, updates: dict[str, Any], *, actor: User) -> User:
        user = await self._users.get(user_id)
        if user is None:
            raise NotFoundError("Utilisateur", str(user_id))

        for field, value in updates.items():
            setattr(user, field, value)

        await self._audit_logs.record(
            actor=actor,
            action="user.updated",
            resource_type="user",
            resource_id=user_id,
            input_payload=updates,
        )
        return user
