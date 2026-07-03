import httpx
import pytest

from app.core.exceptions import AppError, ErrorCode
from app.services.wordpress_client import WordPressClient


@pytest.mark.asyncio
async def test_wordpress_auth_error(monkeypatch: pytest.MonkeyPatch) -> None:
    client = WordPressClient("http://localhost:8080", "demo", "bad")

    async def fake_post(*args, **kwargs):  # type: ignore[no-untyped-def]
        return httpx.Response(401, json={"code": "rest_cannot_create"})

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)

    with pytest.raises(AppError) as exc:
        await client.create_draft("Title", "<h1>Title</h1>")

    assert exc.value.code == ErrorCode.WORDPRESS_AUTH_FAILED
