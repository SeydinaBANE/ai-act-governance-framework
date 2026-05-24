from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.model_card import ModelCardStatus


class MetricItem(BaseModel):
    name: str
    value: float | str
    dataset: str | None = None


class DatasetItem(BaseModel):
    name: str
    description: str | None = None
    size: str | None = None


class ModelCardCreate(BaseModel):
    model_name: str = Field(min_length=2, max_length=255)
    model_type: str | None = None
    architecture: str | None = None
    framework: str | None = None
    license: str | None = None
    training_datasets: list[DatasetItem] | None = None
    preprocessing_steps: str | None = None
    known_biases: str | None = None
    metrics: list[MetricItem] | None = None
    evaluation_procedure: str | None = None
    limitations: str | None = None
    out_of_scope_uses: str | None = None
    ethical_considerations: str | None = None
    risk_level: str | None = None
    conformity_measures: str | None = None
    human_oversight: str | None = None
    developer_contact: str | None = None
    dpo_contact: str | None = None


class ModelCardUpdate(BaseModel):
    model_name: str | None = Field(None, min_length=2, max_length=255)
    model_type: str | None = None
    architecture: str | None = None
    framework: str | None = None
    license: str | None = None
    training_datasets: list[DatasetItem] | None = None
    preprocessing_steps: str | None = None
    known_biases: str | None = None
    metrics: list[MetricItem] | None = None
    evaluation_procedure: str | None = None
    limitations: str | None = None
    out_of_scope_uses: str | None = None
    ethical_considerations: str | None = None
    risk_level: str | None = None
    conformity_measures: str | None = None
    human_oversight: str | None = None
    developer_contact: str | None = None
    dpo_contact: str | None = None
    status: ModelCardStatus | None = None


class ModelCardOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    ai_system_id: uuid.UUID
    version: str
    model_name: str
    model_type: str | None
    architecture: str | None
    framework: str | None
    license: str | None
    training_datasets: list[dict[str, Any]] | None
    preprocessing_steps: str | None
    known_biases: str | None
    metrics: list[dict[str, Any]] | None
    evaluation_procedure: str | None
    limitations: str | None
    out_of_scope_uses: str | None
    ethical_considerations: str | None
    risk_level: str | None
    conformity_measures: str | None
    human_oversight: str | None
    developer_contact: str | None
    dpo_contact: str | None
    status: ModelCardStatus
    created_by: uuid.UUID | None
    reviewed_by: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


class ModelCardList(BaseModel):
    items: list[ModelCardOut]
    total: int


class AIGenerateRequest(BaseModel):
    """Demande de génération automatique des sections textuelles via LLM."""

    pass
