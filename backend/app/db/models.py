from dataclasses import dataclass

from app.schemas.article import ArticleJobStatus


@dataclass(frozen=True)
class ArticleJob:
    id: str
    status: ArticleJobStatus
    reflection_count: int
    generated_title: str | None = None
    generated_html: str | None = None
    wordpress_post_id: int | None = None
    error_code: str | None = None
    error_message: str | None = None
    metadata_json: str | None = None
