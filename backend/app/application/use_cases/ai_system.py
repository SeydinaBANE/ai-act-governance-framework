from __future__ import annotations

import uuid
from typing import Any

import structlog

from app.core.exceptions import NotFoundError
from app.domain.ai_system.ports import AISystemRepository
from app.domain.audit_log.ports import AuditLogPort
from app.models.ai_system import AISystem, RiskCategory, SystemStatus
from app.models.user import User

log = structlog.get_logger(__name__)


class CreateAISystem:
    def __init__(self, ai_systems: AISystemRepository, audit_logs: AuditLogPort) -> None:
        self._ai_systems = ai_systems
        self._audit_logs = audit_logs

    async def execute(self, data: dict[str, Any], *, actor: User) -> AISystem:
        system = AISystem(**data, created_by=actor.id)
        await self._ai_systems.add(system)

        await self._audit_logs.record(
            actor=actor,
            action="ai_system.created",
            resource_type="ai_system",
            resource_id=system.id,
            input_payload=data,
            output_summary={"system_id": str(system.id)},
        )
        log.info("system_created", system_id=str(system.id), name=system.name)
        return system


class GetAISystem:
    def __init__(self, ai_systems: AISystemRepository) -> None:
        self._ai_systems = ai_systems

    async def execute(self, system_id: uuid.UUID) -> AISystem:
        system = await self._ai_systems.get(system_id)
        if system is None:
            raise NotFoundError("Système IA", str(system_id))
        return system


class ListAISystems:
    def __init__(self, ai_systems: AISystemRepository) -> None:
        self._ai_systems = ai_systems

    async def execute(
        self,
        *,
        page: int,
        per_page: int,
        status: SystemStatus | None,
        risk_category: RiskCategory | None,
        search: str | None,
    ) -> tuple[list[AISystem], int]:
        return await self._ai_systems.list_systems(
            page=page,
            per_page=per_page,
            status=status,
            risk_category=risk_category,
            search=search,
        )


class UpdateAISystem:
    def __init__(self, ai_systems: AISystemRepository, audit_logs: AuditLogPort) -> None:
        self._ai_systems = ai_systems
        self._audit_logs = audit_logs

    async def execute(
        self, system_id: uuid.UUID, updates: dict[str, Any], *, actor: User
    ) -> AISystem:
        system = await self._ai_systems.get(system_id)
        if system is None:
            raise NotFoundError("Système IA", str(system_id))

        for field, value in updates.items():
            setattr(system, field, value)

        await self._audit_logs.record(
            actor=actor,
            action="ai_system.updated",
            resource_type="ai_system",
            resource_id=system_id,
            input_payload=updates,
        )
        return system


class DeleteAISystem:
    def __init__(self, ai_systems: AISystemRepository, audit_logs: AuditLogPort) -> None:
        self._ai_systems = ai_systems
        self._audit_logs = audit_logs

    async def execute(self, system_id: uuid.UUID, *, actor: User) -> None:
        system = await self._ai_systems.get(system_id)
        if system is None:
            raise NotFoundError("Système IA", str(system_id))

        await self._ai_systems.delete(system)
        await self._audit_logs.record(
            actor=actor,
            action="ai_system.deleted",
            resource_type="ai_system",
            resource_id=system_id,
            output_summary={"name": system.name},
        )
        log.info("system_deleted", system_id=str(system_id))
