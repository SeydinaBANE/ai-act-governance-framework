from __future__ import annotations

import enum
import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ModelCardStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class ModelCard(Base):
    __tablename__ = "model_cards"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    ai_system_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ai_systems.id", ondelete="CASCADE"), nullable=False
    )
    version: Mapped[str] = mapped_column(String(50), default="1.0", nullable=False)

    # Section 1 — Informations générales
    model_name: Mapped[str] = mapped_column(String(255), nullable=False)
    model_type: Mapped[str | None] = mapped_column(String(100))
    architecture: Mapped[str | None] = mapped_column(String(255))
    framework: Mapped[str | None] = mapped_column(String(100))
    license: Mapped[str | None] = mapped_column(String(100))

    # Section 2 — Données d'entraînement
    training_datasets: Mapped[list[dict] | None] = mapped_column(JSONB)
    preprocessing_steps: Mapped[str | None] = mapped_column(Text)
    known_biases: Mapped[str | None] = mapped_column(Text)

    # Section 3 — Performance
    metrics: Mapped[list[dict] | None] = mapped_column(JSONB)
    evaluation_procedure: Mapped[str | None] = mapped_column(Text)

    # Section 4 — Limitations
    limitations: Mapped[str | None] = mapped_column(Text)
    out_of_scope_uses: Mapped[str | None] = mapped_column(Text)
    ethical_considerations: Mapped[str | None] = mapped_column(Text)

    # Section 5 — Conformité AI Act
    risk_level: Mapped[str | None] = mapped_column(String(50))
    conformity_measures: Mapped[str | None] = mapped_column(Text)
    human_oversight: Mapped[str | None] = mapped_column(Text)

    # Section 6 — Contacts
    developer_contact: Mapped[str | None] = mapped_column(String(255))
    dpo_contact: Mapped[str | None] = mapped_column(String(255))

    status: Mapped[ModelCardStatus] = mapped_column(
        Enum(ModelCardStatus), nullable=False, default=ModelCardStatus.DRAFT
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
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

    ai_system: Mapped["AISystem"] = relationship("AISystem", foreign_keys=[ai_system_id])  # type: ignore[name-defined]
