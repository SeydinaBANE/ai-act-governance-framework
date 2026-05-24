from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


async def _create_system(client: AsyncClient, token: str, name: str = "Système Test") -> dict:
    response = await client.post(
        "/api/v1/systems",
        json={"name": name, "description": "Système de test", "is_autonomous": False, "affects_persons": True},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    return response.json()


async def test_list_systems_empty(client: AsyncClient, admin_token: str) -> None:
    response = await client.get(
        "/api/v1/systems",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


async def test_create_system(client: AsyncClient, reviewer_token: str) -> None:
    system = await _create_system(client, reviewer_token)
    assert system["name"] == "Système Test"
    assert system["status"] == "draft"
    assert system["id"] is not None
    assert system["is_autonomous"] is False
    assert system["affects_persons"] is True


async def test_create_system_readonly_forbidden(client: AsyncClient, db: AsyncSession, admin_token: str) -> None:
    from app.core.security import create_access_token, hash_password
    from app.models.user import User, UserRole

    readonly = User(
        email="readonly_systems@test.com",
        full_name="Read Only",
        hashed_password=hash_password("ReadOnly123!"),
        role=UserRole.READONLY,
    )
    db.add(readonly)
    await db.flush()
    token = create_access_token({"sub": str(readonly.id), "email": readonly.email, "role": "readonly"})

    response = await client.post(
        "/api/v1/systems",
        json={"name": "Interdit"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


async def test_get_system(client: AsyncClient, reviewer_token: str) -> None:
    system = await _create_system(client, reviewer_token, "System Get Test")
    response = await client.get(
        f"/api/v1/systems/{system['id']}",
        headers={"Authorization": f"Bearer {reviewer_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == system["id"]
    assert data["name"] == "System Get Test"


async def test_get_system_not_found(client: AsyncClient, admin_token: str) -> None:
    import uuid
    response = await client.get(
        f"/api/v1/systems/{uuid.uuid4()}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 404


async def test_update_system(client: AsyncClient, reviewer_token: str) -> None:
    system = await _create_system(client, reviewer_token)
    response = await client.patch(
        f"/api/v1/systems/{system['id']}",
        json={"status": "under_review", "version": "2.0"},
        headers={"Authorization": f"Bearer {reviewer_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "under_review"
    assert data["version"] == "2.0"


async def test_delete_system_as_admin(client: AsyncClient, admin_token: str) -> None:
    system = await _create_system(client, admin_token)
    response = await client.delete(
        f"/api/v1/systems/{system['id']}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 204

    # Verify deleted
    get_response = await client.get(
        f"/api/v1/systems/{system['id']}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert get_response.status_code == 404


async def test_delete_system_as_reviewer_forbidden(client: AsyncClient, reviewer_token: str) -> None:
    system = await _create_system(client, reviewer_token)
    response = await client.delete(
        f"/api/v1/systems/{system['id']}",
        headers={"Authorization": f"Bearer {reviewer_token}"},
    )
    assert response.status_code == 403


async def test_list_systems_with_search(client: AsyncClient, reviewer_token: str) -> None:
    await _create_system(client, reviewer_token, "ChatBot Service Client")
    await _create_system(client, reviewer_token, "Scoring RH Autonome")

    response = await client.get(
        "/api/v1/systems?search=ChatBot",
        headers={"Authorization": f"Bearer {reviewer_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert all("ChatBot" in item["name"] or "chatbot" in item["name"].lower() for item in data["items"])


async def test_create_system_audit_log_created(client: AsyncClient, reviewer_token: str, admin_token: str) -> None:
    system = await _create_system(client, reviewer_token)

    audit_response = await client.get(
        f"/api/v1/audit/ai_system/{system['id']}",
        headers={"Authorization": f"Bearer {reviewer_token}"},
    )
    assert audit_response.status_code == 200
    audit_data = audit_response.json()
    assert audit_data["total"] >= 1
    assert any(entry["action"] == "ai_system.created" for entry in audit_data["items"])
