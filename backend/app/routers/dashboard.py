from __future__ import annotations

from typing import Any

import structlog
from fastapi import APIRouter
from sqlalchemy import func, select

from app.core.dependencies import CurrentUser
from app.database import DbSession
from app.models.ai_system import AISystem, RiskCategory, SystemStatus
from app.models.risk_assessment import RiskAssessment

log = structlog.get_logger(__name__)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary")
async def get_summary(db: DbSession, current_user: CurrentUser) -> dict[str, Any]:
    total_result = await db.execute(select(func.count(AISystem.id)))
    total = total_result.scalar_one()

    compliant_result = await db.execute(
        select(func.count(AISystem.id)).where(AISystem.status == SystemStatus.COMPLIANT)
    )
    compliant = compliant_result.scalar_one()

    under_review_result = await db.execute(
        select(func.count(AISystem.id)).where(AISystem.status == SystemStatus.UNDER_REVIEW)
    )
    under_review = under_review_result.scalar_one()

    non_compliant_result = await db.execute(
        select(func.count(AISystem.id)).where(AISystem.status == SystemStatus.NON_COMPLIANT)
    )
    non_compliant = non_compliant_result.scalar_one()

    risk_dist: dict[str, int] = {}
    for category in RiskCategory:
        count_result = await db.execute(
            select(func.count(AISystem.id)).where(AISystem.current_risk_category == category)
        )
        risk_dist[category.value] = count_result.scalar_one()

    return {
        "total_systems": total,
        "compliant": compliant,
        "under_review": under_review,
        "non_compliant": non_compliant,
        "not_assessed": total - sum(risk_dist.values()),
        "risk_distribution": risk_dist,
        "compliance_rate": round((compliant / total * 100) if total > 0 else 0, 1),
    }


@router.get("/systems-at-risk")
async def get_systems_at_risk(db: DbSession, current_user: CurrentUser) -> dict[str, Any]:
    result = await db.execute(
        select(AISystem)
        .where(
            AISystem.current_risk_category.in_([RiskCategory.HIGH_RISK, RiskCategory.PROHIBITED]),
            AISystem.status != SystemStatus.COMPLIANT,
        )
        .order_by(AISystem.current_risk_category.asc(), AISystem.updated_at.desc())
        .limit(50)
    )
    systems = result.scalars().all()

    return {
        "systems": [
            {
                "id": str(s.id),
                "name": s.name,
                "risk_category": s.current_risk_category.value if s.current_risk_category else None,
                "status": s.status.value,
                "owner_team": s.owner_team,
            }
            for s in systems
        ],
        "total": len(systems),
    }


@router.get("/actions-required")
async def get_actions_required(db: DbSession, current_user: CurrentUser) -> dict[str, Any]:
    result = await db.execute(
        select(RiskAssessment)
        .join(AISystem, RiskAssessment.ai_system_id == AISystem.id)
        .where(
            RiskAssessment.required_actions.isnot(None),
            AISystem.status != SystemStatus.COMPLIANT,
        )
        .order_by(RiskAssessment.created_at.desc())
        .limit(20)
    )
    assessments = result.scalars().all()

    actions = []
    for assessment in assessments:
        for action in assessment.required_actions or []:
            actions.append(
                {
                    "assessment_id": str(assessment.id),
                    "system_id": str(assessment.ai_system_id),
                    "article": action.get("article"),
                    "obligation": action.get("obligation"),
                    "deadline": action.get("deadline"),
                    "risk_category": assessment.risk_category,
                }
            )

    return {"actions": actions, "total": len(actions)}
