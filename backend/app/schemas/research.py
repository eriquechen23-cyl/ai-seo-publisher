from pydantic import BaseModel, Field, HttpUrl


class SearchResult(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    url: HttpUrl | str
    snippet: str = Field(default="", max_length=1000)


class ArticleResearchContext(BaseModel):
    query: str
    results: list[SearchResult] = Field(default_factory=list)
    provider: str = "none"
    error: str | None = None

    @property
    def has_results(self) -> bool:
        return bool(self.results)
