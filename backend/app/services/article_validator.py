import re

import bleach
from bs4 import BeautifulSoup

from app.schemas.llm import ArticleValidationResult, LLMArticleOutput


class ArticleValidator:
    allowed_tags = [
        "h1",
        "h2",
        "h3",
        "p",
        "ul",
        "ol",
        "li",
        "strong",
        "em",
        "a",
        "br",
    ]
    allowed_attributes = {"a": ["href", "title", "rel", "target"]}
    dangerous_patterns = [
        re.compile(r"<\s*(script|style|iframe|form)\b", re.IGNORECASE),
        re.compile(r"\son\w+\s*=", re.IGNORECASE),
        re.compile(r"javascript\s*:", re.IGNORECASE),
    ]

    def validate(self, article: LLMArticleOutput, keywords: list[str]) -> ArticleValidationResult:
        errors: list[str] = []
        missing_keywords: list[str] = []
        soup = BeautifulSoup(article.content_html, "html.parser")

        if not article.title:
            errors.append("標題不可空白")
        if not article.content_html:
            errors.append("content_html 不可空白")
        if len(article.content_html) < 200:
            errors.append("文章 HTML 長度過短")

        required_tags = ["h1", "h2", "p"]
        for tag_name in required_tags:
            if soup.find(tag_name) is None:
                errors.append(f"缺少 <{tag_name}> 結構")

        if soup.find("ul") is None and soup.find("ol") is None:
            errors.append("缺少 <ul> 或 <ol> 清單結構")
        if soup.find("li") is None:
            errors.append("缺少 <li> 清單項目")

        for pattern in self.dangerous_patterns:
            if pattern.search(article.content_html):
                errors.append("HTML 包含不安全標籤或屬性")
                break

        searchable = f"{article.title} {soup.get_text(' ')}".casefold()
        for keyword in keywords:
            if keyword.casefold() not in searchable:
                missing_keywords.append(keyword)

        if missing_keywords:
            errors.append("文章未包含所有指定關鍵字")

        return ArticleValidationResult(
            passed=not errors and not missing_keywords,
            errors=errors,
            missing_keywords=missing_keywords,
        )

    def sanitize(self, content_html: str) -> str:
        return bleach.clean(
            content_html,
            tags=self.allowed_tags,
            attributes=self.allowed_attributes,
            protocols=["http", "https", "mailto"],
            strip=True,
        )
