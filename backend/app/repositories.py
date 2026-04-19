from __future__ import annotations

from datetime import datetime
from threading import Lock
from uuid import uuid4

from .bootstrap import (
    seed_ai_config,
    seed_chat,
    seed_interviews,
    seed_jobs,
    seed_knowledge,
    seed_overview,
    seed_resume_lab,
)
from .schemas import (
    AIConfigResponse,
    AutomationTask,
    AutomationTaskCreate,
    ChatHistoryItem,
    ChatResponse,
    InterviewsResponse,
    JobCard,
    JobDetail,
    JobsResponse,
    KnowledgeChunk,
    OverviewResponse,
    PipelineItem,
    RecommendationItem,
    ResumeLabResponse,
)
from .state import LocalStateStore


class DashboardRepository:
    def __init__(self, state_store: LocalStateStore) -> None:
        self._store = state_store
        self._overview_seed = seed_overview()
        self._chat_seed = seed_chat()
        self._jobs_seed = seed_jobs()
        self._ai_config = seed_ai_config()
        self._interviews = seed_interviews()
        self._resume_lab = seed_resume_lab()
        self._knowledge_seed = seed_knowledge()

    def overview(self) -> OverviewResponse:
        snapshot = self._store.snapshot()
        jobs = snapshot.get("jobs", [])
        messages = snapshot.get("messages", [])
        login = snapshot.get("login", {})
        overview = self._overview_seed.model_copy(deep=True)

        overview.stats[0].value = str(len(jobs) or int(overview.stats[0].value.replace(",", "")))
        overview.stats[1].value = str(len(messages))

        if jobs:
            overview.pipeline = [
                PipelineItem(
                    company=job.get("company", "未知公司"),
                    role=job.get("role", "未知职位"),
                    salary=job.get("salary", "薪资待沟通"),
                    stage="已从 BOSS 实时抓取",
                    summary=job.get("summary", "需要打开详情确认"),
                    message=f"你好，我看了下 {job.get('role', '这个岗位')}，和我过往做的方向比较贴合，想进一步了解团队现在最看重的能力点。",
                )
                for job in jobs[:4]
            ]

        login_status = login.get("status", "unknown")
        if login_status == "logged_in":
            overview.hero.status = "BOSS 会话可用"
        elif login_status == "logged_out":
            overview.hero.status = "等待手动登录"
        else:
            overview.hero.status = "尚未检测登录状态"

        return overview

    def chat(self) -> ChatResponse:
        snapshot = self._store.snapshot()
        chat = self._chat_seed.model_copy(deep=True)
        messages = snapshot.get("messages", [])
        jobs = snapshot.get("jobs", [])

        if messages:
            chat.history = [
                ChatHistoryItem(
                    title=item.get("company", "BOSS 会话"),
                    preview=item.get("incoming", ""),
                    time=item.get("time", ""),
                    active=index == 0,
                )
                for index, item in enumerate(messages[:3])
            ]

        if jobs:
            chat.recommendations = [
                RecommendationItem(
                    title=job.get("role", "未知职位"),
                    company=f"{job.get('company', '未知公司')} · {job.get('location', '未知地点')}",
                    tags=job.get("tags", []),
                    score=job.get("score", 80),
                )
                for job in jobs[:4]
            ]

        return chat

    def jobs(self) -> JobsResponse:
        snapshot = self._store.snapshot()
        jobs_response = self._jobs_seed.model_copy(deep=True)
        runtime_jobs = snapshot.get("jobs", [])

        if runtime_jobs:
            jobs_response.summary.count = str(len(runtime_jobs))
            jobs_response.jobs = [
                JobCard(
                    company=job.get("company", "未知公司"),
                    role=job.get("role", "未知职位"),
                    salary=job.get("salary", "薪资待沟通"),
                    location=job.get("location", "未知地点"),
                    tags=job.get("tags", []),
                    summary=job.get("summary", "需要打开职位详情查看"),
                    score=job.get("score", 80),
                )
                for job in runtime_jobs[:12]
            ]
            first = runtime_jobs[0]
            jobs_response.detail = JobDetail(
                role=first.get("role", "未知职位"),
                company=first.get("company", "未知公司"),
                salary=first.get("salary", "薪资待沟通"),
                meta=[first.get("location", "未知地点"), "经验待确认", "学历待确认", "全职"],
                description=[first.get("summary", "需要打开职位详情查看")],
            )

        return jobs_response

    def ai_config(self) -> AIConfigResponse:
        return self._ai_config

    def interviews(self) -> InterviewsResponse:
        return self._interviews

    def resume_lab(self) -> ResumeLabResponse:
        return self._resume_lab

    def knowledge(self) -> list[KnowledgeChunk]:
        snapshot = self._store.snapshot()
        runtime_chunks = [KnowledgeChunk(**item) for item in snapshot.get("knowledge", [])]
        return self._knowledge_seed + runtime_chunks

    def set_jobs(self, jobs: list[dict]) -> None:
        self._store.set_jobs(jobs)

    def set_messages(self, messages: list[dict]) -> None:
        self._store.set_messages(messages)

    def set_login(self, status: str, last_checked: str | None) -> None:
        self._store.set_login(status, last_checked)

    def add_knowledge(self, chunks: list[KnowledgeChunk]) -> None:
        self._store.upsert_knowledge([chunk.model_dump() for chunk in chunks])


class AutomationTaskRepository:
    def __init__(self) -> None:
        self._tasks: list[AutomationTask] = []
        self._lock = Lock()

    def list(self) -> list[AutomationTask]:
        with self._lock:
            return list(reversed(self._tasks))

    def get(self, task_id: str) -> AutomationTask | None:
        with self._lock:
            for task in self._tasks:
                if task.id == task_id:
                    return task
        return None

    def create(self, request: AutomationTaskCreate, result: dict | None = None) -> AutomationTask:
        now = datetime.utcnow()
        task = AutomationTask(
            id=uuid4().hex[:12],
            task_type=request.task_type,
            status="completed",
            created_at=now,
            updated_at=now,
            payload=request.payload,
            result=result or {},
        )
        with self._lock:
            self._tasks.append(task)
        return task
