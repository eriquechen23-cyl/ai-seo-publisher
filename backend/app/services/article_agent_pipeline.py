from collections.abc import Callable
from dataclasses import dataclass

from fastapi import status

from app.core.exceptions import AppError, ErrorCode
from app.schemas.article import GenerateArticleRequest
from app.schemas.llm import ArticleCritiqueResult, ArticleValidationResult, LLMArticleOutput
from app.schemas.research import ArticleResearchContext
from app.services.article_agent_router import AgentRouteDecision, ArticleAgentRouter
from app.services.article_research_tool import ArticleResearchTool
from app.services.article_validator import ArticleValidator
from app.services.llm_service import LLMService


StatusCallback = Callable[[], None]
ResearchCallback = Callable[[ArticleResearchContext, AgentRouteDecision], None]


@dataclass(frozen=True)
class ArticleAgentPipelineResult:
    article: LLMArticleOutput
    validation: ArticleValidationResult
    critique: ArticleCritiqueResult
    reflection_count: int
    research_context: ArticleResearchContext
    route_decision: AgentRouteDecision


class ArticleAgentPipeline:
    def __init__(
        self,
        *,
        llm_service: LLMService,
        validator: ArticleValidator,
        research_tool: ArticleResearchTool | None = None,
        agent_router: ArticleAgentRouter | None = None,
        max_reflections: int = 1,
    ) -> None:
        self.llm_service = llm_service
        self.validator = validator
        self.research_tool = research_tool
        self.agent_router = agent_router or ArticleAgentRouter(mode="always")
        self.max_reflections = max_reflections

    async def run(
        self,
        request: GenerateArticleRequest,
        *,
        on_validating: StatusCallback | None = None,
        on_reflection: StatusCallback | None = None,
        on_research_complete: ResearchCallback | None = None,
    ) -> ArticleAgentPipelineResult:
        research_context, route_decision = await self._research(request)
        self._notify_research(on_research_complete, research_context, route_decision)
        article = await self.llm_service.generate_article(
            request,
            research_context=research_context,
        )
        reflection_count = 0

        while True:
            self._notify(on_validating)
            validation = self.validator.validate(article, request.keywords)
            critique = await self.llm_service.critique_article(
                request=request,
                article=article,
                validation_result=validation,
                research_context=research_context,
            )

            if self._is_publishable(validation, critique):
                return ArticleAgentPipelineResult(
                    article=article,
                    validation=validation,
                    critique=critique,
                    reflection_count=reflection_count,
                    research_context=research_context,
                    route_decision=route_decision,
                )

            if reflection_count >= self.max_reflections:
                raise AppError(
                    ErrorCode.ARTICLE_VALIDATION_FAILED,
                    "Article did not pass producer-critic reflection.",
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    retryable=True,
                    details={
                        "validation": validation.model_dump(),
                        "critique": critique.model_dump(),
                        "reflection_count": reflection_count,
                    },
                )

            self._notify(on_reflection)
            reflection_count += 1
            article = await self.llm_service.revise_article(
                request=request,
                previous_output=article,
                validation_result=validation,
                critique_result=critique,
                research_context=research_context,
            )

    async def _research(
        self,
        request: GenerateArticleRequest,
    ) -> tuple[ArticleResearchContext, AgentRouteDecision]:
        if self.research_tool is None:
            decision = AgentRouteDecision(
                use_research_tool=False,
                reason="No research tool is configured.",
                matched_rules=["tool:none"],
            )
            return ArticleResearchContext(query="", provider="none"), decision

        decision = self.agent_router.route(request)
        if not decision.use_research_tool:
            return (
                ArticleResearchContext(
                    query=self.research_tool.build_query(request),
                    provider="router-skip",
                    error=f"{decision.reason} Matched rules: {', '.join(decision.matched_rules)}",
                ),
                decision,
            )

        return await self.research_tool.research(request), decision

    @staticmethod
    def _is_publishable(
        validation: ArticleValidationResult,
        critique: ArticleCritiqueResult,
    ) -> bool:
        return validation.passed and critique.passed and not critique.requires_revision

    @staticmethod
    def _notify(callback: StatusCallback | None) -> None:
        if callback is not None:
            callback()

    @staticmethod
    def _notify_research(
        callback: ResearchCallback | None,
        research_context: ArticleResearchContext,
        route_decision: AgentRouteDecision,
    ) -> None:
        if callback is not None:
            callback(research_context, route_decision)
