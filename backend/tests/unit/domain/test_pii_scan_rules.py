from __future__ import annotations

from app.domain.pii_scan import rules


def test_compute_source_hash_deterministic() -> None:
    assert rules.compute_source_hash("hello") == rules.compute_source_hash("hello")


def test_compute_source_hash_differs_for_bytes_and_str_with_same_content() -> None:
    assert rules.compute_source_hash("hello") == rules.compute_source_hash(b"hello")


def test_compute_risk_level_thresholds() -> None:
    assert rules.compute_risk_level(0) == "none"
    assert rules.compute_risk_level(1) == "low"
    assert rules.compute_risk_level(5) == "medium"
    assert rules.compute_risk_level(20) == "high"
    assert rules.compute_risk_level(50) == "critical"
    assert rules.compute_risk_level(51) == "critical"


def test_summarize_entities_counts_by_type() -> None:
    findings = [
        {"entity_type": "PERSON"},
        {"entity_type": "PERSON"},
        {"entity_type": "EMAIL_ADDRESS"},
    ]

    summary = rules.summarize_entities(findings)

    assert summary == {"PERSON": 2, "EMAIL_ADDRESS": 1}


def test_summarize_entities_missing_type_becomes_unknown() -> None:
    summary = rules.summarize_entities([{}])

    assert summary == {"UNKNOWN": 1}


def test_build_recommendations_known_entities_only() -> None:
    recs = rules.build_recommendations({"PERSON": 1, "NOT_A_REAL_ENTITY": 1})

    assert len(recs) == 1
    assert recs[0].startswith("[PERSON]")


def test_build_scan_result_no_findings_is_not_pii_found() -> None:
    result = rules.build_scan_result("clean text", [], total_items=2)

    assert result.pii_found is False
    assert result.risk_level == "none"
    assert result.findings == []


def test_build_scan_result_with_findings_is_pii_found() -> None:
    findings = [{"entity_type": "EMAIL_ADDRESS"}]

    result = rules.build_scan_result("contact: a@b.com", findings, total_items=2)

    assert result.pii_found is True
    assert result.entity_summary == {"EMAIL_ADDRESS": 1}
    assert result.risk_level == "low"
    assert any("EMAIL_ADDRESS" in rec for rec in result.recommendations)
