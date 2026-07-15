from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from app.domain.audit_log.hashing import compute_hash
from app.models.ai_system import AISystem, RiskCategory, SystemStatus
from app.models.audit_log import AuditLog
from app.models.model_card import ModelCard
from app.models.pii_scan import PIIScan
from app.models.risk_assessment import RiskAssessment
from app.models.user import User


class InMemoryAuditLogRepository:
    def __init__(self) -> None:
        self.entries: list[AuditLog] = []

    async def record(
        self,
        *,
        actor: User,
        action: str,
        resource_type: str | None = None,
        resource_id: uuid.UUID | None = None,
        input_payload: dict[str, Any] | None = None,
        output_summary: dict[str, Any] | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        request_id: uuid.UUID | None = None,
    ) -> AuditLog:
        rid = str(resource_id) if resource_id else ""
        ts = datetime.now(UTC)

        entry = AuditLog()
        entry.id = uuid.uuid4()
        entry.actor_id = actor.id
        entry.actor_email = actor.email
        entry.action = action
        entry.resource_type = resource_type
        entry.resource_id = resource_id
        entry.input_payload = input_payload
        entry.output_summary = output_summary
        entry.ip_address = ip_address
        entry.user_agent = user_agent
        entry.request_id = request_id
        entry.created_at = ts
        entry.payload_hash = compute_hash(str(actor.id), action, rid, ts.isoformat(), input_payload)

        self.entries.append(entry)
        return entry

    async def list_logs(
        self,
        *,
        page: int,
        per_page: int,
        actor_id: uuid.UUID | None = None,
        resource_type: str | None = None,
        action: str | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> tuple[list[AuditLog], int]:
        results = self.entries
        if actor_id:
            results = [e for e in results if e.actor_id == actor_id]
        if resource_type:
            results = [e for e in results if e.resource_type == resource_type]
        if action:
            results = [e for e in results if action.lower() in e.action.lower()]
        if from_date:
            results = [e for e in results if e.created_at >= from_date]
        if to_date:
            results = [e for e in results if e.created_at <= to_date]

        results = sorted(results, key=lambda e: e.created_at, reverse=True)
        total = len(results)
        start = (page - 1) * per_page
        return results[start : start + per_page], total

    async def list_for_resource(
        self,
        resource_type: str,
        resource_id: uuid.UUID,
        *,
        page: int,
        per_page: int,
    ) -> tuple[list[AuditLog], int]:
        results = [
            e
            for e in self.entries
            if e.resource_type == resource_type and e.resource_id == resource_id
        ]
        results = sorted(results, key=lambda e: e.created_at, reverse=True)
        total = len(results)
        start = (page - 1) * per_page
        return results[start : start + per_page], total

    async def get(self, log_id: uuid.UUID) -> AuditLog | None:
        return next((e for e in self.entries if e.id == log_id), None)


class InMemoryAISystemRepository:
    def __init__(self, systems: list[AISystem] | None = None) -> None:
        self.systems: list[AISystem] = systems or []

    async def add(self, system: AISystem) -> None:
        if system.id is None:
            system.id = uuid.uuid4()
        if system.created_at is None:
            system.created_at = datetime.now(UTC)
        self.systems.append(system)

    async def get(self, system_id: uuid.UUID) -> AISystem | None:
        return next((s for s in self.systems if s.id == system_id), None)

    async def list_systems(
        self,
        *,
        page: int,
        per_page: int,
        status: SystemStatus | None,
        risk_category: RiskCategory | None,
        search: str | None,
    ) -> tuple[list[AISystem], int]:
        results = self.systems
        if status:
            results = [s for s in results if s.status == status]
        if risk_category:
            results = [s for s in results if s.current_risk_category == risk_category]
        if search:
            results = [s for s in results if search.lower() in s.name.lower()]

        results = sorted(results, key=lambda s: s.created_at, reverse=True)
        total = len(results)
        start = (page - 1) * per_page
        return results[start : start + per_page], total

    async def delete(self, system: AISystem) -> None:
        self.systems = [s for s in self.systems if s.id != system.id]


class InMemoryRiskAssessmentRepository:
    def __init__(self) -> None:
        self.assessments: list[RiskAssessment] = []

    async def add(self, assessment: RiskAssessment) -> None:
        if assessment.id is None:
            assessment.id = uuid.uuid4()
        if assessment.created_at is None:
            assessment.created_at = datetime.now(UTC)
        self.assessments.append(assessment)

    async def list_by_system(self, system_id: uuid.UUID) -> list[RiskAssessment]:
        results = [a for a in self.assessments if a.ai_system_id == system_id]
        return sorted(results, key=lambda a: a.created_at, reverse=True)


class InMemoryPIIScanRepository:
    def __init__(self) -> None:
        self.scans: list[PIIScan] = []

    async def add(self, scan: PIIScan) -> None:
        if scan.id is None:
            scan.id = uuid.uuid4()
        if scan.created_at is None:
            scan.created_at = datetime.now(UTC)
        self.scans.append(scan)

    async def get(self, scan_id: uuid.UUID) -> PIIScan | None:
        return next((s for s in self.scans if s.id == scan_id), None)

    async def list_by_user(
        self, user_id: uuid.UUID, *, page: int, per_page: int
    ) -> tuple[list[PIIScan], int]:
        results = [s for s in self.scans if s.scanned_by == user_id]
        results = sorted(results, key=lambda s: s.created_at, reverse=True)
        total = len(results)
        start = (page - 1) * per_page
        return results[start : start + per_page], total


class InMemoryUserRepository:
    def __init__(self, users: list[User] | None = None) -> None:
        self.users: list[User] = users or []

    async def get(self, user_id: uuid.UUID) -> User | None:
        return next((u for u in self.users if u.id == user_id), None)

    async def get_by_email(self, email: str) -> User | None:
        return next((u for u in self.users if u.email == email), None)

    async def add(self, user: User) -> None:
        if user.id is None:
            user.id = uuid.uuid4()
        self.users.append(user)


class InMemoryModelCardRepository:
    def __init__(self) -> None:
        self.cards: list[ModelCard] = []

    async def add(self, card: ModelCard) -> None:
        if card.id is None:
            card.id = uuid.uuid4()
        if card.created_at is None:
            card.created_at = datetime.now(UTC)
        self.cards.append(card)

    async def get(self, card_id: uuid.UUID) -> ModelCard | None:
        return next((c for c in self.cards if c.id == card_id), None)

    async def list_by_system(self, system_id: uuid.UUID) -> list[ModelCard]:
        results = [c for c in self.cards if c.ai_system_id == system_id]
        return sorted(results, key=lambda c: c.created_at, reverse=True)

    async def get_latest_by_system(self, system_id: uuid.UUID) -> ModelCard | None:
        items = await self.list_by_system(system_id)
        return items[0] if items else None
