from __future__ import annotations

import uuid

import pytest
from app.application.use_cases.pii_scan import GetPIIScan, ListPIIScans, ScanFile, ScanText
from app.core.exceptions import NotFoundError
from app.models.pii_scan import PIIScanRiskLevel, ScanSourceType

from tests.factories.user_factory import UserFactory
from tests.fakes.pii_scanner import FakePIIScanner
from tests.fakes.repositories import InMemoryAuditLogRepository, InMemoryPIIScanRepository


async def test_scan_text_persists_scan_and_records_audit() -> None:
    pii_scans = InMemoryPIIScanRepository()
    scanner = FakePIIScanner(findings=[{"entity_type": "EMAIL_ADDRESS"}])
    audit_logs = InMemoryAuditLogRepository()
    actor = UserFactory.build()

    scan = await ScanText(pii_scans, scanner, audit_logs).execute(
        "contact: a@b.com",
        ai_system_id=None,
        confidence_threshold=0.85,
        actor=actor,
    )

    assert scan.source_type == ScanSourceType.TEXT
    assert scan.pii_found is True
    assert scan.risk_level == PIIScanRiskLevel.LOW
    assert len(pii_scans.scans) == 1
    assert audit_logs.entries[0].action == "pii_scan.created"


async def test_scan_text_no_findings_marks_not_found() -> None:
    pii_scans = InMemoryPIIScanRepository()
    scanner = FakePIIScanner(findings=[])
    audit_logs = InMemoryAuditLogRepository()

    scan = await ScanText(pii_scans, scanner, audit_logs).execute(
        "rien à signaler",
        ai_system_id=None,
        confidence_threshold=0.85,
        actor=UserFactory.build(),
    )

    assert scan.pii_found is False
    assert scan.risk_level == PIIScanRiskLevel.NONE


async def test_scan_file_persists_scan_with_filename() -> None:
    pii_scans = InMemoryPIIScanRepository()
    scanner = FakePIIScanner(findings=[{"entity_type": "PERSON"}])
    audit_logs = InMemoryAuditLogRepository()
    actor = UserFactory.build()

    scan = await ScanFile(pii_scans, scanner, audit_logs).execute(
        b"Jean Dupont",
        "clients.txt",
        ai_system_id=None,
        confidence_threshold=0.85,
        actor=actor,
    )

    assert scan.source_type == ScanSourceType.FILE
    assert scan.source_name == "clients.txt"
    assert audit_logs.entries[0].input_payload == {
        "source_type": "file",
        "filename": "clients.txt",
        "size_bytes": 11,
    }


async def test_list_pii_scans_filters_by_user() -> None:
    pii_scans = InMemoryPIIScanRepository()
    scanner = FakePIIScanner()
    audit_logs = InMemoryAuditLogRepository()
    actor = UserFactory.build()
    other = UserFactory.build()

    scan_use_case = ScanText(pii_scans, scanner, audit_logs)
    await scan_use_case.execute("a", ai_system_id=None, confidence_threshold=0.85, actor=actor)
    await scan_use_case.execute("b", ai_system_id=None, confidence_threshold=0.85, actor=other)

    items, total = await ListPIIScans(pii_scans).execute(actor.id, page=1, per_page=10)

    assert total == 1
    assert items[0].scanned_by == actor.id


async def test_get_pii_scan_missing_raises() -> None:
    pii_scans = InMemoryPIIScanRepository()

    with pytest.raises(NotFoundError):
        await GetPIIScan(pii_scans).execute(uuid.uuid4())
