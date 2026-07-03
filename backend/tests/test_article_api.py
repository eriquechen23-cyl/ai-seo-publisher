from fastapi.testclient import TestClient

from app.api import articles
from app.main import app
from app.schemas.article import ArticleJobResponse


client = TestClient(app)


def test_generate_article_requires_keywords() -> None:
    response = client.post(
        "/api/v1/articles/generate-publish",
        json={
            "topic": "中小企業如何導入生成式 AI",
            "keywords": [],
            "target_audience": "台灣中小企業經營者",
            "call_to_action": "立即聯絡我們取得免費諮詢",
        },
    )

    assert response.status_code == 422


def test_generate_article_enqueues_background_job(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    class FakeWorkflow:
        def enqueue(self, request):  # type: ignore[no-untyped-def]
            return "job-123"

        async def process_job(self, job_id, request):  # type: ignore[no-untyped-def]
            return None

    monkeypatch.setattr(articles, "build_workflow_service", lambda: FakeWorkflow())

    response = client.post(
        "/api/v1/articles/generate-publish",
        json={
            "topic": "中小企業如何導入生成式 AI",
            "keywords": ["生成式 AI"],
            "target_audience": "台灣中小企業經營者",
            "call_to_action": "立即聯絡我們取得免費諮詢",
        },
    )

    assert response.status_code == 202
    assert response.json() == {
        "job_id": "job-123",
        "status": "RECEIVED",
        "status_url": "/api/v1/articles/jobs/job-123",
    }


def test_get_article_job_status(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    class FakeWorkflow:
        def get_job(self, job_id):  # type: ignore[no-untyped-def]
            return ArticleJobResponse(
                job_id=job_id,
                status="PUBLISHING",
                title=None,
                wordpress_post_id=None,
                wordpress_status=None,
                wordpress_edit_url=None,
                error=None,
            )

    monkeypatch.setattr(articles, "build_workflow_service", lambda: FakeWorkflow())

    response = client.get("/api/v1/articles/jobs/job-123")

    assert response.status_code == 200
    assert response.json()["status"] == "PUBLISHING"
