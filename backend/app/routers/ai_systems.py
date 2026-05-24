from __future__ import annotations

import uuid
from typing import Annotated

import structlog
from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select

from app.core.dependencies import CurrentUser, ReviewerOrAbove
from app.database import DbSession
from app.models.ai_system import AISystem, RiskCategory, SystemStatus
from app.models.user import User
from app.schemas.ai_system import AISystemCreate, AISystemList, AISystemOut, AISystemUpdate
from app.services import audit_logger

log = structlog.get_logger(__name__)

router = APIRouter(prefix="/systems", tags=["AI Systems"])


@router.get("", response_model=AISystemList)
async def list_systems(
    db: DbSession,
    current_user: CurrentUser,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status_filter: SystemStatus | None = Query(None, alias="status"),
    risk_category: RiskCategory | None = Query(None),
    search: str | None = Query(None),
) -> AISystemList:
    q = select(AISystem)
    if status_filter:
        q = q.where(AISystem.status == status_filter)
    if risk_category:
        q = q.where(AISystem.current_risk_category == risk_category)
    if search:
        q = q.where(AISystem.name.ilike(f"%{search}%"))

    total_result = await db.execute(select(func.count()).select_from(q.subquery()))
    total = total_result.scalar_one()

    q = q.offset((page - 1) * per_page).limit(per_page).order_by(AISystem.created_at.desc())
    result = await db.execute(q)
    items = list(result.scalars().all())

    return AISystemList(items=items, total=total, page=page, per_page=per_page)


@router.post("", response_model=AISystemOut, status_code=status.HTTP_201_CREATED)
async def create_system(
    body: AISystemCreate,
    db: DbSession,
    current_user: CurrentUser,
    _reviewer: Annotated[User, ReviewerOrAbove],
) -> AISystem:
    system = AISystem(**body.model_dump(), created_by=current_user.id)
    db.add(system)
    await db.flush()

    await audit_logger.log_action(
        db,
        actor=current_user,
        action="ai_system.created",
        resource_type="ai_system",
        resource_id=system.id,
        input_payload=body.model_dump(),
        output_summary={"system_id": str(system.id)},
    )

    log.info("system_created", system_id=str(system.id), name=system.name)
    return system


@router.get("/{system_id}", response_model=AISystemOut)
async def get_system(
    system_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> AISystem:
    system = await db.get(AISystem, system_id)
    if not system:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Système IA introuvable")
    return system


@router.patch("/{system_id}", response_model=AISystemOut)
async def update_system(
    system_id: uuid.UUID,
    body: AISystemUpdate,
    db: DbSession,
    current_user: CurrentUser,
    _reviewer: Annotated[User, ReviewerOrAbove],
) -> AISystem:
    system = await db.get(AISystem, system_id)
    if not system:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Système IA introuvable")

    update_data = body.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(system, field, value)

    await db.flush()
    await audit_logger.log_action(
        db,
        actor=current_user,
        action="ai_system.updated",
        resource_type="ai_system",
        resource_id=system_id,
        input_payload=update_data,
    )
    return system


@router.delete("/{system_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def delete_system(
    system_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> None:
    from app.core.exceptions import ForbiddenError
    from app.models.user import UserRole

    if current_user.role != UserRole.ADMIN:
        raise ForbiddenError("supprimer un système IA")

    system = await db.get(AISystem, system_id)
    if not system:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Système IA introuvable")

    await db.delete(system)
    await audit_logger.log_action(
        db,
        actor=current_user,
        action="ai_system.deleted",
        resource_type="ai_system",
        resource_id=system_id,
        output_summary={"name": system.name},
    )
    log.info("system_deleted", system_id=str(system_id))
