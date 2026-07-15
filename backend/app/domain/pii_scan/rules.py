from __future__ import annotations

import hashlib
from typing import Any

from app.domain.pii_scan.ports import PIIScanResult

_RISK_THRESHOLDS: list[tuple[int, str]] = [
    (50, "critical"),
    (20, "high"),
    (5, "medium"),
    (1, "low"),
    (0, "none"),
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


def compute_source_hash(content: str | bytes) -> str:
    data = content.encode() if isinstance(content, str) else content
    return hashlib.sha256(data).hexdigest()


def compute_risk_level(total_findings: int) -> str:
    for threshold, level in _RISK_THRESHOLDS:
        if total_findings >= threshold:
            return level
    return "none"


def summarize_entities(findings: list[dict[str, Any]]) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for finding in findings:
        entity_type = finding.get("entity_type", "UNKNOWN")
        summary[entity_type] = summary.get(entity_type, 0) + 1
    return summary


def build_recommendations(entity_summary: dict[str, Any]) -> list[str]:
    return [
        f"[{entity_type}] {_RECOMMENDATIONS[entity_type]}"
        for entity_type in entity_summary
        if entity_type in _RECOMMENDATIONS
    ]


def build_scan_result(
    content: str | bytes, findings: list[dict[str, Any]], *, total_items: int
) -> PIIScanResult:
    entity_summary = summarize_entities(findings)
    total = sum(entity_summary.values())
    return PIIScanResult(
        source_hash=compute_source_hash(content),
        total_items=total_items,
        pii_found=total > 0,
        findings=findings,
        entity_summary=entity_summary,
        risk_level=compute_risk_level(total),
        recommendations=build_recommendations(entity_summary),
    )
