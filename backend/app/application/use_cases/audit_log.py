from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

import structlog

from app.core.exceptions import NotFoundError
from app.domain.audit_log.hashing import compute_hash
from app.domain.audit_log.ports import AuditLogPort
from app.models.audit_log import AuditLog

log = structlog.get_logger(__name__)


@dataclass(frozen=True)
class AuditLogIntegrityResult:
    log_id: uuid.UUID
    valid: bool
    stored_hash: str
    computed_hash: str


class ListAuditLogs:
    def __init__(self, audit_logs: AuditLogPort) -> None:
        self._audit_logs = audit_logs

    async def execute(
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
        return await self._audit_logs.list_logs(
            page=page,
            per_page=per_page,
            actor_id=actor_id,
            resource_type=resource_type,
            action=action,
            from_date=from_date,
            to_date=to_date,
        )


class GetResourceAuditLogs:
    def __init__(self, audit_logs: AuditLogPort) -> None:
        self._audit_logs = audit_logs

    async def execute(
        self,
        resource_type: str,
        resource_id: uuid.UUID,
        *,
        page: int,
        per_page: int,
    ) -> tuple[list[AuditLog], int]:
        return await self._audit_logs.list_for_resource(
            resource_type, resource_id, page=page, per_page=per_page
        )


class VerifyAuditLogIntegrity:
    def __init__(self, audit_logs: AuditLogPort) -> None:
        self._audit_logs = audit_logs

    async def execute(self, log_id: uuid.UUID) -> AuditLogIntegrityResult:
        entry = await self._audit_logs.get(log_id)
        if entry is None:
            raise NotFoundError("Log d'audit", str(log_id))

        computed = compute_hash(
            str(entry.actor_id),
            entry.action,
            str(entry.resource_id) if entry.resource_id else "",
            entry.created_at.isoformat(),
            entry.input_payload,
        )
        is_valid = computed == entry.payload_hash
        if not is_valid:
            log.warning("audit_hash_mismatch", log_id=str(log_id))

        return AuditLogIntegrityResult(
            log_id=log_id,
            valid=is_valid,
            stored_hash=entry.payload_hash,
            computed_hash=computed,
        )
