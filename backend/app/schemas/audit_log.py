from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    actor_id: uuid.UUID | None
    actor_email: str
    action: str
    resource_type: str | None
    resource_id: uuid.UUID | None
    input_payload: dict[str, Any] | None
    output_summary: dict[str, Any] | None
    payload_hash: str
    ip_address: str | None
    created_at: datetime


class AuditLogList(BaseModel):
    items: list[AuditLogOut]
    total: int


class HashVerifyResult(BaseModel):
    log_id: uuid.UUID
    valid: bool
    hash_match: bool
    stored_hash: str
    computed_hash: str
