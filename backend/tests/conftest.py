from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app
from app.models.user import User, UserRole
from app.core.security import hash_password, create_access_token


TEST_DB_URL = "postgresql+asyncpg://aiact:aiact_dev_secret@localhost:5432/aiact_governance_test"


@pytest_asyncio.fixture(scope="session")
async def engine():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db(engine) -> AsyncGenerator[AsyncSession, None]:
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def admin_user(db: AsyncSession) -> User:
    user = User(
        email="admin@test.com",
        full_name="Admin Test",
        hashed_password=hash_password("AdminPass123!"),
        role=UserRole.ADMIN,
    )
    db.add(user)
    await db.flush()
    return user


@pytest_asyncio.fixture
def admin_token(admin_user: User) -> str:
    return create_access_token({
        "sub": str(admin_user.id),
        "email": admin_user.email,
        "role": admin_user.role.value,
    })


@pytest_asyncio.fixture
async def reviewer_user(db: AsyncSession) -> User:
    user = User(
        email="reviewer@test.com",
        full_name="Reviewer Test",
        hashed_password=hash_password("ReviewPass123!"),
        role=UserRole.REVIEWER,
    )
    db.add(user)
    await db.flush()
    return user


@pytest_asyncio.fixture
def reviewer_token(reviewer_user: User) -> str:
    return create_access_token({
        "sub": str(reviewer_user.id),
        "email": reviewer_user.email,
        "role": reviewer_user.role.value,
    })
