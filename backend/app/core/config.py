from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "AI SEO Publisher API"
    api_prefix: str = "/api/v1"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    database_url: str = "sqlite:///backend/demo.db"

    llm_mode: Literal["mock", "openai_compatible"] = "mock"
    llm_api_base: str = "https://api.openai.com/v1"
    llm_api_key: str = ""
    llm_model: str = "gpt-4o-mini"
    llm_timeout_seconds: int = 30

    research_mode: Literal["disabled", "mock", "brave", "duckduckgo"] = "duckduckgo"
    research_router_mode: Literal["auto", "always", "never"] = "auto"
    search_api_key: str = ""
    search_api_base: str = "https://api.search.brave.com/res/v1/web/search"
    duckduckgo_search_url: str = "https://html.duckduckgo.com/html/"
    search_result_count: int = 5
    search_timeout_seconds: int = 10

    wordpress_url: str = "http://localhost:8080"
    wordpress_username: str = "demo_admin"
    wordpress_app_password: str = ""

    model_config = SettingsConfigDict(
        env_file=BACKEND_ROOT / ".env",
        env_file_encoding="utf-8",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
