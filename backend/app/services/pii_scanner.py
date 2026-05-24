from __future__ import annotations

import hashlib
from typing import Any

import httpx
import structlog

from app.config import settings
from app.models.pii_scan import PIIScanRiskLevel

log = structlog.get_logger(__name__)

# Mapping : nb d'entités → niveau de risque
_RISK_THRESHOLDS = [
    (50, PIIScanRiskLevel.CRITICAL),
    (20, PIIScanRiskLevel.HIGH),
    (5, PIIScanRiskLevel.MEDIUM),
    (1, PIIScanRiskLevel.LOW),
    (0, PIIScanRiskLevel.NONE),
]

_RECOMMENDATIONS: dict[str, str] = {
    "PERSON": "Anonymiser les noms avant stockage ou partage",
    "EMAIL_ADDRESS": "Remplacer les emails par des identifiants internes",
    "PHONE_NUMBER": "Masquer ou supprimer les numéros de téléphone",
    "IBAN_CODE": "Ne jamais stocker les IBAN en clair — utiliser un coffre-fort sécurisé",
    "CREDIT_CARD": "Non-conformité PCI-DSS potentielle — audit immédiat requis",
    "FR_NIN": "Numéro INSEE : données sensibles au sens RGPD — traitement spécial requis",
    "FR_SIRET": "SIRET : vérifier si l'association avec d'autres données crée un risque",
    "IP_ADDRESS": "Données personnelles selon CJUE — journalisation à encadrer",
    "URL": "Vérifier si l'URL contient des paramètres personnels",
    "DATE_TIME": "Vérifier si la date est associée à une identité",
}


def _compute_source_hash(content: str | bytes) -> str:
    data = content.encode() if isinstance(content, str) else content
    return hashlib.sha256(data).hexdigest()


def _compute_risk_level(total_findings: int) -> PIIScanRiskLevel:
    for threshold, level in _RISK_THRESHOLDS:
        if total_findings >= threshold:
            return level
    return PIIScanRiskLevel.NONE


def _build_recommendations(entity_summary: dict[str, int]) -> list[str]:
    recs = []
    for entity_type in entity_summary:
        if rec := _RECOMMENDATIONS.get(entity_type):
            recs.append(f"[{entity_type}] {rec}")
    return recs


async def scan_text(
    client: httpx.AsyncClient,
    text: str,
    language: str = "fr",
    confidence_threshold: float = 0.85,
) -> dict[str, Any]:
    payload = {
        "text": text,
        "language": language,
        "score_threshold": confidence_threshold,
    }

    try:
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

    entity_summary: dict[str, int] = {}
    for finding in findings:
        entity_type = finding.get("entity_type", "UNKNOWN")
        entity_summary[entity_type] = entity_summary.get(entity_type, 0) + 1

    total = sum(entity_summary.values())
    source_hash = _compute_source_hash(text)

    return {
        "source_hash": source_hash,
        "total_items": len(text.split()),
        "pii_found": total > 0,
        "findings": findings,
        "entity_summary": entity_summary,
        "risk_level": _compute_risk_level(total),
        "recommendations": _build_recommendations(entity_summary),
    }


async def scan_file_content(
    client: httpx.AsyncClient,
    content: bytes,
    filename: str,
    confidence_threshold: float = 0.85,
) -> dict[str, Any]:
    text = content.decode(errors="replace")

    # Chunking pour les gros fichiers (Presidio a une limite de taille)
    chunk_size = 5000
    chunks = [text[i: i + chunk_size] for i in range(0, len(text), chunk_size)]

    all_findings: list[dict[str, Any]] = []
    offset = 0
    for chunk in chunks:
        result = await scan_text(client, chunk, confidence_threshold=confidence_threshold)
        for finding in result["findings"]:
            adjusted = finding.copy()
            adjusted["start"] = finding.get("start", 0) + offset
            adjusted["end"] = finding.get("end", 0) + offset
            all_findings.append(adjusted)
        offset += len(chunk)

    entity_summary: dict[str, int] = {}
    for finding in all_findings:
        entity_type = finding.get("entity_type", "UNKNOWN")
        entity_summary[entity_type] = entity_summary.get(entity_type, 0) + 1

    total = sum(entity_summary.values())

    return {
        "source_hash": _compute_source_hash(content),
        "source_name": filename,
        "total_items": len(text.split()),
        "pii_found": total > 0,
        "findings": all_findings,
        "entity_summary": entity_summary,
        "risk_level": _compute_risk_level(total),
        "recommendations": _build_recommendations(entity_summary),
    }
