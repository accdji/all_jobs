from __future__ import annotations

from datetime import datetime
from threading import Lock
from uuid import uuid4

from .core.config import Settings
from .core.env import upsert_env_value
from .schemas import (
    AIConfigModelOption,
    AIConfigResponse,
    AIKnowledgeFile,
    AIProfileSettings,
    AIProviderOption,
    AISubscriptionItem,
    AutomationTask,
    AutomationTaskCreate,
    ChatHistoryItem,
    ChatMessage,
    ChatResponse,
    ConversationMemory,
    HeroBlock,
    InterviewBoard,
    InterviewCard,
    InterviewMemory,
    InterviewsResponse,
    JobCard,
    JobDetail,
    JobsResponse,
    JobSummary,
    JobDecisionMemory,
    KnowledgeChunk,
    ModelOption,
    OverviewResponse,
    PipelineItem,
    PitchVariant,
    PushOption,
    RadarSummary,
    RecommendationItem,
    ResumeLabResponse,
    ResumeVariant,
    RuntimeStatus,
    StatBlock,
    ThreadItem,
    ToggleOption,
    UpcomingInterview,
)
from .state import LocalStateStore


class DashboardRepository:
    def __init__(self, state_store: LocalStateStore, settings: Settings) -> None:
        self._store = state_store
        self._settings = settings

    def overview(self) -> OverviewResponse:
        snapshot = self._store.snapshot()
        jobs = snapshot.get("jobs", [])
        messages = snapshot.get("messages", [])
        knowledge = self._knowledge_chunks(snapshot)
        login = snapshot.get("login", {})

        return OverviewResponse(
            hero=HeroBlock(
                title="求职自动化概览",
                subtitle="所有数据均来自当前本地登录态、BOSS 实时抓取结果和本地 RAG 知识库。",
                status=self._login_status_label(login.get("status", "unknown")),
            ),
            stats=[
                StatBlock(label="已扫描职位", value=str(len(jobs)), delta=self._job_delta(snapshot)),
                StatBlock(label="同步会话数", value=str(len(messages)), delta=self._message_delta(snapshot)),
                StatBlock(label="面试邀约数", value=str(len(self._derive_interview_cards(messages))), delta="实时识别"),
                StatBlock(label="知识片段数", value=str(len(knowledge)), delta="本地 RAG"),
            ],
            pipeline=[
                PipelineItem(
                    company=job.get("company") or "未知公司",
                    role=job.get("role") or "未知职位",
                    salary=job.get("salary") or "",
                    stage=self._job_stage(job),
                    summary=job.get("summary") or "",
                    message=job.get("latest_message") or "",
                )
                for job in jobs[:4]
            ],
            threads=[
                ThreadItem(
                    company=item.get("company") or "未知会话",
                    time=item.get("time") or "",
                    incoming=item.get("incoming") or "",
                    reply=item.get("reply") or "",
                )
                for item in messages[:4]
            ],
            insight=self._build_insight(snapshot),
        )

    def chat(self) -> ChatResponse:
        snapshot = self._store.snapshot()
        messages = snapshot.get("messages", [])
        jobs = snapshot.get("jobs", [])
        knowledge = self._knowledge_chunks(snapshot)

        history = [
            ChatHistoryItem(
                title=item.get("company") or "未知会话",
                preview=(item.get("incoming") or "")[:80],
                time=item.get("time") or "",
                active=index == 0,
            )
            for index, item in enumerate(messages[:8])
        ]

        current_thread = messages[0] if messages else {}
        conversation_messages: list[ChatMessage] = []
        if current_thread.get("incoming"):
            conversation_messages.append(
                ChatMessage(
                    speaker="user",
                    content=current_thread["incoming"],
                    time=current_thread.get("time") or "",
                )
            )
        if current_thread.get("reply"):
            conversation_messages.append(
                ChatMessage(
                    speaker="assistant",
                    content=current_thread["reply"],
                    time=current_thread.get("reply_time") or current_thread.get("time") or "",
                )
            )

        recommendations = [
            RecommendationItem(
                title=job.get("role") or "未知职位",
                company=" · ".join(filter(None, [job.get("company"), job.get("location")])),
                tags=job.get("tags") or [],
                score=int(job.get("score") or 0),
            )
            for job in jobs[:6]
        ]

        return ChatResponse(
            history=history,
            messages=conversation_messages,
            recommendations=recommendations,
            radar=self._build_radar(knowledge, jobs),
        )

    def jobs(self) -> JobsResponse:
        snapshot = self._store.snapshot()
        runtime_jobs = snapshot.get("jobs", [])
        search_meta = snapshot.get("job_search", {})
        keyword = search_meta.get("keyword") or "尚未执行职位抓取"
        filters = [item for item in [keyword, search_meta.get("city"), self._login_status_label(snapshot.get("login", {}).get("status", "unknown"))] if item]

        cards = [
            JobCard(
                company=job.get("company") or "未知公司",
                role=job.get("role") or "未知职位",
                salary=job.get("salary") or "",
                location=job.get("location") or "",
                tags=job.get("tags") or [],
                summary=job.get("summary") or "",
                score=int(job.get("score") or 0),
            )
            for job in runtime_jobs[:20]
        ]

        first = runtime_jobs[0] if runtime_jobs else {}
        detail = JobDetail(
            role=first.get("role") or "暂无职位详情",
            company=first.get("company") or "请先执行职位抓取",
            salary=first.get("salary") or "",
            meta=[item for item in [first.get("location"), first.get("collected_at"), first.get("boss_url")] if item],
            description=[
                text
                for text in [
                    first.get("summary"),
                    "职位详情将来自 BOSS 实时抓取结果；当前尚未抓到可展示职位。" if not runtime_jobs else None,
                ]
                if text
            ],
        )

        return JobsResponse(
            summary=JobSummary(count=str(len(runtime_jobs)), keyword=keyword),
            filters=filters,
            jobs=cards,
            detail=detail,
        )

    def ai_config(self) -> AIConfigResponse:
        snapshot = self._store.snapshot()
        login_status = snapshot.get("login", {}).get("status", "unknown")
        has_knowledge = bool(snapshot.get("knowledge", []))
        stored = snapshot.get("ai_config", {})
        provider = stored.get("provider") or "openai"
        resolved_api_key_env = self._settings.resolve_llm_api_key_env(provider)
        api_key = self._settings.resolve_llm_api_key(provider)
        base_url = stored.get("base_url") or "https://api.openai.com/v1"
        model = stored.get("model") or "gpt-4.1-mini"
        profile = AIProfileSettings(**stored.get("profile", {}))
        subscriptions = [
            AISubscriptionItem(**item)
            for item in stored.get("subscriptions", self._default_subscriptions())
        ]
        knowledge_files = [
            AIKnowledgeFile(
                id=item.id,
                title=item.title,
                kind=item.kind,
                tags=item.tags,
            )
            for item in self._knowledge_chunks(snapshot)
        ]
        providers = self._provider_options()

        available_models = [
            AIConfigModelOption(label="GPT-4.1 mini", value="gpt-4.1-mini"),
            AIConfigModelOption(label="GPT-4.1", value="gpt-4.1"),
            AIConfigModelOption(label="GPT-4o mini", value="gpt-4o-mini"),
        ]
        if model not in {item.value for item in available_models}:
            available_models.append(AIConfigModelOption(label=f"自定义模型 ({model})", value=model))

        return AIConfigResponse(
            api_key_configured=bool(api_key),
            api_key_masked=self._mask_api_key(api_key),
            api_key_env=resolved_api_key_env,
            provider=provider,
            providers=providers,
            base_url=base_url,
            model=model,
            available_models=available_models,
            profile=profile,
            subscriptions=subscriptions,
            knowledge_files=knowledge_files,
            storage_used_label=str(len(knowledge_files)),
            storage_limit_label="100",
            encryption_enabled=True,
            models=[
                ModelOption(name="Chat Reply Generator", provider="Local Service", active=True),
                ModelOption(name=f"Vector Store: {self._settings.vector_store_backend}", provider="Backend", active=True),
            ],
            toggles=[
                ToggleOption(
                    title="BOSS 登录态检测",
                    description=f"当前登录状态：{self._login_status_label(login_status)}",
                    enabled=login_status == "logged_in",
                ),
                ToggleOption(
                    title="职位实时抓取",
                    description="通过 Playwright 持久化浏览器会话抓取 BOSS 职位列表。",
                    enabled=True,
                ),
                ToggleOption(
                    title="RAG 知识检索",
                    description=f"当前知识片段数：{len(snapshot.get('knowledge', []))}",
                    enabled=has_knowledge,
                ),
            ],
            push=[
                PushOption(label="当前未配置外部推送渠道", enabled=False),
            ],
            status=RuntimeStatus(
                load=f"职位 {len(snapshot.get('jobs', []))} / 会话 {len(snapshot.get('messages', []))}",
                credits=self._settings.vector_store_backend,
                window=f"BOSS: {self._settings.boss_base_url} | State: {self._settings.browser_state_dir}",
            ),
        )

    def interviews(self) -> InterviewsResponse:
        snapshot = self._store.snapshot()
        messages = snapshot.get("messages", [])
        cards = self._derive_interview_cards(messages)
        upcoming = [
            UpcomingInterview(
                date=(card.time or "")[:10],
                title=f"{card.company} · {card.role}",
                time=card.time or "待确认时间",
            )
            for card in cards[:4]
        ]

        return InterviewsResponse(
            pending_count=len(cards),
            cards=cards,
            board=InterviewBoard(
                weekly=str(len(cards)),
                match=f"{self._interview_match(cards)}%",
                resume_progress=f"{self._resume_progress(snapshot)}%",
                upcoming=upcoming,
                tip="面试面板仅展示从实际会话中识别到的邀约；没有识别到时会保持为空。",
            ),
        )

    def resume_lab(self) -> ResumeLabResponse:
        snapshot = self._store.snapshot()
        knowledge = self._knowledge_chunks(snapshot)
        resume_chunks = [chunk for chunk in knowledge if chunk.kind == "resume"]
        pitch_sources = [chunk for chunk in knowledge if chunk.kind in {"project", "preference", "conversation"}]
        score = self._resume_score(snapshot)

        return ResumeLabResponse(
            score=score,
            quality=self._resume_quality(score),
            analysis=self._resume_analysis(snapshot, resume_chunks),
            variants=[
                ResumeVariant(name=chunk.title, tag=chunk.kind)
                for chunk in resume_chunks[:8]
            ],
            pitches=[
                PitchVariant(label=chunk.title, content=chunk.content)
                for chunk in pitch_sources[:6]
            ],
            progress=self._resume_progress(snapshot),
        )

    def knowledge(self) -> list[KnowledgeChunk]:
        return self._knowledge_chunks(self._store.snapshot())

    def snapshot(self) -> dict:
        return self._store.snapshot()

    def set_jobs(self, jobs: list[dict], keyword: str | None = None, city: str | None = None) -> None:
        self._store.set_jobs(jobs, keyword=keyword, city=city, collected_at=datetime.utcnow().isoformat())

    def set_messages(self, messages: list[dict]) -> None:
        self._store.set_messages(messages)

    def upsert_conversations(self, conversations: list[ConversationMemory]) -> None:
        self._store.upsert_conversations([item.model_dump() for item in conversations])

    def upsert_interviews(self, interviews: list[InterviewMemory]) -> None:
        self._store.upsert_interviews([item.model_dump() for item in interviews])

    def upsert_job_decisions(self, decisions: list[JobDecisionMemory]) -> None:
        self._store.upsert_job_decisions([item.model_dump() for item in decisions])

    def set_login(self, status: str, last_checked: str | None) -> None:
        self._store.set_login(status, last_checked)

    def add_knowledge(self, chunks: list[KnowledgeChunk]) -> None:
        self._store.upsert_knowledge([chunk.model_dump() for chunk in chunks])

    def set_ai_config(
        self,
        *,
        api_key: str | None,
        provider: str,
        base_url: str,
        model: str,
        profile: AIProfileSettings,
        subscriptions: list[AISubscriptionItem],
    ) -> None:
        snapshot = self._store.snapshot()
        current = snapshot.get("ai_config", {})
        next_provider = provider.strip()
        next_api_key = (api_key or "").strip()
        if next_api_key:
            env_name = self._settings.resolve_llm_api_key_env(next_provider)
            upsert_env_value(env_name, next_api_key)

        self._store.set_ai_config(
            {
                "provider": next_provider,
                "base_url": base_url.strip(),
                "model": model.strip(),
                "profile": profile.model_dump(),
                "subscriptions": [item.model_dump() for item in subscriptions],
            }
        )

    def current_ai_runtime_config(self) -> dict:
        snapshot = self._store.snapshot()
        stored = snapshot.get("ai_config", {})
        provider = str(stored.get("provider") or "openai")
        return {
            **{key: value for key, value in stored.items() if key not in {"api_key", "api_key_env"}},
            "api_key": self._settings.resolve_llm_api_key(provider),
            "api_key_env": self._settings.resolve_llm_api_key_env(provider),
        }

    def _knowledge_chunks(self, snapshot: dict) -> list[KnowledgeChunk]:
        return [KnowledgeChunk(**item) for item in snapshot.get("knowledge", [])]

    def _login_status_label(self, status: str) -> str:
        mapping = {
            "logged_in": "已登录",
            "logged_out": "未登录",
            "error": "检测失败",
            "unknown": "未检测",
        }
        return mapping.get(status, status or "未检测")

    def _job_delta(self, snapshot: dict) -> str:
        collected_at = snapshot.get("job_search", {}).get("collected_at")
        return f"最近抓取 {collected_at}" if collected_at else "尚未抓取"

    def _message_delta(self, snapshot: dict) -> str:
        messages = snapshot.get("messages", [])
        if not messages:
            return "尚未同步"
        return f"最近 {messages[0].get('time') or '刚刚'}"

    def _job_stage(self, job: dict) -> str:
        if job.get("boss_url"):
            return "已抓取到 BOSS 列表"
        return "已写入本地状态"

    def _build_insight(self, snapshot: dict) -> str:
        jobs = snapshot.get("jobs", [])
        messages = snapshot.get("messages", [])
        knowledge = snapshot.get("knowledge", [])
        login_status = self._login_status_label(snapshot.get("login", {}).get("status", "unknown"))
        return (
            f"当前登录状态：{login_status}；已抓取 {len(jobs)} 个职位，"
            f"同步 {len(messages)} 条会话摘要，本地知识库中有 {len(knowledge)} 个片段。"
        )

    def _build_radar(self, knowledge: list[KnowledgeChunk], jobs: list[dict]) -> RadarSummary:
        tags = {tag.lower() for item in jobs for tag in item.get("tags", [])}
        knowledge_kinds = {item.kind for item in knowledge}
        score = min(100, len(knowledge) * 12 + len(jobs) * 4)
        axes = [
            f"简历 {len([item for item in knowledge if item.kind == 'resume'])}",
            f"项目 {len([item for item in knowledge if item.kind == 'project'])}",
            f"偏好 {len([item for item in knowledge if item.kind == 'preference'])}",
            f"岗位标签 {len(tags)}",
        ]
        if not knowledge and not jobs:
            score = 0
        tip = (
            f"当前知识类型：{', '.join(sorted(knowledge_kinds)) or '无'}；"
            f"岗位标签覆盖数：{len(tags)}。"
        )
        return RadarSummary(axes=axes, score=score, tip=tip)

    def _derive_interview_cards(self, messages: list[dict]) -> list[InterviewCard]:
        interview_tokens = ("面试", "约面", "笔试", "到场", "视频", "电话沟通")
        cards: list[InterviewCard] = []
        for item in messages:
            incoming = item.get("incoming") or ""
            if not any(token in incoming for token in interview_tokens):
                continue
            cards.append(
                InterviewCard(
                    company=item.get("company") or "未知公司",
                    role=item.get("role") or "待确认岗位",
                    mode="来自 BOSS 会话",
                    time=item.get("time") or "",
                    reason="根据实际会话内容识别到面试或进一步沟通邀约。",
                    excerpt=incoming[:200],
                )
            )
        return cards

    def _interview_match(self, cards: list[InterviewCard]) -> int:
        if not cards:
            return 0
        return min(100, 60 + len(cards) * 10)

    def _resume_progress(self, snapshot: dict) -> int:
        knowledge = self._knowledge_chunks(snapshot)
        coverage = {chunk.kind for chunk in knowledge}
        if not coverage:
            return 0
        return min(100, len(coverage) * 25)

    def _resume_score(self, snapshot: dict) -> int:
        knowledge = self._knowledge_chunks(snapshot)
        resume_chunks = [chunk for chunk in knowledge if chunk.kind == "resume"]
        project_chunks = [chunk for chunk in knowledge if chunk.kind == "project"]
        preference_chunks = [chunk for chunk in knowledge if chunk.kind == "preference"]
        return min(100, len(resume_chunks) * 35 + len(project_chunks) * 15 + len(preference_chunks) * 10)

    def _resume_quality(self, score: int) -> str:
        if score >= 80:
            return "信息完整"
        if score >= 40:
            return "基础可用"
        return "待补充"

    def _resume_analysis(self, snapshot: dict, resume_chunks: list[KnowledgeChunk]) -> str:
        knowledge = self._knowledge_chunks(snapshot)
        if not knowledge:
            return "本地知识库还没有任何真实简历或项目资料，请先导入后再查看。"
        if not resume_chunks:
            return "已写入知识库，但还没有标记为 resume 的真实简历片段。"
        return f"当前共有 {len(resume_chunks)} 个简历片段、{len(knowledge)} 个总知识片段，页面内容完全来自本地知识库。"

    def _mask_api_key(self, api_key: str) -> str:
        if not api_key:
            return ""
        if len(api_key) <= 8:
            return "*" * len(api_key)
        return f"{api_key[:4]}{'*' * max(4, len(api_key) - 8)}{api_key[-4:]}"

    def _provider_options(self) -> list[AIProviderOption]:
        return [
            AIProviderOption(
                label="OpenAI / GPT",
                value="openai",
                default_base_url="https://api.openai.com/v1",
                default_model="gpt-4.1-mini",
            ),
            AIProviderOption(
                label="Google Gemini",
                value="gemini",
                default_base_url="https://generativelanguage.googleapis.com/v1beta/openai",
                default_model="gemini-2.5-flash",
            ),
            AIProviderOption(
                label="DeepSeek",
                value="deepseek",
                default_base_url="https://api.deepseek.com/v1",
                default_model="deepseek-chat",
            ),
            AIProviderOption(
                label="阿里云百炼",
                value="bailian",
                default_base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                default_model="qwen-plus",
            ),
            AIProviderOption(
                label="火山引擎",
                value="volcengine",
                default_base_url="https://ark.cn-beijing.volces.com/api/v3",
                default_model="doubao-1.5-pro-32k-250115",
            ),
            AIProviderOption(
                label="自定义 OpenAI 兼容",
                value="custom",
                default_base_url="",
                default_model="",
            ),
        ]

    def _default_subscriptions(self) -> list[dict]:
        return [
            {
                "key": "feishu_bot",
                "label": "飞书机器人",
                "description": "Webhook 推送",
                "channel": "feishu",
                "connected": False,
            },
            {
                "key": "wechat_service",
                "label": "微信服务号",
                "description": "模板消息",
                "channel": "wechat",
                "connected": True,
            },
            {
                "key": "email_digest",
                "label": "电子邮箱",
                "description": "每日简报",
                "channel": "email",
                "connected": False,
            },
        ]


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
