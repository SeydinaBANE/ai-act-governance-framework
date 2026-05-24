from __future__ import annotations

import json
import re
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
Sois précis et factuel. Réponds UNIQUEMENT avec un objet JSON valide, sans texte avant ou après."""

_EXPECTED_KEYS = ["limitations", "out_of_scope_uses", "ethical_considerations",
                  "conformity_measures", "human_oversight", "known_biases"]


def _extract_json(text: str) -> dict[str, Any]:
    """Extrait un objet JSON d'un texte qui peut contenir du markdown."""
    text = text.strip()
    # Extraire depuis un bloc ```json ... ```
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        text = match.group(1)
    # Chercher le premier { ... } dans le texte
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        text = match.group(0)
    return json.loads(text)  # type: ignore[no-any-return]


async def generate_sections(
    client: httpx.AsyncClient,
    system: AISystem,
    assessment: RiskAssessment | None = None,
) -> dict[str, Any]:
    if not settings.openrouter_api_key:
        log.warning("openrouter_not_configured")
        return {}

    context = {
        "system_name": system.name,
        "description": system.description,
        "use_case": system.use_case,
        "tech_stack": system.tech_stack,
        "is_autonomous": system.is_autonomous,
        "affects_persons": system.affects_persons,
        "deployment_env": system.deployment_env,
        "data_types": system.data_types,
        "risk_category": str(assessment.risk_category.value) if assessment else "non évalué",
        "ai_act_articles": assessment.ai_act_articles if assessment else [],
    }

    prompt = f"""Voici les informations d'un système IA :
{json.dumps(context, ensure_ascii=False, indent=2)}

Génère un objet JSON avec exactement ces 6 clés (2-3 phrases chacune, en français) :
{{
  "limitations": "...",
  "out_of_scope_uses": "...",
  "ethical_considerations": "...",
  "conformity_measures": "...",
  "human_oversight": "...",
  "known_biases": "..."
}}"""

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
                "temperature": 0.3,
                "max_tokens": 1000,
            },
            timeout=45.0,
        )
        response.raise_for_status()
        data = response.json()

        # Log si erreur renvoyée par OpenRouter
        if "error" in data:
            log.error("openrouter_api_error", error=data["error"])
            return {}

        content = data["choices"][0]["message"]["content"]
        if not content:
            log.error("openrouter_empty_content", raw_response=str(data))
            return {}

        result = _extract_json(content)
        # Ne garder que les clés attendues
        return {k: v for k, v in result.items() if k in _EXPECTED_KEYS}

    except json.JSONDecodeError as e:
        log.error("openrouter_json_parse_failed", error=str(e))
        return {}
    except httpx.HTTPStatusError as e:
        log.error("openrouter_http_error", status=e.response.status_code, body=e.response.text[:200])
        return {}
    except (httpx.HTTPError, KeyError) as e:
        log.error("openrouter_generation_failed", error=str(e))
        return {}
