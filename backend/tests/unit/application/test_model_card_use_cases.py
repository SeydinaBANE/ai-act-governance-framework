from __future__ import annotations

import uuid

import pytest
from app.application.use_cases.model_card import (
    CreateModelCard,
    GenerateModelCardSections,
    ListModelCards,
    PublishModelCard,
    UpdateModelCard,
)
from app.core.exceptions import NotFoundError, ServiceUnavailableError
from app.models.model_card import ModelCardStatus

from tests.factories.ai_system_factory import AISystemFactory
from tests.factories.user_factory import UserFactory
from tests.fakes.llm import FakeLLM
from tests.fakes.repositories import (
    InMemoryAISystemRepository,
    InMemoryAuditLogRepository,
    InMemoryModelCardRepository,
    InMemoryRiskAssessmentRepository,
)


async def test_create_model_card_adds_card_and_records_audit() -> None:
    system = AISystemFactory.build()
    ai_systems = InMemoryAISystemRepository([system])
    model_cards = InMemoryModelCardRepository()
    audit_logs = InMemoryAuditLogRepository()
    actor = UserFactory.build()

    card = await CreateModelCard(model_cards, ai_systems, audit_logs).execute(
        system.id, {"model_name": "Modèle A"}, actor=actor
    )

    assert card.ai_system_id == system.id
    assert card.created_by == actor.id
    assert len(model_cards.cards) == 1
    assert audit_logs.entries[0].action == "model_card.created"


async def test_create_model_card_missing_system_raises() -> None:
    ai_systems = InMemoryAISystemRepository([])
    model_cards = InMemoryModelCardRepository()
    audit_logs = InMemoryAuditLogRepository()

    with pytest.raises(NotFoundError):
        await CreateModelCard(model_cards, ai_systems, audit_logs).execute(
            uuid.uuid4(), {"model_name": "Modèle A"}, actor=UserFactory.build()
        )


async def test_list_model_cards_returns_only_for_system() -> None:
    system = AISystemFactory.build()
    other_system = AISystemFactory.build()
    ai_systems = InMemoryAISystemRepository([system, other_system])
    model_cards = InMemoryModelCardRepository()
    audit_logs = InMemoryAuditLogRepository()
    actor = UserFactory.build()

    create = CreateModelCard(model_cards, ai_systems, audit_logs)
    await create.execute(system.id, {"model_name": "A"}, actor=actor)
    await create.execute(other_system.id, {"model_name": "B"}, actor=actor)

    items, total = await ListModelCards(model_cards).execute(system.id)

    assert total == 1
    assert items[0].ai_system_id == system.id


async def test_update_model_card_applies_fields_and_records_audit() -> None:
    system = AISystemFactory.build()
    ai_systems = InMemoryAISystemRepository([system])
    model_cards = InMemoryModelCardRepository()
    audit_logs = InMemoryAuditLogRepository()
    actor = UserFactory.build()

    card = await CreateModelCard(model_cards, ai_systems, audit_logs).execute(
        system.id, {"model_name": "Ancien nom"}, actor=actor
    )

    updated = await UpdateModelCard(model_cards, audit_logs).execute(
        card.id, {"model_name": "Nouveau nom"}, actor=actor
    )

    assert updated.model_name == "Nouveau nom"
    assert audit_logs.entries[-1].action == "model_card.updated"


async def test_update_model_card_missing_raises() -> None:
    model_cards = InMemoryModelCardRepository()
    audit_logs = InMemoryAuditLogRepository()

    with pytest.raises(NotFoundError):
        await UpdateModelCard(model_cards, audit_logs).execute(
            uuid.uuid4(), {"model_name": "x"}, actor=UserFactory.build()
        )


async def test_publish_model_card_sets_status_and_reviewer() -> None:
    system = AISystemFactory.build()
    ai_systems = InMemoryAISystemRepository([system])
    model_cards = InMemoryModelCardRepository()
    audit_logs = InMemoryAuditLogRepository()
    actor = UserFactory.build()

    card = await CreateModelCard(model_cards, ai_systems, audit_logs).execute(
        system.id, {"model_name": "A"}, actor=actor
    )

    reviewer = UserFactory.build()
    published = await PublishModelCard(model_cards, audit_logs).execute(card.id, actor=reviewer)

    assert published.status == ModelCardStatus.PUBLISHED
    assert published.reviewed_by == reviewer.id
    assert audit_logs.entries[-1].action == "model_card.published"


async def test_publish_model_card_missing_raises() -> None:
    model_cards = InMemoryModelCardRepository()
    audit_logs = InMemoryAuditLogRepository()

    with pytest.raises(NotFoundError):
        await PublishModelCard(model_cards, audit_logs).execute(
            uuid.uuid4(), actor=UserFactory.build()
        )


async def test_generate_model_card_sections_returns_llm_output() -> None:
    system = AISystemFactory.build()
    ai_systems = InMemoryAISystemRepository([system])
    risk_assessments = InMemoryRiskAssessmentRepository()
    llm = FakeLLM(sections={"limitations": "aucune"})

    result = await GenerateModelCardSections(ai_systems, risk_assessments, llm).execute(system.id)

    assert result == {"limitations": "aucune"}
    assert llm.calls[0].system.id == system.id
    assert llm.calls[0].assessment is None


async def test_generate_model_card_sections_missing_system_raises() -> None:
    ai_systems = InMemoryAISystemRepository([])
    risk_assessments = InMemoryRiskAssessmentRepository()
    llm = FakeLLM(sections={"limitations": "aucune"})

    with pytest.raises(NotFoundError):
        await GenerateModelCardSections(ai_systems, risk_assessments, llm).execute(uuid.uuid4())


async def test_generate_model_card_sections_empty_llm_output_raises() -> None:
    system = AISystemFactory.build()
    ai_systems = InMemoryAISystemRepository([system])
    risk_assessments = InMemoryRiskAssessmentRepository()
    llm = FakeLLM(sections={})

    with pytest.raises(ServiceUnavailableError):
        await GenerateModelCardSections(ai_systems, risk_assessments, llm).execute(system.id)
