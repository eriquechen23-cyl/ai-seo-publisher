from enum import StrEnum

from pydantic import BaseModel, Field, HttpUrl, field_validator


class ArticleJobStatus(StrEnum):
    RECEIVED = "RECEIVED"
    GENERATING = "GENERATING"
    VALIDATING = "VALIDATING"
    REPAIRING = "REPAIRING"
    PUBLISHING = "PUBLISHING"
    COMPLETED = "COMPLETED"
    FAILED_LLM = "FAILED_LLM"
    FAILED_VALIDATION = "FAILED_VALIDATION"
    FAILED_WORDPRESS = "FAILED_WORDPRESS"


class GenerateArticleRequest(BaseModel):
    topic: str = Field(min_length=3, max_length=200)
    keywords: list[str] = Field(min_length=1, max_length=10)
    target_audience: str = Field(min_length=2, max_length=200)
    call_to_action: str = Field(min_length=2, max_length=300)

    @field_validator("topic", "target_audience", "call_to_action")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("欄位不可空白")
        return value

    @field_validator("keywords")
    @classmethod
    def validate_keywords(cls, value: list[str]) -> list[str]:
        keywords = [item.strip() for item in value if item.strip()]
        if not keywords:
            raise ValueError("至少需要一個關鍵字")
        return list(dict.fromkeys(keywords))


class GenerateArticleAcceptedResponse(BaseModel):
    job_id: str
    status: ArticleJobStatus
    status_url: str


class ArticleJobError(BaseModel):
    code: str
    message: str
    retryable: bool


class ArticleJobResponse(BaseModel):
    job_id: str
    status: ArticleJobStatus
    title: str | None = None
    wordpress_post_id: int | None = None
    wordpress_status: str | None = None
    wordpress_edit_url: HttpUrl | str | None = None
    error: ArticleJobError | None = None
