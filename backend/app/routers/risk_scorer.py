from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, status

from app.composition import AssessRiskDep, GetQuestionnaireDep, ListRiskAssessmentsDep
from app.core.dependencies import CurrentUser, ReviewerOrAbove
from app.models.risk_assessment import RiskAssessment
from app.models.user import User
from app.schemas.risk_assessment import (
    RiskAssessmentList,
    RiskAssessmentOut,
    RiskAssessmentRequest,
)

router = APIRouter(prefix="/risk", tags=["Risk Scorer"])


@router.get("/questionnaire")
async def get_questionnaire(
    current_user: CurrentUser, use_case: GetQuestionnaireDep
) -> dict[str, Any]:
    return await use_case.execute()


@router.post(
    "/assess/{system_id}",
    response_model=RiskAssessmentOut,
    status_code=status.HTTP_201_CREATED,
)
async def assess_system(
    system_id: uuid.UUID,
    body: RiskAssessmentRequest,
    current_user: CurrentUser,
    _reviewer: Annotated[User, ReviewerOrAbove],
    use_case: AssessRiskDep,
) -> RiskAssessment:
    return await use_case.execute(system_id, body.answers, actor=current_user)


@router.get("/assessments/{system_id}", response_model=RiskAssessmentList)
async def list_assessments(
    system_id: uuid.UUID,
    current_user: CurrentUser,
    use_case: ListRiskAssessmentsDep,
) -> RiskAssessmentList:
    items, total = await use_case.execute(system_id)
    return RiskAssessmentList(
        items=[RiskAssessmentOut.model_validate(i) for i in items], total=total
    )
