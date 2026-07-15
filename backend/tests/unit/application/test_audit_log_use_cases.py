from __future__ import annotations

import uuid

import pytest
from app.application.use_cases.audit_log import (
    GetResourceAuditLogs,
    ListAuditLogs,
    VerifyAuditLogIntegrity,
)
from app.core.exceptions import NotFoundError
from app.models.user import User, UserRole

from tests.fakes.repositories import InMemoryAuditLogRepository


def _actor() -> User:
    return User(
        id=uuid.uuid4(),
        email="admin@test.com",
        full_name="Admin",
        hashed_password="hashed",
        role=UserRole.ADMIN,
    )


async def test_list_audit_logs_paginates_most_recent_first() -> None:
    repo = InMemoryAuditLogRepository()
    actor = _actor()
    for action in ("a.created", "a.updated", "a.deleted"):
        await repo.record(actor=actor, action=action)

    items, total = await ListAuditLogs(repo).execute(page=1, per_page=2)

    assert total == 3
    assert len(items) == 2
    assert items[0].action == "a.deleted"


async def test_list_audit_logs_filters_by_action_substring() -> None:
    repo = InMemoryAuditLogRepository()
    actor = _actor()
    await repo.record(actor=actor, action="ai_system.created")
    await repo.record(actor=actor, action="user.created")

    items, total = await ListAuditLogs(repo).execute(page=1, per_page=10, action="ai_system")

    assert total == 1
    assert items[0].action == "ai_system.created"


async def test_get_resource_audit_logs_filters_by_resource() -> None:
    repo = InMemoryAuditLogRepository()
    actor = _actor()
    system_id = uuid.uuid4()
    await repo.record(
        actor=actor, action="ai_system.updated", resource_type="ai_system", resource_id=system_id
    )
    await repo.record(
        actor=actor,
        action="ai_system.updated",
        resource_type="ai_system",
        resource_id=uuid.uuid4(),
    )

    items, total = await GetResourceAuditLogs(repo).execute(
        "ai_system", system_id, page=1, per_page=10
    )

    assert total == 1
    assert items[0].resource_id == system_id


async def test_verify_audit_log_integrity_valid_entry() -> None:
    repo = InMemoryAuditLogRepository()
    entry = await repo.record(actor=_actor(), action="ai_system.created")

    result = await VerifyAuditLogIntegrity(repo).execute(entry.id)

    assert result.valid is True
    assert result.stored_hash == result.computed_hash


async def test_verify_audit_log_integrity_tampered_entry() -> None:
    repo = InMemoryAuditLogRepository()
    entry = await repo.record(actor=_actor(), action="ai_system.created")
    entry.payload_hash = "tampered"

    result = await VerifyAuditLogIntegrity(repo).execute(entry.id)

    assert result.valid is False
    assert result.stored_hash == "tampered"


async def test_verify_audit_log_integrity_missing_entry_raises() -> None:
    repo = InMemoryAuditLogRepository()

    with pytest.raises(NotFoundError):
        await VerifyAuditLogIntegrity(repo).execute(uuid.uuid4())
