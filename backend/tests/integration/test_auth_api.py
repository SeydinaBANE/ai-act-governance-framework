from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.models.user import UserRole


async def test_login_success(client: AsyncClient, admin_user, admin_token) -> None:
    # Le token est déjà disponible via la fixture
    assert admin_token is not None
    assert len(admin_token) > 10


async def test_login_via_endpoint(client: AsyncClient, admin_user) -> None:
    response = await client.post("/api/v1/auth/login", json={
        "email": "admin@test.com",
        "password": "AdminPass123!",
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


async def test_login_wrong_password(client: AsyncClient, admin_user) -> None:
    response = await client.post("/api/v1/auth/login", json={
        "email": "admin@test.com",
        "password": "WrongPassword!",
    })
    assert response.status_code == 401


async def test_login_unknown_user(client: AsyncClient) -> None:
    response = await client.post("/api/v1/auth/login", json={
        "email": "unknown@test.com",
        "password": "Password123!",
    })
    assert response.status_code == 401


async def test_get_me(client: AsyncClient, admin_user, admin_token) -> None:
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "admin@test.com"
    assert data["role"] == UserRole.ADMIN.value


async def test_get_me_no_token(client: AsyncClient) -> None:
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


async def test_create_user_as_admin(client: AsyncClient, admin_user, admin_token) -> None:
    response = await client.post(
        "/api/v1/auth/users",
        json={
            "email": "newuser@test.com",
            "full_name": "New User",
            "password": "NewPass123!",
            "role": "reviewer",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@test.com"
    assert data["role"] == "reviewer"


async def test_create_user_as_reviewer_forbidden(
    client: AsyncClient, reviewer_user, reviewer_token
) -> None:
    response = await client.post(
        "/api/v1/auth/users",
        json={
            "email": "another@test.com",
            "full_name": "Another",
            "password": "Pass123456!",
            "role": "readonly",
        },
        headers={"Authorization": f"Bearer {reviewer_token}"},
    )
    assert response.status_code == 403
