from __future__ import annotations

import uuid

import pytest
from app.application.use_cases.user import AuthenticateUser, CreateUser, UpdateUser
from app.core.exceptions import (
    AccountDisabledError,
    ConflictError,
    InvalidCredentialsError,
    NotFoundError,
)
from app.core.security import hash_password
from app.models.user import UserRole

from tests.factories.user_factory import UserFactory
from tests.fakes.repositories import InMemoryAuditLogRepository, InMemoryUserRepository


async def test_authenticate_user_valid_credentials_returns_token() -> None:
    user = UserFactory.build(email="a@test.com", hashed_password=hash_password("secret123"))
    users = InMemoryUserRepository([user])

    authenticated, token = await AuthenticateUser(users).execute("a@test.com", "secret123")

    assert authenticated.id == user.id
    assert isinstance(token, str)
    assert token


async def test_authenticate_user_wrong_password_raises() -> None:
    user = UserFactory.build(email="a@test.com", hashed_password=hash_password("secret123"))
    users = InMemoryUserRepository([user])

    with pytest.raises(InvalidCredentialsError):
        await AuthenticateUser(users).execute("a@test.com", "wrong-password")


async def test_authenticate_user_unknown_email_raises() -> None:
    users = InMemoryUserRepository([])

    with pytest.raises(InvalidCredentialsError):
        await AuthenticateUser(users).execute("missing@test.com", "secret123")


async def test_authenticate_user_inactive_account_raises() -> None:
    user = UserFactory.build(
        email="a@test.com", hashed_password=hash_password("secret123"), is_active=False
    )
    users = InMemoryUserRepository([user])

    with pytest.raises(AccountDisabledError):
        await AuthenticateUser(users).execute("a@test.com", "secret123")


async def test_create_user_hashes_password_and_records_audit() -> None:
    users = InMemoryUserRepository()
    audit_logs = InMemoryAuditLogRepository()
    actor = UserFactory.build(role=UserRole.ADMIN)

    user = await CreateUser(users, audit_logs).execute(
        {
            "email": "new@test.com",
            "full_name": "Nouveau",
            "password": "secret123",
            "role": UserRole.READONLY,
        },
        actor=actor,
    )

    assert user.hashed_password != "secret123"
    assert len(users.users) == 1
    assert audit_logs.entries[0].action == "user.created"


async def test_create_user_duplicate_email_raises() -> None:
    existing = UserFactory.build(email="dup@test.com")
    users = InMemoryUserRepository([existing])
    audit_logs = InMemoryAuditLogRepository()

    with pytest.raises(ConflictError):
        await CreateUser(users, audit_logs).execute(
            {
                "email": "dup@test.com",
                "full_name": "Autre",
                "password": "secret123",
                "role": UserRole.READONLY,
            },
            actor=UserFactory.build(role=UserRole.ADMIN),
        )


async def test_update_user_applies_fields_and_records_audit() -> None:
    user = UserFactory.build(full_name="Ancien nom")
    users = InMemoryUserRepository([user])
    audit_logs = InMemoryAuditLogRepository()
    actor = UserFactory.build(role=UserRole.ADMIN)

    updated = await UpdateUser(users, audit_logs).execute(
        user.id, {"full_name": "Nouveau nom"}, actor=actor
    )

    assert updated.full_name == "Nouveau nom"
    assert audit_logs.entries[0].action == "user.updated"


async def test_update_user_missing_raises() -> None:
    users = InMemoryUserRepository([])
    audit_logs = InMemoryAuditLogRepository()

    with pytest.raises(NotFoundError):
        await UpdateUser(users, audit_logs).execute(
            uuid.uuid4(), {"full_name": "x"}, actor=UserFactory.build(role=UserRole.ADMIN)
        )
