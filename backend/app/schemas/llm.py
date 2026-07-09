from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator


CritiqueSummary = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1200)
]
CritiqueItem = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)
]


class LLMArticleOutput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

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
    model_config = ConfigDict(extra="forbid", strict=True)

    passed: bool
    summary: CritiqueSummary
    issues: list[CritiqueItem] = Field(max_length=20)
    recommendations: list[CritiqueItem] = Field(max_length=20)
    requires_revision: bool
