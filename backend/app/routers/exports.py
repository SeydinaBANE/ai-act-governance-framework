from __future__ import annotations

import uuid

import structlog
from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import Response
from sqlalchemy import select

from app.core.dependencies import CurrentUser
from app.core.rate_limiter import limiter
from app.database import DbSession
from app.models.ai_system import AISystem
from app.models.audit_log import AuditLog
from app.models.model_card import ModelCard
from app.models.risk_assessment import RiskAssessment
from app.services import pdf_exporter

log = structlog.get_logger(__name__)

router = APIRouter(prefix="/exports", tags=["Exports"])


@router.get("/compliance-report/{system_id}")
@limiter.limit("10/minute")
async def export_compliance_report(
    request: Request,
    system_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> Response:
    system = await db.get(AISystem, system_id)
    if not system:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Système IA introuvable")

    assessment_result = await db.execute(
        select(RiskAssessment)
        .where(RiskAssessment.ai_system_id == system_id)
        .order_by(RiskAssessment.created_at.desc())
        .limit(1)
    )
    assessment = assessment_result.scalar_one_or_none()

    card_result = await db.execute(
        select(ModelCard)
        .where(ModelCard.ai_system_id == system_id)
        .order_by(ModelCard.created_at.desc())
        .limit(1)
    )
    model_card = card_result.scalar_one_or_none()

    audit_result = await db.execute(
        select(AuditLog)
        .where(AuditLog.resource_id == system_id)
        .order_by(AuditLog.created_at.desc())
        .limit(10)
    )
    audit_logs = list(audit_result.scalars().all())

    pdf_bytes = pdf_exporter.generate_compliance_report(system, assessment, model_card, audit_logs)

    safe_name = system.name.replace(" ", "_").replace("/", "_")
    filename = f"conformite_aiact_{safe_name}.pdf"

    log.info("compliance_report_exported", system_id=str(system_id), user_id=str(current_user.id))

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
