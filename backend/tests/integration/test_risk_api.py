from __future__ import annotations

import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_system import AISystem


async def test_get_questionnaire(client: AsyncClient, reviewer_user, reviewer_token) -> None:
    response = await client.get(
        "/api/v1/risk/questionnaire",
        headers={"Authorization": f"Bearer {reviewer_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "sections" in data
    assert len(data["sections"]) > 0


async def _create_system(client: AsyncClient, token: str) -> str:
    response = await client.post(
        "/api/v1/systems",
        json={"name": "Test System", "description": "A test AI system"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    return response.json()["id"]


async def test_assess_minimal_risk(client: AsyncClient, reviewer_user, reviewer_token) -> None:
    system_id = await _create_system(client, reviewer_token)

    response = await client.post(
        f"/api/v1/risk/assess/{system_id}",
        json={"answers": {}},
        headers={"Authorization": f"Bearer {reviewer_token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["risk_category"] == "minimal_risk"
    assert data["total_score"] == 0
    assert data["ai_system_id"] == system_id


async def test_assess_prohibited(client: AsyncClient, reviewer_user, reviewer_token) -> None:
    system_id = await _create_system(client, reviewer_token)

    response = await client.post(
        f"/api/v1/risk/assess/{system_id}",
        json={"answers": {"q1_biometric_realtime": True}},
        headers={"Authorization": f"Bearer {reviewer_token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["risk_category"] == "prohibited"


async def test_assess_high_risk(client: AsyncClient, reviewer_user, reviewer_token) -> None:
    system_id = await _create_system(client, reviewer_token)

    response = await client.post(
        f"/api/v1/risk/assess/{system_id}",
        json={"answers": {"q7_employment": True}},
        headers={"Authorization": f"Bearer {reviewer_token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["risk_category"] == "high_risk"
    assert len(data["required_actions"]) > 0


async def test_assess_nonexistent_system(client: AsyncClient, reviewer_user, reviewer_token) -> None:
    fake_id = str(uuid.uuid4())
    response = await client.post(
        f"/api/v1/risk/assess/{fake_id}",
        json={"answers": {}},
        headers={"Authorization": f"Bearer {reviewer_token}"},
    )
    assert response.status_code == 404


async def test_list_assessments(client: AsyncClient, reviewer_user, reviewer_token) -> None:
    system_id = await _create_system(client, reviewer_token)
    await client.post(
        f"/api/v1/risk/assess/{system_id}",
        json={"answers": {}},
        headers={"Authorization": f"Bearer {reviewer_token}"},
    )

    response = await client.get(
        f"/api/v1/risk/assessments/{system_id}",
        headers={"Authorization": f"Bearer {reviewer_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
