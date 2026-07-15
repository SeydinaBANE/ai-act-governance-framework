from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pii_scan import PIIScan


class SqlAlchemyPIIScanRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def add(self, scan: PIIScan) -> None:
        self._db.add(scan)
        await self._db.flush()

    async def get(self, scan_id: uuid.UUID) -> PIIScan | None:
        return await self._db.get(PIIScan, scan_id)

    async def list_by_user(
        self, user_id: uuid.UUID, *, page: int, per_page: int
    ) -> tuple[list[PIIScan], int]:
        q = select(PIIScan).where(PIIScan.scanned_by == user_id)
        total_result = await self._db.execute(select(func.count()).select_from(q.subquery()))
        total = total_result.scalar_one()

        result = await self._db.execute(
            q.offset((page - 1) * per_page).limit(per_page).order_by(PIIScan.created_at.desc())
        )
        return list(result.scalars().all()), total
