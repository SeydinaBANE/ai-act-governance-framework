from __future__ import annotations

import json
import re
from typing import Any

from app.domain.model_card.ports import ModelCardGenerationContext

SYSTEM_PROMPT = """Tu es un expert en gouvernance IA et conformité AI Act.
À partir des informations d'un système IA, génère des descriptions concises et professionnelles
pour les sections d'une model card européenne conforme à l'AI Act.
Sois précis et factuel. Réponds UNIQUEMENT avec un objet JSON valide, sans texte avant ou après."""

EXPECTED_KEYS = [
    "limitations",
    "out_of_scope_uses",
    "ethical_considerations",
    "conformity_measures",
    "human_oversight",
    "known_biases",
]


def build_prompt(context: ModelCardGenerationContext) -> str:
    system = context.system
    assessment = context.assessment
    payload = {
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

    return f"""Voici les informations d'un système IA :
{json.dumps(payload, ensure_ascii=False, indent=2)}

Génère un objet JSON avec exactement ces 6 clés (2-3 phrases chacune, en français) :
{{
  "limitations": "...",
  "out_of_scope_uses": "...",
  "ethical_considerations": "...",
  "conformity_measures": "...",
  "human_oversight": "...",
  "known_biases": "..."
}}"""


def extract_json(text: str) -> dict[str, Any]:
    text = text.strip()
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        text = match.group(1)
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        text = match.group(0)
    result: dict[str, Any] = json.loads(text)
    return result


def filter_expected_sections(result: dict[str, Any]) -> dict[str, str]:
    return {k: v for k, v in result.items() if k in EXPECTED_KEYS}
