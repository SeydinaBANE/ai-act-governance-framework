from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import structlog

from app.models.ai_system import RiskCategory

log = structlog.get_logger(__name__)

_QUESTIONNAIRE_PATH = Path(__file__).parent.parent / "data" / "questionnaire.json"


def _load_questionnaire() -> dict[str, Any]:
    with _QUESTIONNAIRE_PATH.open() as f:
        return json.load(f)


def _flatten_questions(questionnaire: dict[str, Any]) -> list[dict[str, Any]]:
    questions: list[dict[str, Any]] = []
    for section in questionnaire["sections"]:
        questions.extend(section["questions"])
    return questions


def get_questionnaire() -> dict[str, Any]:
    return _load_questionnaire()


class RiskScorerResult:
    def __init__(
        self,
        risk_category: RiskCategory,
        total_score: int,
        score_details: dict[str, Any],
        justification: str,
        ai_act_articles: list[str],
        required_actions: list[dict[str, str]],
        valid_until: date,
    ) -> None:
        self.risk_category = risk_category
        self.total_score = total_score
        self.score_details = score_details
        self.justification = justification
        self.ai_act_articles = ai_act_articles
        self.required_actions = required_actions
        self.valid_until = valid_until


# Obligations par catégorie de risque
_OBLIGATIONS: dict[str, list[dict[str, str]]] = {
    "prohibited": [
        {
            "article": "Art. 5",
            "obligation": "Cessation immédiate — système interdit par l'AI Act",
            "deadline": "immédiat",
        }
    ],
    "high_risk": [
        {
            "article": "Art. 9",
            "obligation": "Mettre en place un système de gestion des risques",
            "deadline": "2025-08-02",
        },
        {
            "article": "Art. 10",
            "obligation": "Gouvernance des données d'entraînement documentée",
            "deadline": "2025-08-02",
        },
        {
            "article": "Art. 13",
            "obligation": "Assurer la transparence et fournir des informations aux utilisateurs",
            "deadline": "2025-08-02",
        },
        {
            "article": "Art. 14",
            "obligation": "Mettre en œuvre une supervision humaine effective",
            "deadline": "2025-08-02",
        },
        {
            "article": "Art. 17",
            "obligation": "Établir un système de management de la qualité",
            "deadline": "2025-08-02",
        },
        {
            "article": "Art. 72",
            "obligation": "Enregistrement dans la base de données EU",
            "deadline": "2025-08-02",
        },
    ],
    "limited_risk": [
        {
            "article": "Art. 50",
            "obligation": "Informer les utilisateurs qu'ils interagissent avec un système IA",
            "deadline": "2025-08-02",
        }
    ],
    "minimal_risk": [],
}


def assess(answers: dict[str, bool]) -> RiskScorerResult:
    questionnaire = _load_questionnaire()
    questions = _flatten_questions(questionnaire)

    score_details: dict[str, Any] = {}
    triggered_articles: list[str] = []
    total_score = 0

    # --- Niveau 1 : interdictions absolues (Art. 5) ---
    prohibited_triggers = [q for q in questions if q.get("triggers_prohibited")]
    for q in prohibited_triggers:
        answer = answers.get(q["id"], False)
        score_details[q["id"]] = {"triggered": answer, "weight": q["weight"]}
        if answer:
            triggered_articles.append(q["ai_act_ref"])
            log.info("prohibited_rule_triggered", rule=q["rule"], question_id=q["id"])
            return RiskScorerResult(
                risk_category=RiskCategory.PROHIBITED,
                total_score=100,
                score_details=score_details,
                justification=(
                    f"Le système déclenche une interdiction absolue selon {q['ai_act_ref']} "
                    f"(question : {q['text'][:80]}...). Les systèmes de cette catégorie sont "
                    "formellement interdits par l'AI Act et doivent cesser immédiatement."
                ),
                ai_act_articles=triggered_articles,
                required_actions=_OBLIGATIONS["prohibited"],
                valid_until=date.today(),
            )

    # --- Niveau 2 : haut risque (Annexe III) ---
    high_risk_triggers = [q for q in questions if q.get("triggers_high_risk")]
    is_high_risk = False
    for q in high_risk_triggers:
        answer = answers.get(q["id"], False)
        score_details[q["id"]] = {"triggered": answer, "weight": q["weight"]}
        if answer:
            is_high_risk = True
            triggered_articles.append(q["ai_act_ref"])
            total_score = max(total_score, q["weight"])

    if is_high_risk:
        return RiskScorerResult(
            risk_category=RiskCategory.HIGH_RISK,
            total_score=total_score,
            score_details=score_details,
            justification=(
                f"Le système relève de l'Annexe III de l'AI Act ({', '.join(triggered_articles)}). "
                "En tant que système à haut risque, il est soumis à des obligations strictes "
                "de gestion des risques, de traçabilité, de supervision humaine "
                "et d'enregistrement dans la base de données EU avant mise en service."
            ),
            ai_act_articles=triggered_articles,
            required_actions=_OBLIGATIONS["high_risk"],
            valid_until=date.today() + timedelta(days=365),
        )

    # --- Niveau 3 : scoring pondéré (limited vs minimal) ---
    scored_questions = [
        q for q in questions if not q.get("triggers_prohibited") and not q.get("triggers_high_risk")
    ]
    for q in scored_questions:
        # Questions non répondues n'affectent pas le score (ni positif ni négatif)
        if q["id"] not in answers:
            score_details[q["id"]] = {
                "triggered": None,
                "weight": q["weight"],
                "contributes": False,
            }
            continue

        answer = answers[q["id"]]
        weight = q["weight"]
        inverted = q.get("inverted", False)
        # inverted=True : réponse True = mitigation en place → ne contribue PAS
        # inverted=True : réponse False = mitigation absente → contribue
        contributes = (answer and not inverted) or (not answer and inverted)
        score_details[q["id"]] = {
            "triggered": answer,
            "weight": weight,
            "contributes": contributes,
        }
        if contributes:
            total_score += weight

    if total_score >= 30:
        category = RiskCategory.LIMITED_RISK
        justification = (
            f"Le système obtient un score de risque de {total_score}/100. "
            "Il relève de la catégorie 'risque limité' et doit respecter les obligations "
            "de transparence de l'Art. 50 : informer les utilisateurs "
            "qu'ils interagissent avec un système IA."
        )
        articles = ["Art. 50"]
    else:
        category = RiskCategory.MINIMAL_RISK
        justification = (
            f"Le système obtient un score de risque de {total_score}/100. "
            "Il relève de la catégorie 'risque minimal'. "
            "Aucune obligation réglementaire spécifique n'est imposée par l'AI Act, "
            "mais le respect des bonnes pratiques est recommandé."
        )
        articles = []

    return RiskScorerResult(
        risk_category=category,
        total_score=total_score,
        score_details=score_details,
        justification=justification,
        ai_act_articles=articles,
        required_actions=_OBLIGATIONS.get(category.value, []),
        valid_until=date.today() + timedelta(days=365),
    )
