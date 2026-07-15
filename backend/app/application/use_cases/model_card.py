from __future__ import annotations

import uuid
from typing import Any

import structlog

from app.core.exceptions import NotFoundError, ServiceUnavailableError
from app.domain.ai_system.ports import AISystemRepository
from app.domain.audit_log.ports import AuditLogPort
from app.domain.model_card.ports import LLMPort, ModelCardGenerationContext, ModelCardRepository
from app.domain.risk_assessment.ports import RiskAssessmentRepository
from app.models.model_card import ModelCard, ModelCardStatus
from app.models.user import User

log = structlog.get_logger(__name__)


class CreateModelCard:
    def __init__(
        self,
        model_cards: ModelCardRepository,
        ai_systems: AISystemRepository,
        audit_logs: AuditLogPort,
    ) -> None:
        self._model_cards = model_cards
        self._ai_systems = ai_systems
        self._audit_logs = audit_logs

    async def execute(
        self, system_id: uuid.UUID, data: dict[str, Any], *, actor: User
    ) -> ModelCard:
        system = await self._ai_systems.get(system_id)
        if system is None:
            raise NotFoundError("Système IA", str(system_id))

        card = ModelCard(**data, ai_system_id=system_id, created_by=actor.id)
        await self._model_cards.add(card)

        await self._audit_logs.record(
            actor=actor,
            action="model_card.created",
            resource_type="model_card",
            resource_id=card.id,
            input_payload={"system_id": str(system_id)},
        )
        log.info("model_card_created", card_id=str(card.id), system_id=str(system_id))
        return card


class ListModelCards:
    def __init__(self, model_cards: ModelCardRepository) -> None:
        self._model_cards = model_cards

    async def execute(self, system_id: uuid.UUID) -> tuple[list[ModelCard], int]:
        items = await self._model_cards.list_by_system(system_id)
        return items, len(items)


class UpdateModelCard:
    def __init__(self, model_cards: ModelCardRepository, audit_logs: AuditLogPort) -> None:
        self._model_cards = model_cards
        self._audit_logs = audit_logs

    async def execute(
        self, card_id: uuid.UUID, updates: dict[str, Any], *, actor: User
    ) -> ModelCard:
        card = await self._model_cards.get(card_id)
        if card is None:
            raise NotFoundError("Model card", str(card_id))

        for field, value in updates.items():
            setattr(card, field, value)

        await self._audit_logs.record(
            actor=actor,
            action="model_card.updated",
            resource_type="model_card",
            resource_id=card_id,
            input_payload=updates,
        )
        return card


class PublishModelCard:
    def __init__(self, model_cards: ModelCardRepository, audit_logs: AuditLogPort) -> None:
        self._model_cards = model_cards
        self._audit_logs = audit_logs

    async def execute(self, card_id: uuid.UUID, *, actor: User) -> ModelCard:
        card = await self._model_cards.get(card_id)
        if card is None:
            raise NotFoundError("Model card", str(card_id))

        card.status = ModelCardStatus.PUBLISHED
        card.reviewed_by = actor.id

        await self._audit_logs.record(
            actor=actor,
            action="model_card.published",
            resource_type="model_card",
            resource_id=card_id,
        )
        return card


class GenerateModelCardSections:
    def __init__(
        self,
        ai_systems: AISystemRepository,
        risk_assessments: RiskAssessmentRepository,
        llm: LLMPort,
    ) -> None:
        self._ai_systems = ai_systems
        self._risk_assessments = risk_assessments
        self._llm = llm

    async def execute(self, system_id: uuid.UUID) -> dict[str, str]:
        system = await self._ai_systems.get(system_id)
        if system is None:
            raise NotFoundError("Système IA", str(system_id))

        assessments = await self._risk_assessments.list_by_system(system_id)
        assessment = assessments[0] if assessments else None

        sections = await self._llm.generate_sections(
            ModelCardGenerationContext(system=system, assessment=assessment)
        )
        if not sections:
            raise ServiceUnavailableError(
                "Génération LLM indisponible. Vérifiez la clé OPENROUTER_API_KEY."
            )
        return sections
