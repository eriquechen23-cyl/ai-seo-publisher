import json

from fastapi import status

from app.core.exceptions import AppError, ErrorCode
from app.repositories.article_job_repository import ArticleJobRepository
from app.schemas.article import (
    ArticleJobError,
    ArticleJobResponse,
    ArticleJobStatus,
    ArticleToolStatus,
    GenerateArticleRequest,
)
from app.schemas.research import ArticleResearchContext
from app.services.article_agent_router import AgentRouteDecision
from app.schemas.llm import LLMArticleOutput
from app.services.article_agent_pipeline import ArticleAgentPipeline
from app.services.article_validator import ArticleValidator
from app.services.llm_service import LLMService
from app.services.wordpress_client import WordPressClient


class ArticleWorkflowService:
    def __init__(
        self,
        *,
        repository: ArticleJobRepository,
        llm_service: LLMService,
        validator: ArticleValidator,
        wordpress_client: WordPressClient,
        agent_pipeline: ArticleAgentPipeline | None = None,
    ) -> None:
        self.repository = repository
        self.llm_service = llm_service
        self.validator = validator
        self.wordpress_client = wordpress_client
        self.agent_pipeline = agent_pipeline or ArticleAgentPipeline(
            llm_service=llm_service,
            validator=validator,
        )

    def enqueue(self, request: GenerateArticleRequest) -> str:
        job = self.repository.create(request)
        return job.id

    async def process_job(self, job_id: str, request: GenerateArticleRequest) -> None:
        try:
            self.repository.update_status(job_id, ArticleJobStatus.GENERATING)
            pipeline_result = await self.agent_pipeline.run(
                request,
                on_validating=lambda: self.repository.update_status(
                    job_id, ArticleJobStatus.VALIDATING
                ),
                on_reflection=lambda: self.repository.mark_repairing(job_id),
                on_research_complete=lambda research_context, route_decision: (
                    self._persist_tool_status(job_id, research_context, route_decision)
                ),
            )
            article = pipeline_result.article

            sanitized_html = self.validator.sanitize(article.content_html)
            sanitized_article = LLMArticleOutput(
                title=article.title,
                content_html=sanitized_html,
            )
            final_validation = self.validator.validate(sanitized_article, request.keywords)
            if not final_validation.passed:
                raise AppError(
                    ErrorCode.ARTICLE_VALIDATION_FAILED,
                    "Article failed validation after sanitization.",
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    retryable=True,
                    details={
                        "validation": final_validation.model_dump(),
                        "critique": pipeline_result.critique.model_dump(),
                        "reflection_count": pipeline_result.reflection_count,
                    },
                )

            self.repository.update_status(job_id, ArticleJobStatus.PUBLISHING)
            wordpress_post = await self.wordpress_client.create_draft(
                title=sanitized_article.title,
                content_html=sanitized_article.content_html,
            )
            post_id = int(wordpress_post["id"])

            self.repository.complete(
                job_id,
                generated_title=sanitized_article.title,
                generated_html=sanitized_article.content_html,
                wordpress_post_id=post_id,
            )
        except AppError as exc:
            self.repository.fail(
                job_id,
                status=self._failed_status(exc),
                error_code=exc.code,
                error_message=exc.message,
            )
        except Exception:
            self.repository.fail(
                job_id,
                status=ArticleJobStatus.FAILED_VALIDATION,
                error_code=ErrorCode.INTERNAL_ERROR,
                error_message="Unexpected article workflow error.",
            )

    def get_job(self, job_id: str) -> ArticleJobResponse:
        job = self.repository.get(job_id)
        if job is None:
            raise AppError(
                ErrorCode.JOB_NOT_FOUND,
                "Article job was not found.",
                status_code=status.HTTP_404_NOT_FOUND,
                retryable=False,
            )

        return ArticleJobResponse(
            job_id=job.id,
            status=job.status,
            title=job.generated_title,
            wordpress_post_id=job.wordpress_post_id,
            wordpress_status="draft" if job.wordpress_post_id is not None else None,
            wordpress_edit_url=(
                self.wordpress_client.edit_url(job.wordpress_post_id)
                if job.wordpress_post_id is not None
                else None
            ),
            tool_status=self._tool_status_from_metadata(job.metadata_json),
            error=self._job_error(job.error_code, job.error_message),
        )

    def _persist_tool_status(
        self,
        job_id: str,
        research_context: ArticleResearchContext,
        route_decision: AgentRouteDecision,
    ) -> None:
        self.repository.update_metadata(
            job_id,
            {
                "tool_status": {
                    "research_tool_called": route_decision.use_research_tool,
                    "router_reason": route_decision.reason,
                    "router_rules": route_decision.matched_rules,
                    "provider": research_context.provider,
                    "query": research_context.query,
                    "result_count": len(research_context.results),
                    "error": research_context.error,
                }
            },
        )

    @staticmethod
    def _failed_status(exc: AppError) -> ArticleJobStatus:
        if exc.code in {ErrorCode.LLM_TIMEOUT, ErrorCode.LLM_INVALID_OUTPUT}:
            return ArticleJobStatus.FAILED_LLM
        if exc.code == ErrorCode.ARTICLE_VALIDATION_FAILED:
            return ArticleJobStatus.FAILED_VALIDATION
        if exc.code in {ErrorCode.WORDPRESS_UNAVAILABLE, ErrorCode.WORDPRESS_AUTH_FAILED}:
            return ArticleJobStatus.FAILED_WORDPRESS
        return ArticleJobStatus.FAILED_VALIDATION

    @staticmethod
    def _job_error(error_code: str | None, error_message: str | None) -> ArticleJobError | None:
        if error_code is None or error_message is None:
            return None

        retryable_codes = {
            ErrorCode.LLM_TIMEOUT,
            ErrorCode.LLM_INVALID_OUTPUT,
            ErrorCode.ARTICLE_VALIDATION_FAILED,
            ErrorCode.WORDPRESS_UNAVAILABLE,
        }
        return ArticleJobError(
            code=error_code,
            message=error_message,
            retryable=error_code in {code.value for code in retryable_codes},
        )

    @staticmethod
    def _tool_status_from_metadata(metadata_json: str | None) -> ArticleToolStatus | None:
        if not metadata_json:
            return None

        try:
            metadata = json.loads(metadata_json)
        except json.JSONDecodeError:
            return None

        if not isinstance(metadata, dict):
            return None

        tool_status = metadata.get("tool_status")
        if not isinstance(tool_status, dict):
            return None

        try:
            return ArticleToolStatus.model_validate(tool_status)
        except ValueError:
            return None
