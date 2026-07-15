from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Query

from app.composition import GetResourceAuditLogsDep, ListAuditLogsDep, VerifyAuditLogIntegrityDep
from app.core.dependencies import AdminUser, ReviewerOrAbove
from app.models.user import User
from app.schemas.audit_log import AuditLogList, AuditLogOut, HashVerifyResult

router = APIRouter(prefix="/audit", tags=["Audit Logs"])


@router.get("", response_model=AuditLogList)
async def list_audit_logs(
    use_case: ListAuditLogsDep,
    _admin: Annotated[User, AdminUser],
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    actor_id: uuid.UUID | None = Query(None),
    resource_type: str | None = Query(None),
    action: str | None = Query(None),
    from_date: datetime | None = Query(None),
    to_date: datetime | None = Query(None),
) -> AuditLogList:
    items, total = await use_case.execute(
        page=page,
        per_page=per_page,
        actor_id=actor_id,
        resource_type=resource_type,
        action=action,
        from_date=from_date,
        to_date=to_date,
    )
    return AuditLogList(items=[AuditLogOut.model_validate(i) for i in items], total=total)


@router.get("/{resource_type}/{resource_id}", response_model=AuditLogList)
async def get_resource_audit(
    resource_type: str,
    resource_id: uuid.UUID,
    use_case: GetResourceAuditLogsDep,
    _reviewer: Annotated[User, ReviewerOrAbove],
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
) -> AuditLogList:
    items, total = await use_case.execute(resource_type, resource_id, page=page, per_page=per_page)
    return AuditLogList(items=[AuditLogOut.model_validate(i) for i in items], total=total)


@router.get("/entry/{log_id}/verify", response_model=HashVerifyResult)
async def verify_log_integrity(
    log_id: uuid.UUID,
    use_case: VerifyAuditLogIntegrityDep,
    _admin: Annotated[User, AdminUser],
) -> HashVerifyResult:
    result = await use_case.execute(log_id)
    return HashVerifyResult(
        log_id=result.log_id,
        valid=result.valid,
        hash_match=result.valid,
        stored_hash=result.stored_hash,
        computed_hash=result.computed_hash,
    )
