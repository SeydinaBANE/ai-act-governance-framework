from __future__ import annotations

import hashlib
import json
import uuid
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.models.user import User

log = structlog.get_logger(__name__)


def _compute_hash(
    actor_id: str,
    action: str,
    resource_id: str,
    timestamp: str,
    input_payload: dict[str, Any] | None,
) -> str:
    raw = f"{actor_id}|{action}|{resource_id}|{timestamp}|{json.dumps(input_payload or {}, sort_keys=True)}"
    return hashlib.sha256(raw.encode()).hexdigest()


async def log_action(
    db: AsyncSession,
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
    entry = AuditLog()
    # compute timestamp before persisting
    from datetime import UTC, datetime
    ts = datetime.now(UTC)

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
    entry.payload_hash = _compute_hash(
        str(actor.id), action, rid, ts.isoformat(), input_payload
    )

    db.add(entry)
    await db.flush()

    log.info("audit_log_created", action=action, resource_type=resource_type, resource_id=rid)
    return entry


def verify_hash(entry: AuditLog) -> bool:
    expected = _compute_hash(
        str(entry.actor_id),
        entry.action,
        str(entry.resource_id) if entry.resource_id else "",
        entry.created_at.isoformat(),
        entry.input_payload,
    )
    return expected == entry.payload_hash
