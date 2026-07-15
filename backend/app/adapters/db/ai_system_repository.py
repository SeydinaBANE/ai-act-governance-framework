from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_system import AISystem, RiskCategory, SystemStatus


class SqlAlchemyAISystemRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def add(self, system: AISystem) -> None:
        self._db.add(system)
        await self._db.flush()

    async def get(self, system_id: uuid.UUID) -> AISystem | None:
        return await self._db.get(AISystem, system_id)

    async def list_systems(
        self,
        *,
        page: int,
        per_page: int,
        status: SystemStatus | None,
        risk_category: RiskCategory | None,
        search: str | None,
    ) -> tuple[list[AISystem], int]:
        q = select(AISystem)
        if status:
            q = q.where(AISystem.status == status)
        if risk_category:
            q = q.where(AISystem.current_risk_category == risk_category)
        if search:
            q = q.where(AISystem.name.ilike(f"%{search}%"))

        total_result = await self._db.execute(select(func.count()).select_from(q.subquery()))
        total = total_result.scalar_one()

        q = q.offset((page - 1) * per_page).limit(per_page).order_by(AISystem.created_at.desc())
        result = await self._db.execute(q)
        return list(result.scalars().all()), total

    async def delete(self, system: AISystem) -> None:
        await self._db.delete(system)
