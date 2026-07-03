from typing import Any

import httpx
from fastapi import status

from app.core.exceptions import AppError, ErrorCode


class WordPressClient:
    def __init__(self, base_url: str, username: str, application_password: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.posts_url = f"{self.base_url}/wp-json/wp/v2/posts"
        self.auth = httpx.BasicAuth(username, application_password)

    async def create_draft(self, title: str, content_html: str) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(auth=self.auth, timeout=15) as client:
                response = await client.post(
                    self.posts_url,
                    json={"title": title, "content": content_html, "status": "draft"},
                )
        except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as exc:
            raise AppError(
                ErrorCode.WORDPRESS_UNAVAILABLE,
                "WordPress 站台暫時無法連線，請確認本機站台已啟動。",
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                retryable=True,
            ) from exc

        if response.status_code in {401, 403}:
            raise AppError(
                ErrorCode.WORDPRESS_AUTH_FAILED,
                "WordPress 驗證失敗，請確認使用者名稱與 Application Password。",
                status_code=status.HTTP_502_BAD_GATEWAY,
                retryable=False,
            )

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise AppError(
                ErrorCode.WORDPRESS_UNAVAILABLE,
                "WordPress 建立草稿失敗，請檢查 REST API 回應。",
                status_code=status.HTTP_502_BAD_GATEWAY,
                retryable=False,
                details={"status_code": response.status_code},
            ) from exc

        return response.json()

    def edit_url(self, post_id: int) -> str:
        return f"{self.base_url}/wp-admin/post.php?post={post_id}&action=edit"
