from app.schemas.article import GenerateArticleRequest
from app.schemas.llm import ArticleCritiqueResult, ArticleValidationResult, LLMArticleOutput
from app.schemas.research import ArticleResearchContext


class PromptBuilder:
    def build_messages(
        self,
        request: GenerateArticleRequest,
        research_context: ArticleResearchContext | None = None,
    ) -> list[dict[str, str]]:
        return [
            {"role": "system", "content": self._producer_system_prompt()},
            {"role": "user", "content": self._article_brief(request, research_context)},
        ]

    def build_critique_messages(
        self,
        request: GenerateArticleRequest,
        article: LLMArticleOutput,
        validation_result: ArticleValidationResult,
        research_context: ArticleResearchContext | None = None,
    ) -> list[dict[str, str]]:
        return [
            {"role": "system", "content": self._critic_system_prompt()},
            {"role": "user", "content": self._article_brief(request, research_context)},
            {"role": "assistant", "content": article.model_dump_json()},
            {
                "role": "user",
                "content": (
                    "Use the CRITIC pattern to review the producer output. Check SEO fit, keyword "
                    "coverage, HTML structure, target-audience usefulness, CTA strength, safety, "
                    "whether the draft is ready for WordPress publishing, and whether source-backed "
                    "claims are consistent with the provided research context.\n\n"
                    f"Deterministic validator result:\n{validation_result.model_dump_json()}\n\n"
                    "Return only JSON with this schema:\n"
                    "{\n"
                    '  "passed": true,\n'
                    '  "summary": "short critique summary",\n'
                    '  "issues": ["specific issue"],\n'
                    '  "recommendations": ["specific revision instruction"],\n'
                    '  "requires_revision": false\n'
                    "}"
                ),
            },
        ]

    def build_revision_messages(
        self,
        request: GenerateArticleRequest,
        previous_output: LLMArticleOutput,
        validation_result: ArticleValidationResult,
        critique_result: ArticleCritiqueResult,
        research_context: ArticleResearchContext | None = None,
    ) -> list[dict[str, str]]:
        validation_errors = "\n".join(f"- {error}" for error in validation_result.errors)
        missing_keywords = "\n".join(
            f"- Missing keyword: {keyword}" for keyword in validation_result.missing_keywords
        )
        critique_issues = "\n".join(f"- {issue}" for issue in critique_result.issues)
        critique_recommendations = "\n".join(
            f"- {recommendation}" for recommendation in critique_result.recommendations
        )
        return [
            {"role": "system", "content": self._producer_system_prompt()},
            {"role": "user", "content": self._article_brief(request, research_context)},
            {"role": "assistant", "content": previous_output.model_dump_json()},
            {
                "role": "user",
                "content": (
                    "Reflect on the validator result and CRITIQUE feedback, then revise the article. "
                    "Preserve the requested topic, audience, CTA, and all keywords. Return only the "
                    "same article JSON schema.\n\n"
                    f"Validation errors:\n{validation_errors or '- none'}\n"
                    f"Missing keywords:\n{missing_keywords or '- none'}\n"
                    f"Critic summary:\n{critique_result.summary}\n"
                    f"Critic issues:\n{critique_issues or '- none'}\n"
                    f"Critic recommendations:\n{critique_recommendations or '- none'}"
                ),
            },
        ]

    def build_repair_messages(
        self,
        request: GenerateArticleRequest,
        previous_output: LLMArticleOutput,
        validation_result: ArticleValidationResult,
        research_context: ArticleResearchContext | None = None,
    ) -> list[dict[str, str]]:
        critique_result = ArticleCritiqueResult(
            passed=validation_result.passed,
            summary="Rule-based validation found issues that must be repaired.",
            issues=validation_result.errors
            + [f"Missing keyword: {keyword}" for keyword in validation_result.missing_keywords],
            recommendations=[
                "Repair every deterministic validation issue.",
                "Keep the response in the article JSON schema.",
            ],
            requires_revision=not validation_result.passed,
        )
        return self.build_revision_messages(
            request=request,
            previous_output=previous_output,
            validation_result=validation_result,
            critique_result=critique_result,
            research_context=research_context,
        )

    @staticmethod
    def _producer_system_prompt() -> str:
        return """
You are the PRODUCER agent for an SEO article workflow.
Write useful, publication-ready WordPress article drafts.
Return JSON only. Do not wrap the JSON in Markdown.

JSON schema:
{
  "title": "article title",
  "content_html": "<h1>...</h1><h2>...</h2><p>...</p><ul><li>...</li></ul>"
}

Rules:
1. Include every requested keyword naturally.
2. Match the target audience and call to action.
3. Use valid article HTML with h1, h2, p, ul or ol, and li elements.
4. Do not include script, style, iframe, form, inline event handlers, or unsafe URLs.
5. Avoid Markdown and explanatory wrapper text.
""".strip()

    @staticmethod
    def _critic_system_prompt() -> str:
        return """
You are the CRITIQUE agent in a producer-critic article pipeline.
You do not rewrite the article. You decide whether the draft is ready to publish and produce
specific feedback the producer can act on.
Return JSON only.
""".strip()

    @staticmethod
    def _article_brief(
        request: GenerateArticleRequest,
        research_context: ArticleResearchContext | None = None,
    ) -> str:
        keywords = ", ".join(request.keywords)
        research_text = PromptBuilder._research_context_text(research_context)
        return f"""
Create a WordPress SEO article draft.

Topic: {request.topic}
Keywords: {keywords}
Target audience: {request.target_audience}
Call to action: {request.call_to_action}

Research context:
{research_text}
""".strip()

    @staticmethod
    def _research_context_text(research_context: ArticleResearchContext | None) -> str:
        if research_context is None:
            return "No external search context was provided."

        if research_context.error:
            return (
                f"Search provider: {research_context.provider}\n"
                f"Query: {research_context.query}\n"
                f"Search error: {research_context.error}\n"
                "Write without inventing source-backed facts."
            )

        if not research_context.results:
            return (
                f"Search provider: {research_context.provider}\n"
                f"Query: {research_context.query}\n"
                "No search results were returned. Write without inventing source-backed facts."
            )

        source_lines = [
            f"{index}. {result.title}\nURL: {result.url}\nSnippet: {result.snippet}"
            for index, result in enumerate(research_context.results, start=1)
        ]
        return (
            f"Search provider: {research_context.provider}\n"
            f"Query: {research_context.query}\n"
            "Search results:\n"
            + "\n".join(source_lines)
        )
