from dataclasses import dataclass, field
from typing import Literal

from app.schemas.article import GenerateArticleRequest


RouterMode = Literal["auto", "always", "never"]


@dataclass(frozen=True)
class AgentRouteDecision:
    use_research_tool: bool
    reason: str
    matched_rules: list[str] = field(default_factory=list)


class ArticleAgentRouter:
    """Rule-based router for deciding when the agent pipeline should call tools."""

    TIMELY_TERMS = {
        "最新",
        "近期",
        "趨勢",
        "新聞",
        "市場",
        "行情",
        "價格",
        "成本",
        "比較",
        "排名",
        "法規",
        "政策",
        "2024",
        "2025",
        "2026",
    }
    RESEARCH_TERMS = {
        "SEO",
        "搜尋",
        "Google",
        "WordPress",
        "REST API",
        "AI",
        "生成式 AI",
        "資安",
        "ESG",
        "金融",
        "醫療",
        "製造",
        "SaaS",
    }
    INTERNAL_ONLY_TERMS = {
        "內部",
        "公司內訓",
        "品牌語氣",
        "個人心得",
        "團隊公告",
        "會議紀錄",
    }

    def __init__(self, mode: RouterMode = "auto") -> None:
        self.mode = mode

    def route(self, request: GenerateArticleRequest) -> AgentRouteDecision:
        if self.mode == "always":
            return AgentRouteDecision(
                use_research_tool=True,
                reason="Router mode is always.",
                matched_rules=["mode:always"],
            )

        if self.mode == "never":
            return AgentRouteDecision(
                use_research_tool=False,
                reason="Router mode is never.",
                matched_rules=["mode:never"],
            )

        text = self._request_text(request)
        matched_rules: list[str] = []

        if self._contains_any(text, self.INTERNAL_ONLY_TERMS):
            matched_rules.append("content:internal_or_brand_specific")
            return AgentRouteDecision(
                use_research_tool=False,
                reason="The brief looks internal or brand-specific, so external search is unlikely to help.",
                matched_rules=matched_rules,
            )

        if self._contains_any(text, self.TIMELY_TERMS):
            matched_rules.append("content:timely_or_comparative")

        if self._contains_any(text, self.RESEARCH_TERMS):
            matched_rules.append("content:research_sensitive")

        if len(request.keywords) >= 3:
            matched_rules.append("keywords:multi_keyword_seo")

        if matched_rules:
            return AgentRouteDecision(
                use_research_tool=True,
                reason="The brief benefits from outside context before Producer and Critique run.",
                matched_rules=matched_rules,
            )

        return AgentRouteDecision(
            use_research_tool=False,
            reason="No rule indicated that external search is needed for this brief.",
            matched_rules=["default:no_tool"],
        )

    @staticmethod
    def _request_text(request: GenerateArticleRequest) -> str:
        return " ".join(
            [
                request.topic,
                " ".join(request.keywords),
                request.target_audience,
                request.call_to_action,
            ]
        )

    @staticmethod
    def _contains_any(text: str, terms: set[str]) -> bool:
        lower_text = text.lower()
        return any(term.lower() in lower_text for term in terms)
