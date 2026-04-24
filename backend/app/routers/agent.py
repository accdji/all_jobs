from __future__ import annotations

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from ..repositories import DashboardRepository
from ..schemas import (
    AutomationTask,
    AutomationTaskCreate,
    ChatReplyRequest,
    ChatReplyResponse,
    KnowledgeIngestRequest,
    KnowledgeUploadResponse,
    RAGSearchRequest,
    RAGSearchResponse,
)
from ..services.automation import AutomationService
from ..services.chat import ChatAgentService
from ..services.document_ingest import DocumentIngestService
from ..services.knowledge import KnowledgeService
from ..services.rag import RAGService


def build_agent_router(
    dashboard_repository: DashboardRepository,
    rag_service: RAGService,
    knowledge_service: KnowledgeService,
    document_ingest_service: DocumentIngestService,
    chat_service: ChatAgentService,
    automation_service: AutomationService,
) -> APIRouter:
    router = APIRouter(prefix="/api", tags=["agent"])

    @router.post("/rag/search", response_model=RAGSearchResponse)
    def search_knowledge(request: RAGSearchRequest) -> RAGSearchResponse:
        return RAGSearchResponse(query=request.query, results=rag_service.search(request.query, request.top_k))

    @router.post("/rag/ingest")
    def ingest_knowledge(request: KnowledgeIngestRequest) -> dict:
        dashboard_repository.add_knowledge(request.chunks)
        return knowledge_service.ingest(request.chunks)

    @router.post("/rag/upload", response_model=KnowledgeUploadResponse)
    async def upload_knowledge_file(
        file: UploadFile = File(...),
        kind: str = Form("resume"),
        title: str | None = Form(None),
        tags: str = Form(""),
    ) -> KnowledgeUploadResponse:
        parsed_tags = [item.strip() for item in tags.split(",") if item.strip()]
        chunks, response = await document_ingest_service.convert_upload(
            file,
            kind=kind,
            title=title,
            tags=parsed_tags,
        )
        dashboard_repository.add_knowledge(chunks)
        knowledge_service.ingest_chunks(chunks, source="markitdown")
        return response

    @router.post("/chat/reply", response_model=ChatReplyResponse)
    def generate_chat_reply(request: ChatReplyRequest) -> ChatReplyResponse:
        return chat_service.generate_reply(request.message)

    @router.get("/automation/worker")
    def get_worker_status() -> dict:
        return automation_service.worker_status()

    @router.get("/automation/tasks", response_model=list[AutomationTask])
    def list_tasks() -> list[AutomationTask]:
        return automation_service.list_tasks()

    @router.post("/automation/tasks", response_model=AutomationTask)
    def create_task(request: AutomationTaskCreate) -> AutomationTask:
        return automation_service.create_task(request)

    @router.get("/automation/tasks/{task_id}", response_model=AutomationTask)
    def get_task(task_id: str) -> AutomationTask:
        task = automation_service.get_task(task_id)
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")
        return task

    return router
