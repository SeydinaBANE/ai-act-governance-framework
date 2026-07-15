from __future__ import annotations

from typing import Any

import httpx
import structlog

from app.config import settings
from app.domain.pii_scan import rules
from app.domain.pii_scan.ports import PIIScanResult

log = structlog.get_logger(__name__)

_CHUNK_SIZE = 5000


class PresidioPIIScanner:
    async def scan_text(
        self, text: str, *, language: str = "fr", confidence_threshold: float = 0.85
    ) -> PIIScanResult:
        findings = await self._analyze(
            text, language=language, confidence_threshold=confidence_threshold
        )
        return rules.build_scan_result(text, findings, total_items=len(text.split()))

    async def scan_file(
        self, content: bytes, filename: str, *, confidence_threshold: float = 0.85
    ) -> PIIScanResult:
        text = content.decode(errors="replace")
        chunks = [text[i : i + _CHUNK_SIZE] for i in range(0, len(text), _CHUNK_SIZE)]

        all_findings: list[dict[str, Any]] = []
        offset = 0
        for chunk in chunks:
            findings = await self._analyze(
                chunk, language="fr", confidence_threshold=confidence_threshold
            )
            for finding in findings:
                adjusted = dict(finding)
                adjusted["start"] = finding.get("start", 0) + offset
                adjusted["end"] = finding.get("end", 0) + offset
                all_findings.append(adjusted)
            offset += len(chunk)

        return rules.build_scan_result(content, all_findings, total_items=len(text.split()))

    async def _analyze(
        self, text: str, *, language: str, confidence_threshold: float
    ) -> list[dict[str, Any]]:
        payload = {
            "text": text,
            "language": language,
            "score_threshold": confidence_threshold,
        }
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{settings.presidio_analyzer_url}/analyze",
                    json=payload,
                    timeout=30.0,
                )
                response.raise_for_status()
                findings: list[dict[str, Any]] = response.json()
        except httpx.HTTPError as e:
            log.error("presidio_analyzer_error", error=str(e))
            raise RuntimeError("Service Presidio Analyzer indisponible") from e
        return findings
