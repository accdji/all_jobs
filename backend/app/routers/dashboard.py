from __future__ import annotations

from fastapi import APIRouter

from ..repositories import DashboardRepository
from ..schemas import AIConfigResponse, AIConfigUpdateRequest, ChatResponse, InterviewsResponse, JobsResponse, OverviewResponse, ResumeLabResponse


def build_dashboard_router(repository: DashboardRepository) -> APIRouter:
    router = APIRouter(prefix="/api", tags=["dashboard"])

    @router.get("/overview", response_model=OverviewResponse)
    def get_overview() -> OverviewResponse:
        return repository.overview()

    @router.get("/chat", response_model=ChatResponse)
    def get_chat() -> ChatResponse:
        return repository.chat()

    @router.get("/jobs", response_model=JobsResponse)
    def get_jobs() -> JobsResponse:
        return repository.jobs()

    @router.get("/ai-config", response_model=AIConfigResponse)
    def get_ai_config() -> AIConfigResponse:
        return repository.ai_config()

    @router.put("/ai-config", response_model=AIConfigResponse)
    def update_ai_config(request: AIConfigUpdateRequest) -> AIConfigResponse:
        repository.set_ai_config(
            api_key=request.api_key,
            provider=request.provider,
            base_url=request.base_url,
            model=request.model,
            profile=request.profile,
            subscriptions=request.subscriptions,
        )
        return repository.ai_config()

    @router.get("/interviews", response_model=InterviewsResponse)
    def get_interviews() -> InterviewsResponse:
        return repository.interviews()

    @router.get("/resume-lab", response_model=ResumeLabResponse)
    def get_resume_lab() -> ResumeLabResponse:
        return repository.resume_lab()

    return router
