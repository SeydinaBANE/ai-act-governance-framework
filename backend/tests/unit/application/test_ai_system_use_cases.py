from __future__ import annotations

import uuid

import pytest
from app.application.use_cases.ai_system import (
    CreateAISystem,
    DeleteAISystem,
    GetAISystem,
    ListAISystems,
    UpdateAISystem,
)
from app.core.exceptions import NotFoundError
from app.models.ai_system import SystemStatus

from tests.factories.ai_system_factory import AISystemFactory
from tests.factories.user_factory import UserFactory
from tests.fakes.repositories import InMemoryAISystemRepository, InMemoryAuditLogRepository


async def test_create_ai_system_adds_system_and_records_audit() -> None:
    ai_systems = InMemoryAISystemRepository()
    audit_logs = InMemoryAuditLogRepository()
    actor = UserFactory.build()

    system = await CreateAISystem(ai_systems, audit_logs).execute(
        {"name": "Scoring crédit", "description": "Système de scoring"}, actor=actor
    )

    assert system.name == "Scoring crédit"
    assert system.created_by == actor.id
    assert len(ai_systems.systems) == 1
    assert audit_logs.entries[0].action == "ai_system.created"


async def test_get_ai_system_returns_system() -> None:
    system = AISystemFactory.build()
    ai_systems = InMemoryAISystemRepository([system])

    result = await GetAISystem(ai_systems).execute(system.id)

    assert result.id == system.id


async def test_get_ai_system_missing_raises() -> None:
    ai_systems = InMemoryAISystemRepository([])

    with pytest.raises(NotFoundError):
        await GetAISystem(ai_systems).execute(uuid.uuid4())


async def test_list_ai_systems_filters_by_status() -> None:
    draft = AISystemFactory.build(status=SystemStatus.DRAFT)
    compliant = AISystemFactory.build(status=SystemStatus.COMPLIANT)
    ai_systems = InMemoryAISystemRepository([draft, compliant])

    items, total = await ListAISystems(ai_systems).execute(
        page=1, per_page=10, status=SystemStatus.COMPLIANT, risk_category=None, search=None
    )

    assert total == 1
    assert items[0].id == compliant.id


async def test_update_ai_system_applies_fields_and_records_audit() -> None:
    system = AISystemFactory.build(name="Ancien nom")
    ai_systems = InMemoryAISystemRepository([system])
    audit_logs = InMemoryAuditLogRepository()
    actor = UserFactory.build()

    updated = await UpdateAISystem(ai_systems, audit_logs).execute(
        system.id, {"name": "Nouveau nom"}, actor=actor
    )

    assert updated.name == "Nouveau nom"
    assert audit_logs.entries[0].action == "ai_system.updated"


async def test_update_ai_system_missing_raises() -> None:
    ai_systems = InMemoryAISystemRepository([])
    audit_logs = InMemoryAuditLogRepository()

    with pytest.raises(NotFoundError):
        await UpdateAISystem(ai_systems, audit_logs).execute(
            uuid.uuid4(), {"name": "x"}, actor=UserFactory.build()
        )


async def test_delete_ai_system_removes_system_and_records_audit() -> None:
    system = AISystemFactory.build()
    ai_systems = InMemoryAISystemRepository([system])
    audit_logs = InMemoryAuditLogRepository()
    actor = UserFactory.build()

    await DeleteAISystem(ai_systems, audit_logs).execute(system.id, actor=actor)

    assert ai_systems.systems == []
    assert audit_logs.entries[0].action == "ai_system.deleted"


async def test_delete_ai_system_missing_raises() -> None:
    ai_systems = InMemoryAISystemRepository([])
    audit_logs = InMemoryAuditLogRepository()

    with pytest.raises(NotFoundError):
        await DeleteAISystem(ai_systems, audit_logs).execute(
            uuid.uuid4(), actor=UserFactory.build()
        )
