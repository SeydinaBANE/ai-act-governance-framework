from __future__ import annotations

import uuid
from typing import Protocol

from app.models.ai_system import AISystem, RiskCategory, SystemStatus


class AISystemRepository(Protocol):
    async def add(self, system: AISystem) -> None: ...

    async def get(self, system_id: uuid.UUID) -> AISystem | None: ...

    async def list_systems(
        self,
        *,
        page: int,
        per_page: int,
        status: SystemStatus | None,
        risk_category: RiskCategory | None,
        search: str | None,
    ) -> tuple[list[AISystem], int]: ...

    async def delete(self, system: AISystem) -> None: ...
