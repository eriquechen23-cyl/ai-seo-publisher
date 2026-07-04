import json
import uuid
from typing import Any
from datetime import UTC, datetime

from app.db.database import connect, init_db
from app.db.models import ArticleJob
from app.schemas.article import ArticleJobStatus, GenerateArticleRequest


class ArticleJobRepository:
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url
        init_db(database_url)

    def create(self, request: GenerateArticleRequest) -> ArticleJob:
        job_id = str(uuid.uuid4())
        now = self._now()
        with connect(self.database_url) as connection:
            connection.execute(
                """
                INSERT INTO article_jobs (
                    id, topic, keywords_json, target_audience, call_to_action,
                    status, reflection_count, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job_id,
                    request.topic,
                    json.dumps(request.keywords, ensure_ascii=False),
                    request.target_audience,
                    request.call_to_action,
                    ArticleJobStatus.RECEIVED,
                    0,
                    now,
                    now,
                ),
            )
            connection.commit()
        return ArticleJob(id=job_id, status=ArticleJobStatus.RECEIVED, reflection_count=0)

    def get(self, job_id: str) -> ArticleJob | None:
        with connect(self.database_url) as connection:
            row = connection.execute(
                """
                SELECT id, status, reflection_count, generated_title, generated_html,
                       wordpress_post_id, error_code, error_message, metadata_json
                FROM article_jobs
                WHERE id = ?
                """,
                (job_id,),
            ).fetchone()

        if row is None:
            return None

        return ArticleJob(
            id=row["id"],
            status=ArticleJobStatus(row["status"]),
            reflection_count=row["reflection_count"],
            generated_title=row["generated_title"],
            generated_html=row["generated_html"],
            wordpress_post_id=row["wordpress_post_id"],
            error_code=row["error_code"],
            error_message=row["error_message"],
            metadata_json=row["metadata_json"],
        )

    def update_status(self, job_id: str, status: ArticleJobStatus) -> None:
        with connect(self.database_url) as connection:
            connection.execute(
                "UPDATE article_jobs SET status = ?, updated_at = ? WHERE id = ?",
                (status, self._now(), job_id),
            )
            connection.commit()

    def mark_repairing(self, job_id: str) -> None:
        with connect(self.database_url) as connection:
            connection.execute(
                """
                UPDATE article_jobs
                SET status = ?, reflection_count = reflection_count + 1, updated_at = ?
                WHERE id = ?
                """,
                (ArticleJobStatus.REPAIRING, self._now(), job_id),
            )
            connection.commit()

    def update_metadata(self, job_id: str, metadata: dict[str, Any]) -> None:
        job = self.get(job_id)
        current_metadata = self._decode_metadata(job.metadata_json if job else None)
        current_metadata.update(metadata)

        with connect(self.database_url) as connection:
            connection.execute(
                """
                UPDATE article_jobs
                SET metadata_json = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    json.dumps(current_metadata, ensure_ascii=False),
                    self._now(),
                    job_id,
                ),
            )
            connection.commit()

    def complete(
        self,
        job_id: str,
        *,
        generated_title: str,
        generated_html: str,
        wordpress_post_id: int,
    ) -> None:
        with connect(self.database_url) as connection:
            connection.execute(
                """
                UPDATE article_jobs
                SET status = ?,
                    generated_title = ?,
                    generated_html = ?,
                    wordpress_post_id = ?,
                    error_code = NULL,
                    error_message = NULL,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    ArticleJobStatus.COMPLETED,
                    generated_title,
                    generated_html,
                    wordpress_post_id,
                    self._now(),
                    job_id,
                ),
            )
            connection.commit()

    def fail(
        self,
        job_id: str,
        *,
        status: ArticleJobStatus,
        error_code: str,
        error_message: str,
    ) -> None:
        with connect(self.database_url) as connection:
            connection.execute(
                """
                UPDATE article_jobs
                SET status = ?, error_code = ?, error_message = ?, updated_at = ?
                WHERE id = ?
                """,
                (status, error_code, error_message, self._now(), job_id),
            )
            connection.commit()

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).isoformat()

    @staticmethod
    def _decode_metadata(metadata_json: str | None) -> dict[str, Any]:
        if not metadata_json:
            return {}

        try:
            metadata = json.loads(metadata_json)
        except json.JSONDecodeError:
            return {}

        return metadata if isinstance(metadata, dict) else {}
