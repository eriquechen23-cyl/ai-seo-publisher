from pydantic import BaseModel, Field, field_validator


class LLMArticleOutput(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    content_html: str = Field(min_length=50)

    @field_validator("title", "content_html")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()


class ArticleValidationResult(BaseModel):
    passed: bool
    errors: list[str] = Field(default_factory=list)
    missing_keywords: list[str] = Field(default_factory=list)


class ArticleCritiqueResult(BaseModel):
    passed: bool
    summary: str = Field(min_length=1, max_length=1200)
    issues: list[str] = Field(default_factory=list, max_length=20)
    recommendations: list[str] = Field(default_factory=list, max_length=20)
    requires_revision: bool = False
