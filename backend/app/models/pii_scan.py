from __future__ import annotations

import enum
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ScanSourceType(enum.StrEnum):
    FILE = "file"
    TEXT = "text"
    DATABASE_SAMPLE = "database_sample"


class ScanStatus(enum.StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class PIIScanRiskLevel(enum.StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


class PIIScan(Base):
    __tablename__ = "pii_scans"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ai_system_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ai_systems.id", ondelete="SET NULL")
    )
    scanned_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    source_type: Mapped[ScanSourceType] = mapped_column(Enum(ScanSourceType), nullable=False)
    source_name: Mapped[str | None] = mapped_column(String(255))
    source_hash: Mapped[str | None] = mapped_column(String(64))
    total_items: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    pii_found: Mapped[bool] = mapped_column(default=False, nullable=False)
    findings: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    entity_summary: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    confidence_threshold: Mapped[float] = mapped_column(Float, default=0.85, nullable=False)
    status: Mapped[ScanStatus] = mapped_column(
        Enum(ScanStatus), nullable=False, default=ScanStatus.COMPLETED
    )
    risk_level: Mapped[PIIScanRiskLevel | None] = mapped_column(Enum(PIIScanRiskLevel))
    recommendations: Mapped[list[str] | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False, index=True
    )

    ai_system: Mapped[AISystem] = relationship("AISystem", foreign_keys=[ai_system_id])  # type: ignore[name-defined]
