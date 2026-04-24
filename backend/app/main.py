from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import settings
from .repositories import AutomationTaskRepository, DashboardRepository
from .routers.agent import build_agent_router
from .routers.dashboard import build_dashboard_router
from .services.automation import AutomationService
from .services.browser_worker import BrowserWorker
from .services.chat import ChatAgentService
from .services.document_ingest import DocumentIngestService
from .services.knowledge import KnowledgeService
from .services.rag import RAGService
from .services.vector_store import InMemoryVectorStore, PgVectorStore
from .state import LocalStateStore


@asynccontextmanager
async def lifespan(app: FastAPI):
    state_store = LocalStateStore(settings.state_file)
    dashboard_repository = DashboardRepository(state_store, settings)
    task_repository = AutomationTaskRepository()
    vector_store = (
        PgVectorStore(settings.pgvector_dsn)
        if settings.vector_store_backend == "pgvector"
        else InMemoryVectorStore(dashboard_repository.knowledge())
    )
    knowledge_service = KnowledgeService(vector_store)
    document_ingest_service = DocumentIngestService()
    rag_service = RAGService(vector_store)
    chat_service = ChatAgentService(rag_service, dashboard_repository)
    browser_worker = BrowserWorker(
        base_url=settings.boss_base_url,
        state_dir=settings.browser_state_dir,
        headless=settings.browser_headless,
    )
    automation_service = AutomationService(task_repository, dashboard_repository, browser_worker, settings)

    app.state.dashboard_repository = dashboard_repository
    app.state.rag_service = rag_service
    app.state.knowledge_service = knowledge_service
    app.state.document_ingest_service = document_ingest_service
    app.state.chat_service = chat_service
    app.state.automation_service = automation_service
    yield


app = FastAPI(title=settings.api_title, version="0.3.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": app.title, "vector_store_backend": settings.vector_store_backend}


state_store = LocalStateStore(settings.state_file)
dashboard_repository = DashboardRepository(state_store, settings)
vector_store = (
    PgVectorStore(settings.pgvector_dsn)
    if settings.vector_store_backend == "pgvector"
    else InMemoryVectorStore(dashboard_repository.knowledge())
)
knowledge_service = KnowledgeService(vector_store)
document_ingest_service = DocumentIngestService()
rag_service = RAGService(vector_store)
chat_service = ChatAgentService(rag_service, dashboard_repository)
browser_worker = BrowserWorker(
    base_url=settings.boss_base_url,
    state_dir=settings.browser_state_dir,
    headless=settings.browser_headless,
)
automation_service = AutomationService(AutomationTaskRepository(), dashboard_repository, browser_worker, settings)

app.include_router(build_dashboard_router(dashboard_repository))
app.include_router(
    build_agent_router(
        dashboard_repository,
        rag_service,
        knowledge_service,
        document_ingest_service,
        chat_service,
        automation_service,
    )
)
