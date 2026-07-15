from __future__ import annotations

from typing import Any

from app.domain.pii_scan import rules
from app.domain.pii_scan.ports import PIIScanResult


class FakePIIScanner:
    def __init__(self, findings: list[dict[str, Any]] | None = None) -> None:
        self.findings = findings or []
        self.text_calls: list[str] = []
        self.file_calls: list[tuple[bytes, str]] = []

    async def scan_text(
        self, text: str, *, language: str = "fr", confidence_threshold: float = 0.85
    ) -> PIIScanResult:
        self.text_calls.append(text)
        return rules.build_scan_result(text, self.findings, total_items=len(text.split()))

    async def scan_file(
        self, content: bytes, filename: str, *, confidence_threshold: float = 0.85
    ) -> PIIScanResult:
        self.file_calls.append((content, filename))
        text = content.decode(errors="replace")
        return rules.build_scan_result(content, self.findings, total_items=len(text.split()))
