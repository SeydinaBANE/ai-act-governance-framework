from __future__ import annotations

from app.domain.model_card import rules
from app.domain.model_card.ports import ModelCardGenerationContext

from tests.factories.ai_system_factory import AISystemFactory


def test_build_prompt_includes_system_name_and_unassessed_category() -> None:
    system = AISystemFactory.build(name="Scoring crédit")
    context = ModelCardGenerationContext(system=system, assessment=None)

    prompt = rules.build_prompt(context)

    assert "Scoring crédit" in prompt
    assert "non évalué" in prompt


def test_extract_json_parses_raw_object() -> None:
    result = rules.extract_json('{"limitations": "aucune"}')

    assert result == {"limitations": "aucune"}


def test_extract_json_parses_fenced_code_block() -> None:
    text = '```json\n{"limitations": "aucune"}\n```'

    result = rules.extract_json(text)

    assert result == {"limitations": "aucune"}


def test_extract_json_parses_object_surrounded_by_prose() -> None:
    text = 'Voici le résultat :\n{"limitations": "aucune"}\nFin.'

    result = rules.extract_json(text)

    assert result == {"limitations": "aucune"}


def test_filter_expected_sections_drops_unknown_keys() -> None:
    result = rules.filter_expected_sections({"limitations": "a", "not_a_real_section": "b"})

    assert result == {"limitations": "a"}
