from __future__ import annotations

import os
from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.security import create_access_token, hash_password
from app.database import Base, get_db
from app.main import app
from app.models.user import User, UserRole

# En CI, DATABASE_URL pointe sur localhost (service container GitHub Actions).
# En local Docker, on force postgres:5432. La base de test utilise le même host que la prod.
_base_url = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://aiact:aiact_dev_secret_2026@postgres:5432/aiact_governance",
)
TEST_DB_URL = _base_url.rsplit("/", 1)[0] + "/aiact_governance_test"


@pytest_asyncio.fixture(scope="session")
async def engine():
    # NullPool: aucun partage de connexion entre tests
    _engine = create_async_engine(TEST_DB_URL, echo=False, poolclass=NullPool)
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield _engine
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await _engine.dispose()


@pytest_asyncio.fixture
async def db(engine) -> AsyncGenerator[AsyncSession, None]:
    """Chaque test reçoit une connexion propre avec rollback automatique."""
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
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
