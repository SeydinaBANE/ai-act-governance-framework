from __future__ import annotations

import json

import httpx
import structlog

from app.config import settings
from app.domain.model_card import rules
from app.domain.model_card.ports import ModelCardGenerationContext

log = structlog.get_logger(__name__)


class OpenRouterLLM:
    async def generate_sections(self, context: ModelCardGenerationContext) -> dict[str, str]:
        if not settings.openrouter_api_key:
            log.warning("openrouter_not_configured")
            return {}

        prompt = rules.build_prompt(context)

        try:
            async with httpx.AsyncClient() as client:
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
                            {"role": "system", "content": rules.SYSTEM_PROMPT},
                            {"role": "user", "content": prompt},
                        ],
                        "temperature": 0.3,
                        "max_tokens": 1000,
                    },
                    timeout=45.0,
                )
                response.raise_for_status()
                data = response.json()

            if "error" in data:
                log.error("openrouter_api_error", error=data["error"])
                return {}

            content = data["choices"][0]["message"]["content"]
            if not content:
                log.error("openrouter_empty_content", raw_response=str(data))
                return {}

            result = rules.extract_json(content)
            return rules.filter_expected_sections(result)

        except json.JSONDecodeError as e:
            log.error("openrouter_json_parse_failed", error=str(e))
            return {}
        except httpx.HTTPStatusError as e:
            log.error(
                "openrouter_http_error", status=e.response.status_code, body=e.response.text[:200]
            )
            return {}
        except (httpx.HTTPError, KeyError) as e:
            log.error("openrouter_generation_failed", error=str(e))
            return {}
