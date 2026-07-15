from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Protocol

from app.models.ai_system import AISystem
from app.models.model_card import ModelCard
from app.models.risk_assessment import RiskAssessment


@dataclass(frozen=True)
class ModelCardGenerationContext:
    system: AISystem
    assessment: RiskAssessment | None


class ModelCardRepository(Protocol):
    async def add(self, card: ModelCard) -> None: ...

    async def get(self, card_id: uuid.UUID) -> ModelCard | None: ...

    async def list_by_system(self, system_id: uuid.UUID) -> list[ModelCard]: ...

    async def get_latest_by_system(self, system_id: uuid.UUID) -> ModelCard | None: ...


class LLMPort(Protocol):
    async def generate_sections(self, context: ModelCardGenerationContext) -> dict[str, str]: ...
