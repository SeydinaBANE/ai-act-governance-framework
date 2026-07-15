from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, Protocol

from app.models.pii_scan import PIIScan


@dataclass(frozen=True)
class PIIScanResult:
    source_hash: str
    total_items: int
    pii_found: bool
    findings: list[dict[str, Any]]
    entity_summary: dict[str, Any]
    risk_level: str
    recommendations: list[str]


class PIIScanRepository(Protocol):
    async def add(self, scan: PIIScan) -> None: ...

    async def get(self, scan_id: uuid.UUID) -> PIIScan | None: ...

    async def list_by_user(
        self, user_id: uuid.UUID, *, page: int, per_page: int
    ) -> tuple[list[PIIScan], int]: ...


class PIIScannerPort(Protocol):
    async def scan_text(
        self, text: str, *, language: str = "fr", confidence_threshold: float = 0.85
    ) -> PIIScanResult: ...

    async def scan_file(
        self, content: bytes, filename: str, *, confidence_threshold: float = 0.85
    ) -> PIIScanResult: ...
