from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated

import structlog
from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select

from app.core.dependencies import AdminUser, ReviewerOrAbove
from app.database import DbSession
from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.audit_log import AuditLogList, AuditLogOut, HashVerifyResult

log = structlog.get_logger(__name__)

router = APIRouter(prefix="/audit", tags=["Audit Logs"])


@router.get("", response_model=AuditLogList)
async def list_audit_logs(
    db: DbSession,
    _admin: Annotated[User, AdminUser],
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    actor_id: uuid.UUID | None = Query(None),
    resource_type: str | None = Query(None),
    action: str | None = Query(None),
    from_date: datetime | None = Query(None),
    to_date: datetime | None = Query(None),
) -> AuditLogList:
    from sqlalchemy import func

    q = select(AuditLog)
    if actor_id:
        q = q.where(AuditLog.actor_id == actor_id)
    if resource_type:
        q = q.where(AuditLog.resource_type == resource_type)
    if action:
        q = q.where(AuditLog.action.ilike(f"%{action}%"))
    if from_date:
        q = q.where(AuditLog.created_at >= from_date)
    if to_date:
        q = q.where(AuditLog.created_at <= to_date)

    total_result = await db.execute(select(func.count()).select_from(q.subquery()))
    total = total_result.scalar_one()

    result = await db.execute(
        q.offset((page - 1) * per_page).limit(per_page).order_by(AuditLog.created_at.desc())
    )
    return AuditLogList(
        items=[AuditLogOut.model_validate(i) for i in result.scalars().all()], total=total
    )


@router.get("/{resource_type}/{resource_id}", response_model=AuditLogList)
async def get_resource_audit(
    resource_type: str,
    resource_id: uuid.UUID,
    db: DbSession,
    _reviewer: Annotated[User, ReviewerOrAbove],
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
) -> AuditLogList:
    from sqlalchemy import func

    q = select(AuditLog).where(
        AuditLog.resource_type == resource_type,
        AuditLog.resource_id == resource_id,
    )
    total_result = await db.execute(select(func.count()).select_from(q.subquery()))
    total = total_result.scalar_one()

    result = await db.execute(
        q.offset((page - 1) * per_page).limit(per_page).order_by(AuditLog.created_at.desc())
    )
    return AuditLogList(
        items=[AuditLogOut.model_validate(i) for i in result.scalars().all()], total=total
    )


@router.get("/entry/{log_id}/verify", response_model=HashVerifyResult)
async def verify_log_integrity(
    log_id: uuid.UUID,
    db: DbSession,
    _admin: Annotated[User, AdminUser],
) -> HashVerifyResult:
    from app.services.audit_logger import _compute_hash

    entry = await db.get(AuditLog, log_id)
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Log introuvable")

    computed = _compute_hash(
        str(entry.actor_id),
        entry.action,
        str(entry.resource_id) if entry.resource_id else "",
        entry.created_at.isoformat(),
        entry.input_payload,
    )
    is_valid = computed == entry.payload_hash

    if not is_valid:
        log.warning("audit_hash_mismatch", log_id=str(log_id))

    return HashVerifyResult(
        log_id=log_id,
        valid=is_valid,
        hash_match=is_valid,
        stored_hash=entry.payload_hash,
        computed_hash=computed,
    )
