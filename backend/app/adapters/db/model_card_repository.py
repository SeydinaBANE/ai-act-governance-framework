from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.model_card import ModelCard


class SqlAlchemyModelCardRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def add(self, card: ModelCard) -> None:
        self._db.add(card)
        await self._db.flush()

    async def get(self, card_id: uuid.UUID) -> ModelCard | None:
        return await self._db.get(ModelCard, card_id)

    async def list_by_system(self, system_id: uuid.UUID) -> list[ModelCard]:
        result = await self._db.execute(
            select(ModelCard)
            .where(ModelCard.ai_system_id == system_id)
            .order_by(ModelCard.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_latest_by_system(self, system_id: uuid.UUID) -> ModelCard | None:
        result = await self._db.execute(
            select(ModelCard)
            .where(ModelCard.ai_system_id == system_id)
            .order_by(ModelCard.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
