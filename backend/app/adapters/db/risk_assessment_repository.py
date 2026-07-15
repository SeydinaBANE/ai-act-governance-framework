from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.risk_assessment import RiskAssessment


class SqlAlchemyRiskAssessmentRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def add(self, assessment: RiskAssessment) -> None:
        self._db.add(assessment)
        await self._db.flush()

    async def list_by_system(self, system_id: uuid.UUID) -> list[RiskAssessment]:
        result = await self._db.execute(
            select(RiskAssessment)
            .where(RiskAssessment.ai_system_id == system_id)
            .order_by(RiskAssessment.created_at.desc())
        )
        return list(result.scalars().all())
