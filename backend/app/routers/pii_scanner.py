import uuid
from typing import Annotated

import structlog
from fastapi import APIRouter, File, HTTPException, Query, Request, UploadFile, status

from app.composition import GetPIIScanDep, ListPIIScansDep, ScanFileDep, ScanTextDep
from app.config import settings
from app.core.dependencies import CurrentUser, ReviewerOrAbove
from app.core.rate_limiter import limiter
from app.models.pii_scan import PIIScan
from app.models.user import User
from app.schemas.pii_scan import PIIScanList, PIIScanOut, PIIScanTextRequest

log = structlog.get_logger(__name__)

router = APIRouter(prefix="/pii", tags=["PII Scanner"])

_MAX_BYTES = settings.max_upload_size_mb * 1024 * 1024


@router.post("/scan/text", response_model=PIIScanOut, status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
async def scan_text(
    body: PIIScanTextRequest,
    current_user: CurrentUser,
    request: Request,
    _reviewer: Annotated[User, ReviewerOrAbove],
    use_case: ScanTextDep,
) -> PIIScan:
    return await use_case.execute(
        body.text,
        ai_system_id=body.ai_system_id,
        confidence_threshold=body.confidence_threshold,
        actor=current_user,
        ip_address=request.client.host if request.client else None,
    )


@router.post("/scan/file", response_model=PIIScanOut, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def scan_file(
    file: Annotated[UploadFile, File()],
    current_user: CurrentUser,
    request: Request,
    _reviewer: Annotated[User, ReviewerOrAbove],
    use_case: ScanFileDep,
    ai_system_id: uuid.UUID | None = Query(None),
    confidence_threshold: float = Query(0.85, ge=0.0, le=1.0),
) -> PIIScan:
    content = await file.read()
    if len(content) > _MAX_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Fichier trop volumineux. Maximum : {settings.max_upload_size_mb} MB",
        )

    filename = file.filename or "upload"
    allowed_types = {"text/plain", "text/csv", "application/json", "application/csv"}
    if file.content_type and file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Format non supporté. Formats acceptés : TXT, CSV, JSON",
        )

    return await use_case.execute(
        content,
        filename,
        ai_system_id=ai_system_id,
        confidence_threshold=confidence_threshold,
        actor=current_user,
        ip_address=request.client.host if request.client else None,
    )


@router.get("/scans", response_model=PIIScanList)
async def list_scans(
    current_user: CurrentUser,
    use_case: ListPIIScansDep,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
) -> PIIScanList:
    items, total = await use_case.execute(current_user.id, page=page, per_page=per_page)
    return PIIScanList(items=[PIIScanOut.model_validate(i) for i in items], total=total)


@router.get("/scans/{scan_id}", response_model=PIIScanOut)
async def get_scan(
    scan_id: uuid.UUID,
    current_user: CurrentUser,
    use_case: GetPIIScanDep,
) -> PIIScan:
    return await use_case.execute(scan_id)
