from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class HeroBlock(BaseModel):
    title: str
    subtitle: str
    status: str


class StatBlock(BaseModel):
    label: str
    value: str
    delta: str


class PipelineItem(BaseModel):
    company: str
    role: str
    salary: str
    stage: str
    summary: str
    message: str


class ThreadItem(BaseModel):
    company: str
    time: str
    incoming: str
    reply: str


class OverviewResponse(BaseModel):
    hero: HeroBlock
    stats: list[StatBlock]
    pipeline: list[PipelineItem]
    threads: list[ThreadItem]
    insight: str


class ChatHistoryItem(BaseModel):
    title: str
    preview: str
    time: str
    active: bool


class ChatMessage(BaseModel):
    speaker: Literal["user", "assistant"]
    content: str
    time: str


class RecommendationItem(BaseModel):
    title: str
    company: str
    tags: list[str]
    score: int


class RadarSummary(BaseModel):
    axes: list[str]
    score: int
    tip: str


class ChatResponse(BaseModel):
    history: list[ChatHistoryItem]
    messages: list[ChatMessage]
    recommendations: list[RecommendationItem]
    radar: RadarSummary


class JobDetail(BaseModel):
    role: str
    company: str
    salary: str
    meta: list[str]
    description: list[str]


class JobCard(BaseModel):
    company: str
    role: str
    salary: str
    location: str
    tags: list[str]
    summary: str
    score: int


class JobSummary(BaseModel):
    count: str
    keyword: str


class JobsResponse(BaseModel):
    summary: JobSummary
    filters: list[str]
    jobs: list[JobCard]
    detail: JobDetail


class ModelOption(BaseModel):
    name: str
    provider: str
    active: bool


class ToggleOption(BaseModel):
    title: str
    description: str
    enabled: bool


class PushOption(BaseModel):
    label: str
    enabled: bool


class RuntimeStatus(BaseModel):
    load: str
    credits: str
    window: str


class AIConfigModelOption(BaseModel):
    label: str
    value: str


class AIProviderOption(BaseModel):
    label: str
    value: str
    default_base_url: str
    default_model: str


class AIProfileSettings(BaseModel):
    desired_salary_min: str = ""
    desired_salary_max: str = ""
    preferred_location: str = "北京"
    skills: list[str] = Field(default_factory=list)
    summary: str = ""


class AIKnowledgeFile(BaseModel):
    id: str
    title: str
    kind: str
    tags: list[str] = Field(default_factory=list)


class AISubscriptionItem(BaseModel):
    key: str
    label: str
    description: str
    channel: str
    connected: bool = False


class AIConfigResponse(BaseModel):
    api_key_configured: bool
    api_key_masked: str
    api_key_env: str
    provider: str
    providers: list[AIProviderOption]
    base_url: str
    model: str
    available_models: list[AIConfigModelOption]
    profile: AIProfileSettings
    subscriptions: list[AISubscriptionItem]
    knowledge_files: list[AIKnowledgeFile]
    storage_used_label: str
    storage_limit_label: str
    encryption_enabled: bool
    models: list[ModelOption]
    toggles: list[ToggleOption]
    push: list[PushOption]
    status: RuntimeStatus


class AIConfigUpdateRequest(BaseModel):
    api_key: str | None = None
    provider: str = Field(min_length=1, max_length=80)
    base_url: str = Field(min_length=1, max_length=500)
    model: str = Field(min_length=1, max_length=120)
    profile: AIProfileSettings
    subscriptions: list[AISubscriptionItem] = Field(default_factory=list)


class InterviewCard(BaseModel):
    company: str
    role: str
    mode: str
    time: str
    reason: str
    excerpt: str


class UpcomingInterview(BaseModel):
    date: str
    title: str
    time: str


class InterviewBoard(BaseModel):
    weekly: str
    match: str
    resume_progress: str
    upcoming: list[UpcomingInterview]
    tip: str


class InterviewsResponse(BaseModel):
    pending_count: int
    cards: list[InterviewCard]
    board: InterviewBoard


class ResumeVariant(BaseModel):
    name: str
    tag: str


class PitchVariant(BaseModel):
    label: str
    content: str


class ResumeLabResponse(BaseModel):
    score: int
    quality: str
    analysis: str
    variants: list[ResumeVariant]
    pitches: list[PitchVariant]
    progress: int


class KnowledgeChunk(BaseModel):
    id: str
    title: str
    kind: Literal["resume", "project", "preference", "faq", "conversation", "interview", "job", "decision"]
    content: str
    tags: list[str] = Field(default_factory=list)


class ConversationSyncMessage(BaseModel):
    speaker: Literal["hr", "candidate", "system"]
    content: str
    time: str = ""


class ConversationMemory(BaseModel):
    id: str
    company: str
    role: str = ""
    conversation_id: str
    hr_name: str = ""
    stage: str = "new"
    style: str = ""
    common_questions: list[str] = Field(default_factory=list)
    last_message_time: str = ""
    last_sync_time: str = ""
    last_message_summary: str = ""
    full_transcript: list[ConversationSyncMessage] = Field(default_factory=list)
    synced_message_count: int = 0
    follow_up_at: str = ""
    tags: list[str] = Field(default_factory=list)


class InterviewMemory(BaseModel):
    id: str
    company: str
    role: str
    conversation_id: str
    stage: str = ""
    result: Literal["pending", "passed", "failed", "unknown"] = "unknown"
    interview_time: str = ""
    interview_mode: str = ""
    interviewer: str = ""
    questions: list[str] = Field(default_factory=list)
    answers_summary: str = ""
    feedback: str = ""
    outcome_reason: str = ""
    source_excerpt: str = ""
    created_at: str = ""


class JobDecisionMemory(BaseModel):
    id: str
    company: str
    role: str
    job_key: str
    job_url: str = ""
    salary: str = ""
    location: str = ""
    match_reason: str = ""
    risk_reason: str = ""
    missing_skills: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    current_stage: str = "discovered"
    interview_result: Literal["pending", "passed", "failed", "unknown"] = "unknown"
    skip_reason: str = ""
    permanent_skip: bool = False
    allow_retry: bool = True
    last_action: str = ""
    last_updated: str = ""
    tags: list[str] = Field(default_factory=list)


class KnowledgeMatch(BaseModel):
    id: str
    title: str
    kind: str
    score: float
    excerpt: str
    tags: list[str]


class RAGSearchRequest(BaseModel):
    query: str = Field(min_length=2, max_length=500)
    top_k: int = Field(default=4, ge=1, le=10)


class RAGSearchResponse(BaseModel):
    query: str
    results: list[KnowledgeMatch]


class KnowledgeIngestRequest(BaseModel):
    chunks: list[KnowledgeChunk]


class ChatReplyRequest(BaseModel):
    message: str = Field(min_length=2, max_length=1000)
    conversation_id: str | None = None
    auto_send: bool = False


class ChatReplyResponse(BaseModel):
    user_message: str
    intent: str
    retrieved: list[KnowledgeMatch]
    draft_reply: str
    suggested_action: Literal["send_now", "review_then_send", "clarify"]
    confidence: float
    provider: str = ""
    model: str = ""


class AutomationTaskCreate(BaseModel):
    task_type: Literal["manual_login", "login_check", "collect_jobs", "sync_messages", "send_message", "refresh_rag"]
    payload: dict = Field(default_factory=dict)


class AutomationTask(BaseModel):
    id: str
    task_type: str
    status: Literal["queued", "running", "completed", "failed"]
    created_at: datetime
    updated_at: datetime
    payload: dict
    result: dict = Field(default_factory=dict)
