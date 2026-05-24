from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.ai_system import RiskCategory, SystemStatus


class AISystemCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    description: str | None = None
    version: str | None = Field(None, max_length=100)
    owner_team: str | None = Field(None, max_length=255)
    tech_stack: list[str] | None = None
    deployment_env: str | None = Field(None, max_length=100)
    use_case: str | None = None
    data_types: list[str] | None = None
    is_autonomous: bool = False
    affects_persons: bool = False


class AISystemUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=255)
    description: str | None = None
    version: str | None = None
    owner_team: str | None = None
    tech_stack: list[str] | None = None
    deployment_env: str | None = None
    use_case: str | None = None
    data_types: list[str] | None = None
    is_autonomous: bool | None = None
    affects_persons: bool | None = None
    status: SystemStatus | None = None


class AISystemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None
    version: str | None
    owner_team: str | None
    tech_stack: list[str] | None
    deployment_env: str | None
    use_case: str | None
    data_types: list[str] | None
    is_autonomous: bool
    affects_persons: bool
    status: SystemStatus
    current_risk_category: RiskCategory | None
    created_by: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


class AISystemList(BaseModel):
    items: list[AISystemOut]
    total: int
    page: int
    per_page: int
