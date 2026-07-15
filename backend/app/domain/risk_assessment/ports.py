from __future__ import annotations

import uuid
from typing import Protocol

from app.models.risk_assessment import RiskAssessment


class RiskAssessmentRepository(Protocol):
    async def add(self, assessment: RiskAssessment) -> None: ...

    async def list_by_system(self, system_id: uuid.UUID) -> list[RiskAssessment]: ...
