from __future__ import annotations

import uuid
from typing import Annotated, Any

import structlog
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.core.dependencies import CurrentUser, ReviewerOrAbove
from app.database import DbSession
from app.models.ai_system import AISystem
from app.models.risk_assessment import RiskAssessment
from app.models.user import User
from app.schemas.risk_assessment import (
    RiskAssessmentList,
    RiskAssessmentOut,
    RiskAssessmentRequest,
)
from app.services import audit_logger
from app.services import risk_scorer as scorer

log = structlog.get_logger(__name__)

router = APIRouter(prefix="/risk", tags=["Risk Scorer"])


@router.get("/questionnaire")
async def get_questionnaire(current_user: CurrentUser) -> dict[str, Any]:
    return scorer.get_questionnaire()


@router.post(
    "/assess/{system_id}",
    response_model=RiskAssessmentOut,
    status_code=status.HTTP_201_CREATED,
)
async def assess_system(
    system_id: uuid.UUID,
    body: RiskAssessmentRequest,
    db: DbSession,
    current_user: CurrentUser,
    _reviewer: Annotated[User, ReviewerOrAbove],
) -> RiskAssessment:
    system = await db.get(AISystem, system_id)
    if not system:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Système IA introuvable")

    result = scorer.assess(body.answers)

    assessment = RiskAssessment(
        ai_system_id=system_id,
        assessed_by=current_user.id,
        questionnaire=body.answers,
        score_details=result.score_details,
        total_score=result.total_score,
        risk_category=result.risk_category,
        justification=result.justification,
        ai_act_articles=result.ai_act_articles,
        required_actions=result.required_actions,
        valid_until=result.valid_until,
    )
    db.add(assessment)

    # Mettre à jour la catégorie de risque du système
    system.current_risk_category = result.risk_category
    await db.flush()

    await audit_logger.log_action(
        db,
        actor=current_user,
        action="risk_assessment.created",
        resource_type="risk_assessment",
        resource_id=assessment.id,
        input_payload={"system_id": str(system_id), "answers_count": len(body.answers)},
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


@router.get("/assessments/{system_id}", response_model=RiskAssessmentList)
async def list_assessments(
    system_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> RiskAssessmentList:
    result = await db.execute(
        select(RiskAssessment)
        .where(RiskAssessment.ai_system_id == system_id)
        .order_by(RiskAssessment.created_at.desc())
    )
    items = list(result.scalars().all())
    return RiskAssessmentList(items=items, total=len(items))
