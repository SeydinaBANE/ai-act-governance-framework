from __future__ import annotations

import json
from typing import Any

import httpx
import structlog

from app.config import settings
from app.models.ai_system import AISystem
from app.models.risk_assessment import RiskAssessment

log = structlog.get_logger(__name__)

_SYSTEM_PROMPT = """Tu es un expert en gouvernance IA et conformité AI Act.
À partir des informations d'un système IA, génère des descriptions concises et professionnelles
pour les sections d'une model card européenne conforme à l'AI Act.
Réponds uniquement en JSON avec les clés demandées. Sois précis et factuel."""


async def generate_sections(
    client: httpx.AsyncClient,
    system: AISystem,
    assessment: RiskAssessment | None = None,
) -> dict[str, Any]:
    context = {
        "system_name": system.name,
        "description": system.description,
        "use_case": system.use_case,
        "tech_stack": system.tech_stack,
        "is_autonomous": system.is_autonomous,
        "affects_persons": system.affects_persons,
        "deployment_env": system.deployment_env,
        "data_types": system.data_types,
        "risk_category": assessment.risk_category if assessment else "non évalué",
        "ai_act_articles": assessment.ai_act_articles if assessment else [],
    }

    prompt = f"""Génère les sections suivantes pour ce système IA :
{json.dumps(context, ensure_ascii=False, indent=2)}

Retourne un JSON avec exactement ces clés :
- "limitations": limitations connues du système (2-3 phrases)
- "out_of_scope_uses": usages non prévus et à éviter (2-3 phrases)
- "ethical_considerations": considérations éthiques spécifiques (2-3 phrases)
- "conformity_measures": mesures de conformité AI Act en place ou à mettre en place (2-3 phrases)
- "human_oversight": description de la supervision humaine (2-3 phrases)
- "known_biases": biais potentiels identifiés (1-2 phrases)"""

    if not settings.openrouter_api_key:
        log.warning("openrouter_not_configured", message="Génération LLM désactivée")
        return {}

    try:
        response = await client.post(
            f"{settings.openrouter_base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.openrouter_api_key}",
                "HTTP-Referer": "https://aiact-governance.internal",
                "X-Title": "AI Act Governance Framework",
            },
            json={
                "model": settings.openrouter_model,
                "messages": [
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.3,
                "max_tokens": 800,
            },
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        return json.loads(content)  # type: ignore[no-any-return]
    except (httpx.HTTPError, json.JSONDecodeError, KeyError) as e:
        log.error("openrouter_generation_failed", error=str(e))
        return {}
