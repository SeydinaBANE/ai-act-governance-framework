from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Protocol

from app.models.audit_log import AuditLog
from app.models.user import User


class AuditLogPort(Protocol):
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
    ) -> AuditLog: ...

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
    ) -> tuple[list[AuditLog], int]: ...

    async def list_for_resource(
        self,
        resource_type: str,
        resource_id: uuid.UUID,
        *,
        page: int,
        per_page: int,
    ) -> tuple[list[AuditLog], int]: ...

    async def get(self, log_id: uuid.UUID) -> AuditLog | None: ...
