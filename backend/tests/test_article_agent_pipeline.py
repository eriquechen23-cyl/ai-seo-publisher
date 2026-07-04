import pytest

from app.schemas.article import GenerateArticleRequest
from app.schemas.llm import ArticleCritiqueResult, ArticleValidationResult, LLMArticleOutput
from app.schemas.research import ArticleResearchContext, SearchResult
from app.services.article_agent_pipeline import ArticleAgentPipeline
from app.services.article_agent_router import ArticleAgentRouter
from app.services.article_validator import ArticleValidator


def _request() -> GenerateArticleRequest:
    return GenerateArticleRequest(
        topic="AI content workflow",
        keywords=["producer critic", "SEO draft"],
        target_audience="content marketing teams",
        call_to_action="Book a workflow review.",
    )


def _article(label: str) -> LLMArticleOutput:
    return LLMArticleOutput(
        title=f"{label} producer critic SEO draft",
        content_html=f"""
<h1>{label} producer critic SEO draft</h1>
<p>This article explains an AI content workflow for content marketing teams and includes producer critic plus SEO draft context for the reader.</p>
<h2>Why the workflow matters</h2>
<p>The process helps teams draft, review, and improve content before publishing. It keeps search intent, audience needs, and editorial quality visible during generation.</p>
<h2>Checklist</h2>
<ul><li>producer critic</li><li>SEO draft</li><li>Book a workflow review.</li></ul>
<p>Book a workflow review to improve the publishing pipeline.</p>
""".strip(),
    )


@pytest.mark.asyncio
async def test_pipeline_accepts_article_without_reflection() -> None:
    class FakeLLM:
        def __init__(self) -> None:
            self.revise_count = 0
            self.research_provider: str | None = None

        async def generate_article(self, request, research_context=None):  # type: ignore[no-untyped-def]
            self.research_provider = research_context.provider
            return _article("Initial")

        async def critique_article(  # type: ignore[no-untyped-def]
            self,
            request,
            article,
            validation_result: ArticleValidationResult,
            research_context=None,
        ):
            return ArticleCritiqueResult(
                passed=validation_result.passed,
                summary="Ready to publish.",
                issues=[],
                recommendations=[],
                requires_revision=False,
            )

        async def revise_article(self, **kwargs):  # type: ignore[no-untyped-def]
            self.revise_count += 1
            return _article("Unexpected")

    fake_llm = FakeLLM()
    validations: list[str] = []
    reflections: list[str] = []
    pipeline = ArticleAgentPipeline(
        llm_service=fake_llm,  # type: ignore[arg-type]
        validator=ArticleValidator(),
    )

    result = await pipeline.run(
        _request(),
        on_validating=lambda: validations.append("validating"),
        on_reflection=lambda: reflections.append("reflection"),
    )

    assert result.reflection_count == 0
    assert result.validation.passed is True
    assert result.critique.passed is True
    assert fake_llm.revise_count == 0
    assert result.research_context.provider == "none"
    assert fake_llm.research_provider == "none"
    assert validations == ["validating"]
    assert reflections == []


@pytest.mark.asyncio
async def test_pipeline_revises_when_critic_requires_revision() -> None:
    class FakeLLM:
        def __init__(self) -> None:
            self.critique_count = 0
            self.revise_count = 0

        async def generate_article(self, request, research_context=None):  # type: ignore[no-untyped-def]
            return _article("Initial")

        async def critique_article(  # type: ignore[no-untyped-def]
            self,
            request,
            article,
            validation_result: ArticleValidationResult,
            research_context=None,
        ):
            self.critique_count += 1
            if self.critique_count == 1:
                return ArticleCritiqueResult(
                    passed=False,
                    summary="CTA is too weak.",
                    issues=["CTA needs a more concrete next step."],
                    recommendations=["Make the CTA explicit and action-oriented."],
                    requires_revision=True,
                )
            return ArticleCritiqueResult(
                passed=True,
                summary="Revised article is ready.",
                issues=[],
                recommendations=[],
                requires_revision=False,
            )

        async def revise_article(self, **kwargs):  # type: ignore[no-untyped-def]
            self.revise_count += 1
            return _article("Revised")

    fake_llm = FakeLLM()
    validations: list[str] = []
    reflections: list[str] = []
    pipeline = ArticleAgentPipeline(
        llm_service=fake_llm,  # type: ignore[arg-type]
        validator=ArticleValidator(),
    )

    result = await pipeline.run(
        _request(),
        on_validating=lambda: validations.append("validating"),
        on_reflection=lambda: reflections.append("reflection"),
    )

    assert result.article.title.startswith("Revised")
    assert result.reflection_count == 1
    assert fake_llm.critique_count == 2
    assert fake_llm.revise_count == 1
    assert validations == ["validating", "validating"]
    assert reflections == ["reflection"]


@pytest.mark.asyncio
async def test_pipeline_passes_search_context_to_agents() -> None:
    class FakeResearchTool:
        async def research(self, request):  # type: ignore[no-untyped-def]
            return ArticleResearchContext(
                query=request.topic,
                provider="fake-search",
                results=[
                    SearchResult(
                        title="Research result",
                        url="https://example.com/source",
                        snippet="Useful context for the article.",
                    )
                ],
            )

    class FakeLLM:
        def __init__(self) -> None:
            self.generate_provider: str | None = None
            self.critique_provider: str | None = None

        async def generate_article(self, request, research_context=None):  # type: ignore[no-untyped-def]
            self.generate_provider = research_context.provider
            return _article("Initial")

        async def critique_article(  # type: ignore[no-untyped-def]
            self,
            request,
            article,
            validation_result: ArticleValidationResult,
            research_context=None,
        ):
            self.critique_provider = research_context.provider
            return ArticleCritiqueResult(
                passed=validation_result.passed,
                summary="Ready with research context.",
                issues=[],
                recommendations=[],
                requires_revision=False,
            )

        async def revise_article(self, **kwargs):  # type: ignore[no-untyped-def]
            return _article("Unexpected")

    fake_llm = FakeLLM()
    pipeline = ArticleAgentPipeline(
        llm_service=fake_llm,  # type: ignore[arg-type]
        validator=ArticleValidator(),
        research_tool=FakeResearchTool(),  # type: ignore[arg-type]
    )

    result = await pipeline.run(_request())

    assert result.research_context.provider == "fake-search"
    assert result.research_context.results[0].title == "Research result"
    assert fake_llm.generate_provider == "fake-search"
    assert fake_llm.critique_provider == "fake-search"


@pytest.mark.asyncio
async def test_pipeline_skips_search_when_router_says_no() -> None:
    class FakeResearchTool:
        def __init__(self) -> None:
            self.called = False

        def build_query(self, request):  # type: ignore[no-untyped-def]
            return request.topic

        async def research(self, request):  # type: ignore[no-untyped-def]
            self.called = True
            return ArticleResearchContext(query=request.topic, provider="unexpected")

    class FakeLLM:
        def __init__(self) -> None:
            self.generate_provider: str | None = None
            self.critique_provider: str | None = None

        async def generate_article(self, request, research_context=None):  # type: ignore[no-untyped-def]
            self.generate_provider = research_context.provider
            return _article("Initial")

        async def critique_article(  # type: ignore[no-untyped-def]
            self,
            request,
            article,
            validation_result: ArticleValidationResult,
            research_context=None,
        ):
            self.critique_provider = research_context.provider
            return ArticleCritiqueResult(
                passed=validation_result.passed,
                summary="Ready without external search.",
                issues=[],
                recommendations=[],
                requires_revision=False,
            )

        async def revise_article(self, **kwargs):  # type: ignore[no-untyped-def]
            return _article("Unexpected")

    fake_llm = FakeLLM()
    fake_research_tool = FakeResearchTool()
    pipeline = ArticleAgentPipeline(
        llm_service=fake_llm,  # type: ignore[arg-type]
        validator=ArticleValidator(),
        research_tool=fake_research_tool,  # type: ignore[arg-type]
        agent_router=ArticleAgentRouter(mode="never"),
    )

    result = await pipeline.run(_request())

    assert fake_research_tool.called is False
    assert result.research_context.provider == "router-skip"
    assert result.research_context.error is not None
    assert fake_llm.generate_provider == "router-skip"
    assert fake_llm.critique_provider == "router-skip"
