from __future__ import annotations

from datetime import datetime

from ..core.config import Settings
from ..repositories import AutomationTaskRepository, DashboardRepository
from ..schemas import AutomationTask, AutomationTaskCreate
from .browser_worker import BrowserWorker
from .memory import MemoryService


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
        self._memory = MemoryService()

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

    def _merge_messages(self, existing: list[dict], updates: list[dict]) -> list[dict]:
        merged: dict[str, dict] = {}
        for item in existing:
            key = item.get("conversation_id") or f"existing-{len(merged)}"
            merged[key] = item
        for item in updates:
            key = item.get("conversation_id") or f"update-{len(merged)}"
            previous = merged.get(key, {})
            merged[key] = {**previous, **item}
        return list(merged.values())

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
            snapshot = self._dashboard_repository.snapshot()
            keyword = request.payload.get("keyword", "前端")
            city = request.payload.get("city", "101010100")
            auto_apply_limit = int(request.payload.get("auto_apply_limit", 1) or 1)
            intro_message = str(request.payload.get("intro_message", "") or "")
            profile = snapshot.get("ai_config", {}).get("profile", {})

            result = self._worker.collect_jobs(
                keyword,
                city=city,
                auto_apply_limit=auto_apply_limit,
                intro_message=intro_message,
                profile=profile,
            )

            original_jobs = result.get("jobs", [])
            merged_messages = self._merge_messages(snapshot.get("messages", []), result.get("messages", []))
            self._dashboard_repository.set_messages(merged_messages)

            refreshed_snapshot = self._dashboard_repository.snapshot()
            memory_result = self._memory.sync(refreshed_snapshot, original_jobs, merged_messages)
            self._dashboard_repository.set_jobs(memory_result.jobs, keyword=result.get("keyword"), city=city)
            self._dashboard_repository.upsert_conversations(memory_result.conversations)
            self._dashboard_repository.upsert_interviews(memory_result.interviews)
            self._dashboard_repository.upsert_job_decisions(memory_result.job_decisions)
            self._dashboard_repository.add_knowledge(memory_result.knowledge_chunks)

            if result.get("login_status"):
                self._dashboard_repository.set_login(result["login_status"], datetime.utcnow().isoformat())

            result["jobs"] = memory_result.jobs
            result["skipped_jobs"] = max(0, len(original_jobs) - len(memory_result.jobs))
            result["conversation_memories"] = len(memory_result.conversations)
            result["interview_memories"] = len(memory_result.interviews)
            return result

        if request.task_type == "sync_messages":
            snapshot = self._dashboard_repository.snapshot()
            known_ids = [item.get("conversation_id") for item in snapshot.get("conversations", []) if item.get("conversation_id")]
            result = self._worker.sync_messages(known_conversation_ids=known_ids)
            merged_messages = self._merge_messages(snapshot.get("messages", []), result.get("messages", []))
            self._dashboard_repository.set_messages(merged_messages)

            refreshed_snapshot = self._dashboard_repository.snapshot()
            memory_result = self._memory.sync(refreshed_snapshot, refreshed_snapshot.get("jobs", []), merged_messages)
            self._dashboard_repository.upsert_conversations(memory_result.conversations)
            self._dashboard_repository.upsert_interviews(memory_result.interviews)
            self._dashboard_repository.upsert_job_decisions(memory_result.job_decisions)
            self._dashboard_repository.add_knowledge(memory_result.knowledge_chunks)

            if result.get("login_status"):
                self._dashboard_repository.set_login(result["login_status"], datetime.utcnow().isoformat())

            result["conversation_memories"] = len(memory_result.conversations)
            result["interview_memories"] = len(memory_result.interviews)
            return result

        if request.task_type == "send_message":
            return self._worker.send_message(request.payload)

        return {
            "refreshed_chunks": len(self._dashboard_repository.knowledge()),
            "note": "已根据当前本地知识库重新加载 RAG 数据。",
        }
