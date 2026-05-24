from __future__ import annotations

import uuid
from typing import Annotated

import structlog
from fastapi import APIRouter, HTTPException, Query, Request, UploadFile, status
from sqlalchemy import select

from app.config import settings
from app.core.dependencies import CurrentUser, ReviewerOrAbove
from app.database import DbSession
from app.models.pii_scan import PIIScan, ScanSourceType
from app.models.user import User
from app.schemas.pii_scan import PIIScanList, PIIScanOut, PIIScanTextRequest
from app.services import audit_logger
from app.services import pii_scanner as scanner_svc

log = structlog.get_logger(__name__)

router = APIRouter(prefix="/pii", tags=["PII Scanner"])

_MAX_BYTES = settings.max_upload_size_mb * 1024 * 1024


@router.post("/scan/text", response_model=PIIScanOut, status_code=status.HTTP_201_CREATED)
async def scan_text(
    body: PIIScanTextRequest,
    db: DbSession,
    current_user: CurrentUser,
    request: Request,
    _reviewer: Annotated[User, ReviewerOrAbove],
) -> PIIScan:
    import httpx

    async with httpx.AsyncClient() as client:
        result = await scanner_svc.scan_text(
            client, body.text, confidence_threshold=body.confidence_threshold
        )

    scan = PIIScan(
        ai_system_id=body.ai_system_id,
        scanned_by=current_user.id,
        source_type=ScanSourceType.TEXT,
        source_hash=result["source_hash"],
        total_items=result["total_items"],
        pii_found=result["pii_found"],
        findings=result["findings"],
        entity_summary=result["entity_summary"],
        confidence_threshold=body.confidence_threshold,
        risk_level=result["risk_level"],
        recommendations=result["recommendations"],
    )
    db.add(scan)
    await db.flush()

    await audit_logger.log_action(
        db,
        actor=current_user,
        action="pii_scan.created",
        resource_type="pii_scan",
        resource_id=scan.id,
        input_payload={"source_type": "text", "text_length": len(body.text)},
        output_summary={"pii_found": result["pii_found"], "entity_summary": result["entity_summary"]},
        ip_address=request.client.host if request.client else None,
    )

    return scan


@router.post("/scan/file", response_model=PIIScanOut, status_code=status.HTTP_201_CREATED)
async def scan_file(
    file: UploadFile,
    db: DbSession,
    current_user: CurrentUser,
    request: Request,
    _reviewer: Annotated[User, ReviewerOrAbove],
    ai_system_id: uuid.UUID | None = Query(None),
    confidence_threshold: float = Query(0.85, ge=0.0, le=1.0),
) -> PIIScan:
    import httpx

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

    async with httpx.AsyncClient() as client:
        result = await scanner_svc.scan_file_content(
            client, content, filename, confidence_threshold=confidence_threshold
        )

    scan = PIIScan(
        ai_system_id=ai_system_id,
        scanned_by=current_user.id,
        source_type=ScanSourceType.FILE,
        source_name=filename,
        source_hash=result["source_hash"],
        total_items=result["total_items"],
        pii_found=result["pii_found"],
        findings=result["findings"],
        entity_summary=result["entity_summary"],
        confidence_threshold=confidence_threshold,
        risk_level=result["risk_level"],
        recommendations=result["recommendations"],
    )
    db.add(scan)
    await db.flush()

    await audit_logger.log_action(
        db,
        actor=current_user,
        action="pii_scan.created",
        resource_type="pii_scan",
        resource_id=scan.id,
        input_payload={"source_type": "file", "filename": filename, "size_bytes": len(content)},
        output_summary={"pii_found": result["pii_found"], "entity_summary": result["entity_summary"]},
        ip_address=request.client.host if request.client else None,
    )

    return scan


@router.get("/scans", response_model=PIIScanList)
async def list_scans(
    db: DbSession,
    current_user: CurrentUser,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
) -> PIIScanList:
    from sqlalchemy import func

    q = select(PIIScan).where(PIIScan.scanned_by == current_user.id)
    total_result = await db.execute(select(func.count()).select_from(q.subquery()))
    total = total_result.scalar_one()

    result = await db.execute(
        q.offset((page - 1) * per_page).limit(per_page).order_by(PIIScan.created_at.desc())
    )
    return PIIScanList(items=list(result.scalars().all()), total=total)


@router.get("/scans/{scan_id}", response_model=PIIScanOut)
async def get_scan(
    scan_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> PIIScan:
    scan = await db.get(PIIScan, scan_id)
    if not scan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan introuvable")
    return scan
