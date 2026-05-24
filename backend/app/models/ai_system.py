from __future__ import annotations

import enum
import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class SystemStatus(str, enum.Enum):
    DRAFT = "draft"
    UNDER_REVIEW = "under_review"
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    EXEMPTED = "exempted"


class RiskCategory(str, enum.Enum):
    PROHIBITED = "prohibited"
    HIGH_RISK = "high_risk"
    LIMITED_RISK = "limited_risk"
    MINIMAL_RISK = "minimal_risk"


class AISystem(Base):
    __tablename__ = "ai_systems"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    version: Mapped[str | None] = mapped_column(String(100))
    owner_team: Mapped[str | None] = mapped_column(String(255))
    tech_stack: Mapped[list[str] | None] = mapped_column(JSONB)
    deployment_env: Mapped[str | None] = mapped_column(String(100))
    use_case: Mapped[str | None] = mapped_column(Text)
    data_types: Mapped[list[str] | None] = mapped_column(JSONB)
    is_autonomous: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    affects_persons: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[SystemStatus] = mapped_column(
        Enum(SystemStatus), nullable=False, default=SystemStatus.DRAFT
    )
    current_risk_category: Mapped[RiskCategory | None] = mapped_column(Enum(RiskCategory))
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    creator: Mapped["User"] = relationship("User", foreign_keys=[created_by], lazy="selectin")  # type: ignore[name-defined]

    def __repr__(self) -> str:
        return f"<AISystem {self.name} [{self.status}]>"
