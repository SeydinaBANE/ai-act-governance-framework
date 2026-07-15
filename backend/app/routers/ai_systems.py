from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Query, status

from app.composition import (
    CreateAISystemDep,
    DeleteAISystemDep,
    GetAISystemDep,
    ListAISystemsDep,
    UpdateAISystemDep,
)
from app.core.dependencies import AdminUser, CurrentUser, ReviewerOrAbove
from app.models.ai_system import AISystem, RiskCategory, SystemStatus
from app.models.user import User
from app.schemas.ai_system import AISystemCreate, AISystemList, AISystemOut, AISystemUpdate

router = APIRouter(prefix="/systems", tags=["AI Systems"])


@router.get("", response_model=AISystemList)
async def list_systems(
    current_user: CurrentUser,
    use_case: ListAISystemsDep,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status_filter: SystemStatus | None = Query(None, alias="status"),
    risk_category: RiskCategory | None = Query(None),
    search: str | None = Query(None),
) -> AISystemList:
    items, total = await use_case.execute(
        page=page,
        per_page=per_page,
        status=status_filter,
        risk_category=risk_category,
        search=search,
    )
    return AISystemList(
        items=[AISystemOut.model_validate(i) for i in items],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.post("", response_model=AISystemOut, status_code=status.HTTP_201_CREATED)
async def create_system(
    body: AISystemCreate,
    current_user: CurrentUser,
    _reviewer: Annotated[User, ReviewerOrAbove],
    use_case: CreateAISystemDep,
) -> AISystem:
    return await use_case.execute(body.model_dump(), actor=current_user)


@router.get("/{system_id}", response_model=AISystemOut)
async def get_system(
    system_id: uuid.UUID,
    current_user: CurrentUser,
    use_case: GetAISystemDep,
) -> AISystem:
    return await use_case.execute(system_id)


@router.patch("/{system_id}", response_model=AISystemOut)
async def update_system(
    system_id: uuid.UUID,
    body: AISystemUpdate,
    current_user: CurrentUser,
    _reviewer: Annotated[User, ReviewerOrAbove],
    use_case: UpdateAISystemDep,
) -> AISystem:
    return await use_case.execute(system_id, body.model_dump(exclude_none=True), actor=current_user)


@router.delete("/{system_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def delete_system(
    system_id: uuid.UUID,
    current_user: CurrentUser,
    _admin: Annotated[User, AdminUser],
    use_case: DeleteAISystemDep,
) -> None:
    await use_case.execute(system_id, actor=current_user)
