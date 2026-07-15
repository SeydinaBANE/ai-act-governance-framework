from __future__ import annotations

from app.domain.model_card.ports import ModelCardGenerationContext


class FakeLLM:
    def __init__(self, sections: dict[str, str] | None = None) -> None:
        self.sections = sections if sections is not None else {}
        self.calls: list[ModelCardGenerationContext] = []

    async def generate_sections(self, context: ModelCardGenerationContext) -> dict[str, str]:
        self.calls.append(context)
        return self.sections
