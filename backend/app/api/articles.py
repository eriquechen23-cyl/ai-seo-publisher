from fastapi import APIRouter, BackgroundTasks, status

from app.core.config import get_settings
from app.repositories.article_job_repository import ArticleJobRepository
from app.schemas.article import (
    ArticleJobResponse,
    GenerateArticleAcceptedResponse,
    GenerateArticleRequest,
)
from app.services.article_validator import ArticleValidator
from app.services.article_agent_router import ArticleAgentRouter
from app.services.article_agent_pipeline import ArticleAgentPipeline
from app.services.article_research_tool import ArticleResearchTool
from app.services.article_workflow import ArticleWorkflowService
from app.services.llm_service import LLMService
from app.services.prompt_builder import PromptBuilder
from app.services.wordpress_client import WordPressClient


router = APIRouter(prefix="/articles", tags=["articles"])


def build_workflow_service() -> ArticleWorkflowService:
    settings = get_settings()
    repository = ArticleJobRepository(settings.database_url)
    prompt_builder = PromptBuilder()
    llm_service = LLMService(settings, prompt_builder)
    validator = ArticleValidator()
    agent_router = ArticleAgentRouter(settings.research_router_mode)
    research_tool = ArticleResearchTool(settings)
    agent_pipeline = ArticleAgentPipeline(
        llm_service=llm_service,
        validator=validator,
        research_tool=research_tool,
        agent_router=agent_router,
    )
    wordpress_client = WordPressClient(
        base_url=settings.wordpress_url,
        username=settings.wordpress_username,
        application_password=settings.wordpress_app_password,
    )
    return ArticleWorkflowService(
        repository=repository,
        llm_service=llm_service,
        validator=validator,
        wordpress_client=wordpress_client,
        agent_pipeline=agent_pipeline,
    )


@router.post(
    "/generate-publish",
    response_model=GenerateArticleAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def generate_and_publish(
    request: GenerateArticleRequest,
    background_tasks: BackgroundTasks,
) -> GenerateArticleAcceptedResponse:
    workflow = build_workflow_service()
    job_id = workflow.enqueue(request)
    background_tasks.add_task(workflow.process_job, job_id, request)
    return GenerateArticleAcceptedResponse(
        job_id=job_id,
        status="RECEIVED",
        status_url=f"/api/v1/articles/jobs/{job_id}",
    )


@router.get("/jobs/{job_id}", response_model=ArticleJobResponse)
async def get_article_job(job_id: str) -> ArticleJobResponse:
    workflow = build_workflow_service()
    return workflow.get_job(job_id)
