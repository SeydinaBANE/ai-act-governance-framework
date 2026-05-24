from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.pii_scan import PIIScanRiskLevel, ScanSourceType, ScanStatus


class PIIScanTextRequest(BaseModel):
    text: str = Field(min_length=1)
    ai_system_id: uuid.UUID | None = None
    confidence_threshold: float = Field(default=0.85, ge=0.0, le=1.0)


class PIIFinding(BaseModel):
    entity_type: str
    start: int
    end: int
    score: float
    context: str | None = None


class PIIScanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    ai_system_id: uuid.UUID | None
    scanned_by: uuid.UUID | None
    source_type: ScanSourceType
    source_name: str | None
    source_hash: str | None
    total_items: int
    pii_found: bool
    findings: list[dict[str, Any]]
    entity_summary: dict[str, int] | None
    confidence_threshold: float
    status: ScanStatus
    risk_level: PIIScanRiskLevel | None
    recommendations: list[str] | None
    created_at: datetime


class PIIScanList(BaseModel):
    items: list[PIIScanOut]
    total: int
