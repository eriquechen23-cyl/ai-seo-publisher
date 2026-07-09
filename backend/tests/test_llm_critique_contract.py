import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.schemas.article import GenerateArticleRequest
from app.schemas.llm import ArticleCritiqueResult, ArticleValidationResult, LLMArticleOutput
from app.services.llm_service import LLMService
from app.services.prompt_builder import PromptBuilder


def _request() -> GenerateArticleRequest:
    return GenerateArticleRequest(
        topic="AI SEO workflow",
        keywords=["AI SEO", "content review"],
        target_audience="marketing teams",
        call_to_action="Schedule a content audit.",
    )


def _article() -> LLMArticleOutput:
    return LLMArticleOutput(
        title="AI SEO workflow with content review",
        content_html=(
            "<h1>AI SEO workflow</h1>"
            "<p>This draft explains AI SEO and content review for marketing teams.</p>"
        ),
    )


def _validation_result() -> ArticleValidationResult:
    return ArticleValidationResult(passed=True, errors=[], missing_keywords=[])


def test_critique_result_rejects_non_strict_or_extra_llm_output() -> None:
    with pytest.raises(ValidationError):
        ArticleCritiqueResult.model_validate(
            {
                "passed": "true",
                "summary": "Looks ready.",
                "issues": [],
                "recommendations": [],
                "requires_revision": False,
                "score": 98,
            }
        )


def test_critique_prompt_includes_strict_validator_schema() -> None:
    messages = PromptBuilder().build_critique_messages(
        request=_request(),
        article=_article(),
        validation_result=_validation_result(),
    )

    prompt = messages[-1]["content"]

    assert "Return exactly one valid JSON object" in prompt
    assert '"additionalProperties": false' in prompt
    assert '"passed"' in prompt
    assert '"requires_revision"' in prompt


@pytest.mark.asyncio
async def test_critique_generation_uses_critique_validator_schema() -> None:
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
                                '{"passed": true, "summary": "Ready.", "issues": [], '
                                '"recommendations": [], "requires_revision": false}'
                            )
                        }
                    }
                ]
            }

    service = CapturingLLMService()

    result = await service._generate_critique_from_messages(
        [{"role": "user", "content": "Critique this article."}]
    )

    assert result.passed is True
    assert service.schema_name == "article_critique_result"
    assert service.response_schema is not None
    assert service.response_schema["additionalProperties"] is False
    assert set(service.response_schema["required"]) == {
        "passed",
        "summary",
        "issues",
        "recommendations",
        "requires_revision",
    }
