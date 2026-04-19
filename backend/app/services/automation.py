from __future__ import annotations

from datetime import datetime

from ..core.config import Settings
from ..repositories import DashboardRepository
from ..repositories import AutomationTaskRepository
from ..schemas import AutomationTask, AutomationTaskCreate
from .browser_worker import BrowserWorker


class AutomationService:
    def __init__(
        self,
        repository: AutomationTaskRepository,
        dashboard_repository: DashboardRepository,
        worker: BrowserWorker,
        settings: Settings,
    ) -> None:
        self._repository = repository
        self._dashboard_repository = dashboard_repository
        self._worker = worker
        self._settings = settings

    def create_task(self, request: AutomationTaskCreate) -> AutomationTask:
        result = self._run(request)
        return self._repository.create(request, result=result)

    def list_tasks(self) -> list[AutomationTask]:
        return self._repository.list()

    def get_task(self, task_id: str) -> AutomationTask | None:
        return self._repository.get(task_id)

    def worker_status(self) -> dict:
        status = self._worker.status()
        status["vector_store_backend"] = self._settings.vector_store_backend
        return status

    def _run(self, request: AutomationTaskCreate) -> dict:
        if request.task_type == "manual_login":
            result = self._worker.manual_login()
            self._dashboard_repository.set_login(result["login_status"], datetime.utcnow().isoformat())
            return result
        if request.task_type == "login_check":
            result = self._worker.login_check()
            self._dashboard_repository.set_login(result["login_status"], result.get("checked_at"))
            return result
        if request.task_type == "collect_jobs":
            keyword = request.payload.get("keyword", "前端")
            result = self._worker.collect_jobs(keyword)
            self._dashboard_repository.set_jobs(result.get("jobs", []))
            return result
        if request.task_type == "sync_messages":
            result = self._worker.sync_messages()
            self._dashboard_repository.set_messages(result.get("messages", []))
            return result
        if request.task_type == "send_message":
            return self._worker.send_message(request.payload)
        return {"refreshed_chunks": 5, "note": "当前使用知识库存储接口，后续可替换为 pgvector 实现。"}
