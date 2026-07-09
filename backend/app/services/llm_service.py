import json
from typing import Any

import httpx
from fastapi import status
from tenacity import RetryError, retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.config import Settings
from app.core.exceptions import AppError, ErrorCode
from app.schemas.article import GenerateArticleRequest
from app.schemas.llm import ArticleCritiqueResult, ArticleValidationResult, LLMArticleOutput
from app.schemas.research import ArticleResearchContext
from app.services.prompt_builder import PromptBuilder


class LLMService:
    def __init__(self, settings: Settings, prompt_builder: PromptBuilder) -> None:
        self.settings = settings
        self.prompt_builder = prompt_builder

    async def generate_article(
        self,
        request: GenerateArticleRequest,
        research_context: ArticleResearchContext | None = None,
    ) -> LLMArticleOutput:
        if self.settings.llm_mode == "mock":
            return self._mock_article(request)

        messages = self.prompt_builder.build_messages(request, research_context)
        return await self._generate_article_from_messages(messages)

    async def critique_article(
        self,
        request: GenerateArticleRequest,
        article: LLMArticleOutput,
        validation_result: ArticleValidationResult,
        research_context: ArticleResearchContext | None = None,
    ) -> ArticleCritiqueResult:
        if self.settings.llm_mode == "mock":
            return self._mock_critique(validation_result)

        messages = self.prompt_builder.build_critique_messages(
            request=request,
            article=article,
            validation_result=validation_result,
            research_context=research_context,
        )
        return await self._generate_critique_from_messages(messages)

    async def revise_article(
        self,
        request: GenerateArticleRequest,
        previous_output: LLMArticleOutput,
        validation_result: ArticleValidationResult,
        critique_result: ArticleCritiqueResult,
        research_context: ArticleResearchContext | None = None,
    ) -> LLMArticleOutput:
        if self.settings.llm_mode == "mock":
            return self._mock_article(request)

        messages = self.prompt_builder.build_revision_messages(
            request=request,
            previous_output=previous_output,
            validation_result=validation_result,
            critique_result=critique_result,
            research_context=research_context,
        )
        return await self._generate_article_from_messages(messages)

    async def repair_article(
        self,
        request: GenerateArticleRequest,
        previous_output: LLMArticleOutput,
        validation_result: ArticleValidationResult,
        research_context: ArticleResearchContext | None = None,
    ) -> LLMArticleOutput:
        critique_result = ArticleCritiqueResult(
            passed=validation_result.passed,
            summary="Rule-based validation found issues that must be repaired.",
            issues=validation_result.errors
            + [f"Missing keyword: {keyword}" for keyword in validation_result.missing_keywords],
            recommendations=["Revise the draft so validation passes."],
            requires_revision=not validation_result.passed,
        )
        return await self.revise_article(
            request=request,
            previous_output=previous_output,
            validation_result=validation_result,
            critique_result=critique_result,
            research_context=research_context,
        )

    async def _generate_article_from_messages(
        self, messages: list[dict[str, str]]
    ) -> LLMArticleOutput:
        payload = await self._generate_json_payload(
            messages,
            response_schema=LLMArticleOutput.model_json_schema(),
            schema_name="llm_article_output",
        )
        try:
            content = payload["choices"][0]["message"]["content"]
            decoded = json.loads(content)
            return LLMArticleOutput.model_validate(decoded)
        except (KeyError, IndexError, TypeError, json.JSONDecodeError, ValueError) as exc:
            raise AppError(
                ErrorCode.LLM_INVALID_OUTPUT,
                "LLM article output was not valid JSON.",
                status_code=status.HTTP_502_BAD_GATEWAY,
                retryable=True,
            ) from exc

    async def _generate_critique_from_messages(
        self, messages: list[dict[str, str]]
    ) -> ArticleCritiqueResult:
        payload = await self._generate_json_payload(
            messages,
            response_schema=ArticleCritiqueResult.model_json_schema(),
            schema_name="article_critique_result",
        )
        try:
            content = payload["choices"][0]["message"]["content"]
            decoded = json.loads(content)
            return ArticleCritiqueResult.model_validate(decoded)
        except (KeyError, IndexError, TypeError, json.JSONDecodeError, ValueError) as exc:
            raise AppError(
                ErrorCode.LLM_INVALID_OUTPUT,
                "LLM critique output was not valid JSON.",
                status_code=status.HTTP_502_BAD_GATEWAY,
                retryable=True,
            ) from exc

    async def _generate_json_payload(
        self,
        messages: list[dict[str, str]],
        *,
        response_schema: dict[str, Any] | None = None,
        schema_name: str = "llm_response",
    ) -> dict:
        if not self.settings.llm_api_key:
            raise AppError(
                ErrorCode.LLM_INVALID_OUTPUT,
                "LLM_API_KEY is not configured.",
                status_code=status.HTTP_502_BAD_GATEWAY,
                retryable=False,
            )

        try:
            return await self._post_chat_completion(
                messages,
                response_schema=response_schema,
                schema_name=schema_name,
            )
        except RetryError as exc:
            if isinstance(exc.last_attempt.exception(), httpx.TimeoutException):
                raise AppError(
                    ErrorCode.LLM_TIMEOUT,
                    "LLM request timed out.",
                    status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                    retryable=True,
                ) from exc
            raise
        except httpx.TimeoutException as exc:
            raise AppError(
                ErrorCode.LLM_TIMEOUT,
                "LLM request timed out.",
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                retryable=True,
            ) from exc

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=2),
        retry=retry_if_exception_type(httpx.TimeoutException),
        reraise=False,
    )
    async def _post_chat_completion(
        self,
        messages: list[dict[str, str]],
        *,
        response_schema: dict[str, Any] | None = None,
        schema_name: str = "llm_response",
    ) -> dict:
        url = f"{self.settings.llm_api_base.rstrip('/')}/chat/completions"
        headers = {"Authorization": f"Bearer {self.settings.llm_api_key}"}
        response_format: dict[str, Any] = {"type": "json_object"}
        if response_schema is not None:
            response_format = {
                "type": "json_schema",
                "json_schema": {
                    "name": schema_name,
                    "strict": True,
                    "schema": response_schema,
                },
            }
        async with httpx.AsyncClient(timeout=self.settings.llm_timeout_seconds) as client:
            response = await client.post(
                url,
                headers=headers,
                json={
                    "model": self.settings.llm_model,
                    "messages": messages,
                    "temperature": 0.4,
                    "response_format": response_format,
                },
            )
        response.raise_for_status()
        return response.json()

    @staticmethod
    def _mock_article(request: GenerateArticleRequest) -> LLMArticleOutput:
        keywords = ", ".join(request.keywords)
        keyword_items = "".join(
            f"<li>{keyword}: practical angle for the target reader.</li>"
            for keyword in request.keywords
        )
        content_html = f"""
<h1>{request.topic}: SEO article draft</h1>
<p>This draft is written for {request.target_audience}. It introduces {request.topic} with a practical publishing angle and naturally includes the requested keyword set: {keywords}.</p>
<h2>Why this topic matters</h2>
<p>{request.topic} can help readers compare options, understand tradeoffs, and make a confident next step. The article keeps the language clear, uses scannable structure, and avoids unsafe markup so it can move into WordPress as a draft.</p>
<h2>Key SEO angles</h2>
<ul>{keyword_items}</ul>
<p>The content should connect search intent with useful guidance, then lead the reader toward a concrete action instead of ending with a vague summary.</p>
<h2>Next step</h2>
<p>{request.call_to_action}</p>
""".strip()
        return LLMArticleOutput(
            title=f"{request.topic}: SEO article draft",
            content_html=content_html,
        )

    @staticmethod
    def _mock_critique(validation_result: ArticleValidationResult) -> ArticleCritiqueResult:
        if validation_result.passed:
            return ArticleCritiqueResult(
                passed=True,
                summary="Mock critique approved the article.",
                issues=[],
                recommendations=[],
                requires_revision=False,
            )

        return ArticleCritiqueResult(
            passed=False,
            summary="Mock critique found validation issues that require revision.",
            issues=validation_result.errors
            + [f"Missing keyword: {keyword}" for keyword in validation_result.missing_keywords],
            recommendations=["Revise the draft until all validator checks pass."],
            requires_revision=True,
        )
