from __future__ import annotations

import uuid

import structlog

from app.core.exceptions import NotFoundError
from app.domain.audit_log.ports import AuditLogPort
from app.domain.pii_scan.ports import PIIScannerPort, PIIScanRepository, PIIScanResult
from app.models.pii_scan import PIIScan, PIIScanRiskLevel, ScanSourceType
from app.models.user import User

log = structlog.get_logger(__name__)


def _build_scan(
    result: PIIScanResult,
    *,
    source_type: ScanSourceType,
    source_name: str | None,
    ai_system_id: uuid.UUID | None,
    scanned_by: uuid.UUID,
    confidence_threshold: float,
) -> PIIScan:
    return PIIScan(
        ai_system_id=ai_system_id,
        scanned_by=scanned_by,
        source_type=source_type,
        source_name=source_name,
        source_hash=result.source_hash,
        total_items=result.total_items,
        pii_found=result.pii_found,
        findings=result.findings,
        entity_summary=result.entity_summary,
        confidence_threshold=confidence_threshold,
        risk_level=PIIScanRiskLevel(result.risk_level),
        recommendations=result.recommendations,
    )


class ScanText:
    def __init__(
        self,
        pii_scans: PIIScanRepository,
        scanner: PIIScannerPort,
        audit_logs: AuditLogPort,
    ) -> None:
        self._pii_scans = pii_scans
        self._scanner = scanner
        self._audit_logs = audit_logs

    async def execute(
        self,
        text: str,
        *,
        ai_system_id: uuid.UUID | None,
        confidence_threshold: float,
        actor: User,
        ip_address: str | None = None,
    ) -> PIIScan:
        result = await self._scanner.scan_text(text, confidence_threshold=confidence_threshold)
        scan = _build_scan(
            result,
            source_type=ScanSourceType.TEXT,
            source_name=None,
            ai_system_id=ai_system_id,
            scanned_by=actor.id,
            confidence_threshold=confidence_threshold,
        )
        await self._pii_scans.add(scan)

        await self._audit_logs.record(
            actor=actor,
            action="pii_scan.created",
            resource_type="pii_scan",
            resource_id=scan.id,
            input_payload={"source_type": "text", "text_length": len(text)},
            output_summary={"pii_found": result.pii_found, "entity_summary": result.entity_summary},
            ip_address=ip_address,
        )
        return scan


class ScanFile:
    def __init__(
        self,
        pii_scans: PIIScanRepository,
        scanner: PIIScannerPort,
        audit_logs: AuditLogPort,
    ) -> None:
        self._pii_scans = pii_scans
        self._scanner = scanner
        self._audit_logs = audit_logs

    async def execute(
        self,
        content: bytes,
        filename: str,
        *,
        ai_system_id: uuid.UUID | None,
        confidence_threshold: float,
        actor: User,
        ip_address: str | None = None,
    ) -> PIIScan:
        result = await self._scanner.scan_file(
            content, filename, confidence_threshold=confidence_threshold
        )
        scan = _build_scan(
            result,
            source_type=ScanSourceType.FILE,
            source_name=filename,
            ai_system_id=ai_system_id,
            scanned_by=actor.id,
            confidence_threshold=confidence_threshold,
        )
        await self._pii_scans.add(scan)

        await self._audit_logs.record(
            actor=actor,
            action="pii_scan.created",
            resource_type="pii_scan",
            resource_id=scan.id,
            input_payload={
                "source_type": "file",
                "filename": filename,
                "size_bytes": len(content),
            },
            output_summary={"pii_found": result.pii_found, "entity_summary": result.entity_summary},
            ip_address=ip_address,
        )
        return scan


class ListPIIScans:
    def __init__(self, pii_scans: PIIScanRepository) -> None:
        self._pii_scans = pii_scans

    async def execute(
        self, user_id: uuid.UUID, *, page: int, per_page: int
    ) -> tuple[list[PIIScan], int]:
        return await self._pii_scans.list_by_user(user_id, page=page, per_page=per_page)


class GetPIIScan:
    def __init__(self, pii_scans: PIIScanRepository) -> None:
        self._pii_scans = pii_scans

    async def execute(self, scan_id: uuid.UUID) -> PIIScan:
        scan = await self._pii_scans.get(scan_id)
        if scan is None:
            raise NotFoundError("Scan", str(scan_id))
        return scan
