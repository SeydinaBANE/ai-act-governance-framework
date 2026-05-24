from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.models.ai_system import RiskCategory


class RiskAssessmentRequest(BaseModel):
    answers: dict[str, bool]


class RequiredAction(BaseModel):
    article: str
    obligation: str
    deadline: str


class RiskAssessmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    ai_system_id: uuid.UUID
    assessed_by: uuid.UUID | None
    total_score: int
    risk_category: RiskCategory
    justification: str | None
    ai_act_articles: list[str] | None
    required_actions: list[dict] | None
    valid_until: date | None
    created_at: datetime


class RiskAssessmentList(BaseModel):
    items: list[RiskAssessmentOut]
    total: int
