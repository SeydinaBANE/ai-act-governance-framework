from __future__ import annotations

import hashlib
import json
from typing import Any

from app.models.audit_log import AuditLog


def compute_hash(
    actor_id: str,
    action: str,
    resource_id: str,
    timestamp: str,
    input_payload: dict[str, Any] | None,
) -> str:
    payload_str = json.dumps(input_payload or {}, sort_keys=True)
    raw = f"{actor_id}|{action}|{resource_id}|{timestamp}|{payload_str}"
    return hashlib.sha256(raw.encode()).hexdigest()


def verify_hash(entry: AuditLog) -> bool:
    expected = compute_hash(
        str(entry.actor_id),
        entry.action,
        str(entry.resource_id) if entry.resource_id else "",
        entry.created_at.isoformat(),
        entry.input_payload,
    )
    return expected == entry.payload_hash
