from __future__ import annotations

import uuid
from typing import Any

import structlog

from app.core.exceptions import NotFoundError
from app.domain.ai_system.ports import AISystemRepository
from app.domain.audit_log.ports import AuditLogPort
from app.domain.risk_assessment import rules
from app.domain.risk_assessment.ports import RiskAssessmentRepository
from app.models.risk_assessment import RiskAssessment
from app.models.user import User

log = structlog.get_logger(__name__)


class GetQuestionnaire:
    async def execute(self) -> dict[str, Any]:
        return rules.get_questionnaire()


class AssessRisk:
    def __init__(
        self,
        ai_systems: AISystemRepository,
        risk_assessments: RiskAssessmentRepository,
        audit_logs: AuditLogPort,
    ) -> None:
        self._ai_systems = ai_systems
        self._risk_assessments = risk_assessments
        self._audit_logs = audit_logs

    async def execute(
        self,
        system_id: uuid.UUID,
        answers: dict[str, bool],
        *,
        actor: User,
    ) -> RiskAssessment:
        system = await self._ai_systems.get(system_id)
        if system is None:
            raise NotFoundError("Système IA", str(system_id))

        result = rules.assess(answers)

        assessment = RiskAssessment(
            ai_system_id=system_id,
            assessed_by=actor.id,
            questionnaire=answers,
            score_details=result.score_details,
            total_score=result.total_score,
            risk_category=result.risk_category,
            justification=result.justification,
            ai_act_articles=result.ai_act_articles,
            required_actions=result.required_actions,
            valid_until=result.valid_until,
        )
        await self._risk_assessments.add(assessment)

        system.current_risk_category = result.risk_category

        await self._audit_logs.record(
            actor=actor,
            action="risk_assessment.created",
            resource_type="risk_assessment",
            resource_id=assessment.id,
            input_payload={"system_id": str(system_id), "answers_count": len(answers)},
            output_summary={
                "risk_category": result.risk_category.value,
                "total_score": result.total_score,
            },
        )

        log.info(
            "risk_assessed",
            system_id=str(system_id),
            category=result.risk_category.value,
            score=result.total_score,
        )
        return assessment


class ListRiskAssessments:
    def __init__(self, risk_assessments: RiskAssessmentRepository) -> None:
        self._risk_assessments = risk_assessments

    async def execute(self, system_id: uuid.UUID) -> tuple[list[RiskAssessment], int]:
        items = await self._risk_assessments.list_by_system(system_id)
        return items, len(items)
