from __future__ import annotations

import uuid

import pytest
from app.application.use_cases.risk_assessment import (
    AssessRisk,
    GetQuestionnaire,
    ListRiskAssessments,
)
from app.core.exceptions import NotFoundError
from app.models.ai_system import RiskCategory

from tests.factories.ai_system_factory import AISystemFactory
from tests.factories.user_factory import UserFactory
from tests.fakes.repositories import (
    InMemoryAISystemRepository,
    InMemoryAuditLogRepository,
    InMemoryRiskAssessmentRepository,
)


async def test_get_questionnaire_returns_sections() -> None:
    questionnaire = await GetQuestionnaire().execute()

    assert "sections" in questionnaire
    assert len(questionnaire["sections"]) > 0


async def test_assess_risk_updates_system_category_and_records_audit() -> None:
    system = AISystemFactory.build()
    ai_systems = InMemoryAISystemRepository([system])
    risk_assessments = InMemoryRiskAssessmentRepository()
    audit_logs = InMemoryAuditLogRepository()
    actor = UserFactory.build()

    use_case = AssessRisk(ai_systems, risk_assessments, audit_logs)
    assessment = await use_case.execute(
        system.id, {"q1_biometric_realtime": True}, actor=actor
    )

    assert assessment.risk_category == RiskCategory.PROHIBITED
    assert system.current_risk_category == RiskCategory.PROHIBITED
    assert len(risk_assessments.assessments) == 1
    assert len(audit_logs.entries) == 1
    assert audit_logs.entries[0].action == "risk_assessment.created"


async def test_assess_risk_missing_system_raises() -> None:
    ai_systems = InMemoryAISystemRepository([])
    risk_assessments = InMemoryRiskAssessmentRepository()
    audit_logs = InMemoryAuditLogRepository()
    actor = UserFactory.build()

    use_case = AssessRisk(ai_systems, risk_assessments, audit_logs)

    with pytest.raises(NotFoundError):
        await use_case.execute(uuid.uuid4(), {}, actor=actor)


async def test_list_risk_assessments_returns_only_for_system() -> None:
    system = AISystemFactory.build()
    other_system = AISystemFactory.build()
    ai_systems = InMemoryAISystemRepository([system, other_system])
    risk_assessments = InMemoryRiskAssessmentRepository()
    audit_logs = InMemoryAuditLogRepository()
    actor = UserFactory.build()

    assess = AssessRisk(ai_systems, risk_assessments, audit_logs)
    await assess.execute(system.id, {}, actor=actor)
    await assess.execute(other_system.id, {}, actor=actor)

    items, total = await ListRiskAssessments(risk_assessments).execute(system.id)

    assert total == 1
    assert items[0].ai_system_id == system.id
