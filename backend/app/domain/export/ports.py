from __future__ import annotations

from typing import Protocol

from app.models.ai_system import AISystem
from app.models.audit_log import AuditLog
from app.models.model_card import ModelCard
from app.models.risk_assessment import RiskAssessment


class PDFGeneratorPort(Protocol):
    def generate_compliance_report(
        self,
        system: AISystem,
        assessment: RiskAssessment | None,
        model_card: ModelCard | None,
        audit_logs: list[AuditLog],
    ) -> bytes: ...
