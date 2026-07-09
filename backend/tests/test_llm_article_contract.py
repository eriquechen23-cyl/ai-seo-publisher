import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.schemas.llm import LLMArticleOutput
from app.services.llm_service import LLMService
from app.services.prompt_builder import PromptBuilder


def test_article_output_rejects_non_strict_or_extra_llm_output() -> None:
    with pytest.raises(ValidationError):
        LLMArticleOutput.model_validate(
            {
                "title": 123,
                "content_html": "<h1>Valid title</h1><p>This body is long enough for validation.</p>",
                "notes": "extra text from the model",
            }
        )

    with pytest.raises(ValidationError):
        LLMArticleOutput.model_validate(
            {
                "title": "Valid article",
                "content_html": "<h1>Valid title</h1><p>This body is long enough for validation.</p>",
                "notes": "extra text from the model",
            }
        )


def test_producer_prompt_includes_strict_article_validator_schema() -> None:
    prompt = PromptBuilder()._producer_system_prompt()

    assert "Return exactly one valid JSON object" in prompt
    assert '"additionalProperties": false' in prompt
    assert '"title"' in prompt
    assert '"content_html"' in prompt


@pytest.mark.asyncio
async def test_article_generation_uses_article_validator_schema() -> None:
    class CapturingLLMService(LLMService):
        def __init__(self) -> None:
            super().__init__(
                Settings(
                    llm_mode="openai_compatible",
                    llm_api_key="test-key",
                ),
                PromptBuilder(),
            )
            self.response_schema: dict | None = None
            self.schema_name: str | None = None

        async def _generate_json_payload(
            self,
            messages: list[dict[str, str]],
            *,
            response_schema: dict | None = None,
            schema_name: str = "llm_response",
        ) -> dict:
            self.response_schema = response_schema
            self.schema_name = schema_name
            return {
                "choices": [
                    {
                        "message": {
                            "content": (
                                '{"title": "Valid article", '
                                '"content_html": "<h1>Valid article</h1><p>This article body is long enough.</p>"}'
                            )
                        }
                    }
                ]
            }

    service = CapturingLLMService()

    result = await service._generate_article_from_messages(
        [{"role": "user", "content": "Write an article."}]
    )

    assert result.title == "Valid article"
    assert service.schema_name == "llm_article_output"
    assert service.response_schema is not None
    assert service.response_schema["additionalProperties"] is False
    assert set(service.response_schema["required"]) == {"title", "content_html"}
