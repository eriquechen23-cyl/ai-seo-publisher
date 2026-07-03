from app.schemas.llm import LLMArticleOutput
from app.services.article_validator import ArticleValidator


def test_validator_accepts_valid_article() -> None:
    validator = ArticleValidator()
    article = LLMArticleOutput(
        title="生成式 AI 導入指南",
        content_html="""
        <h1>生成式 AI 導入指南</h1>
        <p>這篇文章說明中小企業如何規劃數位轉型。</p>
        <h2>重點</h2>
        <p>生成式 AI 可以協助內容、客服與營運流程。</p>
        <ul><li>生成式 AI</li><li>數位轉型</li><li>中小企業</li></ul>
        <p>立即聯絡我們取得免費諮詢。</p>
        """,
    )

    result = validator.validate(article, ["生成式 AI", "數位轉型", "中小企業"])

    assert result.passed is True


def test_validator_reports_missing_keyword_and_structure() -> None:
    validator = ArticleValidator()
    article = LLMArticleOutput(
        title="導入指南",
        content_html="<h1>導入指南</h1><p>這是一段足夠長但仍缺少必要結構與指定關鍵字的文章內容，用來測試 validator 可以回報問題。</p>",
    )

    result = validator.validate(article, ["生成式 AI"])

    assert result.passed is False
    assert "生成式 AI" in result.missing_keywords
    assert any("缺少 <h2>" in error for error in result.errors)


def test_sanitizer_removes_script() -> None:
    validator = ArticleValidator()

    cleaned = validator.sanitize("<h1>Title</h1><script>alert(1)</script><p>Safe</p>")

    assert "<script>" not in cleaned
    assert "alert(1)" in cleaned
