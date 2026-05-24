from __future__ import annotations

import uuid
from datetime import UTC, date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.ai_system import RiskCategory


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ai_system_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ai_systems.id", ondelete="CASCADE"), nullable=False
    )
    assessed_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    questionnaire: Mapped[dict] = mapped_column(JSONB, nullable=False)
    score_details: Mapped[dict] = mapped_column(JSONB, nullable=False)
    total_score: Mapped[int] = mapped_column(Integer, nullable=False)
    risk_category: Mapped[RiskCategory] = mapped_column(String(50), nullable=False)
    justification: Mapped[str | None] = mapped_column(Text)
    ai_act_articles: Mapped[list[str] | None] = mapped_column(JSONB)
    required_actions: Mapped[list[dict] | None] = mapped_column(JSONB)
    valid_until: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    ai_system: Mapped[AISystem] = relationship("AISystem", foreign_keys=[ai_system_id])  # type: ignore[name-defined]
    assessor: Mapped[User] = relationship("User", foreign_keys=[assessed_by])  # type: ignore[name-defined]
