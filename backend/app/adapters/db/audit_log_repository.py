from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.audit_log.hashing import compute_hash
from app.models.audit_log import AuditLog
from app.models.user import User

log = structlog.get_logger(__name__)


class SqlAlchemyAuditLogRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

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

        self._db.add(entry)
        await self._db.flush()

        log.info("audit_log_created", action=action, resource_type=resource_type, resource_id=rid)
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
        q = select(AuditLog)
        if actor_id:
            q = q.where(AuditLog.actor_id == actor_id)
        if resource_type:
            q = q.where(AuditLog.resource_type == resource_type)
        if action:
            q = q.where(AuditLog.action.ilike(f"%{action}%"))
        if from_date:
            q = q.where(AuditLog.created_at >= from_date)
        if to_date:
            q = q.where(AuditLog.created_at <= to_date)

        total_result = await self._db.execute(select(func.count()).select_from(q.subquery()))
        total = total_result.scalar_one()

        result = await self._db.execute(
            q.offset((page - 1) * per_page).limit(per_page).order_by(AuditLog.created_at.desc())
        )
        return list(result.scalars().all()), total

    async def list_for_resource(
        self,
        resource_type: str,
        resource_id: uuid.UUID,
        *,
        page: int,
        per_page: int,
    ) -> tuple[list[AuditLog], int]:
        q = select(AuditLog).where(
            AuditLog.resource_type == resource_type,
            AuditLog.resource_id == resource_id,
        )
        total_result = await self._db.execute(select(func.count()).select_from(q.subquery()))
        total = total_result.scalar_one()

        result = await self._db.execute(
            q.offset((page - 1) * per_page).limit(per_page).order_by(AuditLog.created_at.desc())
        )
        return list(result.scalars().all()), total

    async def get(self, log_id: uuid.UUID) -> AuditLog | None:
        return await self._db.get(AuditLog, log_id)
