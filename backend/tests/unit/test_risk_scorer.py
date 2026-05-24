from __future__ import annotations

from app.models.ai_system import RiskCategory
from app.services.risk_scorer import assess


def test_prohibited_biometric_realtime() -> None:
    answers = {"q1_biometric_realtime": True}
    result = assess(answers)
    assert result.risk_category == RiskCategory.PROHIBITED
    assert result.total_score == 100
    assert "Art. 5" in " ".join(result.ai_act_articles)
    assert len(result.required_actions) > 0


def test_prohibited_social_scoring() -> None:
    answers = {"q2_social_scoring": True}
    result = assess(answers)
    assert result.risk_category == RiskCategory.PROHIBITED


def test_prohibited_subliminal() -> None:
    answers = {"q3_subliminal": True}
    result = assess(answers)
    assert result.risk_category == RiskCategory.PROHIBITED


def test_high_risk_critical_infrastructure() -> None:
    answers = {"q5_critical_infra": True}
    result = assess(answers)
    assert result.risk_category == RiskCategory.HIGH_RISK
    assert "Annexe III" in " ".join(result.ai_act_articles)


def test_high_risk_employment() -> None:
    answers = {"q7_employment": True}
    result = assess(answers)
    assert result.risk_category == RiskCategory.HIGH_RISK
    assert result.valid_until is not None


def test_high_risk_multiple_domains() -> None:
    answers = {"q6_education": True, "q7_employment": True}
    result = assess(answers)
    assert result.risk_category == RiskCategory.HIGH_RISK
    assert len(result.required_actions) >= 3


def test_limited_risk_autonomous_sensitive_data() -> None:
    answers = {
        "q12_autonomous_decision": True,
        "q13_irreversible": True,
        "q15_sensitive_data": True,
    }
    result = assess(answers)
    assert result.risk_category == RiskCategory.LIMITED_RISK
    assert result.total_score >= 30


def test_minimal_risk_no_answers() -> None:
    result = assess({})
    assert result.risk_category == RiskCategory.MINIMAL_RISK
    assert result.total_score == 0
    assert result.required_actions == []


def test_minimal_risk_with_all_mitigations() -> None:
    # Answering all mitigations as True (in place) → score stays 0
    answers = {
        "q14_explainability": True,
        "q18_risk_management": True,
        "q19_human_oversight": True,
        "q20_logging": True,
    }
    result = assess(answers)
    assert result.risk_category == RiskCategory.MINIMAL_RISK
    assert result.total_score == 0


def test_unanswered_questions_dont_contribute() -> None:
    # Questions left out of answers dict → no effect on score
    result = assess({"q12_autonomous_decision": True})  # weight 25 only
    assert result.total_score == 25
    assert result.risk_category == RiskCategory.MINIMAL_RISK


def test_prohibited_takes_priority_over_high_risk() -> None:
    answers = {
        "q1_biometric_realtime": True,
        "q5_critical_infra": True,
    }
    result = assess(answers)
    assert result.risk_category == RiskCategory.PROHIBITED


def test_justification_not_empty() -> None:
    result = assess({})
    assert result.justification
    assert len(result.justification) > 10


def test_valid_until_future_date_for_non_prohibited() -> None:
    from datetime import date

    result = assess({})
    assert result.valid_until > date.today()
