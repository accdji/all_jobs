from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from hashlib import md5
import re

from ..schemas import ConversationMemory, ConversationSyncMessage, InterviewMemory, JobDecisionMemory, KnowledgeChunk


def _now() -> str:
    return datetime.utcnow().isoformat()


def _normalize(value: str) -> str:
    return re.sub(r"\s+", "", (value or "").strip()).lower()


def _stable_id(prefix: str, *parts: str) -> str:
    joined = "||".join(_normalize(part) for part in parts if part is not None)
    return f"{prefix}-{md5(joined.encode('utf-8')).hexdigest()[:16]}"


def _job_key(company: str, role: str) -> str:
    return f"{_normalize(company)}::{_normalize(role)}"


@dataclass
class MemorySyncResult:
    jobs: list[dict]
    conversations: list[ConversationMemory]
    interviews: list[InterviewMemory]
    job_decisions: list[JobDecisionMemory]
    knowledge_chunks: list[KnowledgeChunk]


class MemoryService:
    def sync(self, snapshot: dict, jobs: list[dict], messages: list[dict]) -> MemorySyncResult:
        existing_conversations = {
            item["id"]: ConversationMemory(**item) for item in snapshot.get("conversations", [])
        }
        existing_interviews = {
            item["id"]: InterviewMemory(**item) for item in snapshot.get("interviews", [])
        }
        existing_decisions = {
            item["job_key"]: JobDecisionMemory(**item) for item in snapshot.get("job_decisions", [])
        }

        passed_keys = {
            _job_key(item.company, item.role)
            for item in existing_interviews.values()
            if item.result == "passed"
        }

        synced_jobs, job_decisions = self._sync_jobs(jobs, existing_decisions, passed_keys)
        conversations, interviews = self._sync_conversations(messages, existing_conversations, existing_interviews, job_decisions)
        knowledge_chunks = self._build_knowledge_chunks(conversations, interviews, job_decisions)

        return MemorySyncResult(
            jobs=synced_jobs,
            conversations=list(conversations.values()),
            interviews=list(interviews.values()),
            job_decisions=list(job_decisions.values()),
            knowledge_chunks=knowledge_chunks,
        )

    def _sync_jobs(
        self,
        jobs: list[dict],
        existing_decisions: dict[str, JobDecisionMemory],
        passed_keys: set[str],
    ) -> tuple[list[dict], dict[str, JobDecisionMemory]]:
        next_jobs: list[dict] = []
        next_decisions = dict(existing_decisions)

        for job in jobs:
            company = job.get("company") or "未知公司"
            role = job.get("role") or "未知职位"
            key = _job_key(company, role)
            previous = next_decisions.get(key)
            tags = [str(tag) for tag in job.get("tags", []) if str(tag).strip()]
            strengths = [tag for tag in tags[:4] if tag]
            missing_skills = [token for token in ["react", "typescript", "ai", "webgl"] if token not in " ".join(tags).lower()]

            permanent_skip = key in passed_keys
            skip_reason = "同公司同岗位已面试通过，自动跳过" if permanent_skip else (previous.skip_reason if previous else "")
            current_stage = "skipped" if permanent_skip else job.get("apply_status") or (previous.current_stage if previous else "discovered")
            interview_result = "passed" if permanent_skip else (previous.interview_result if previous else "pending")

            decision = JobDecisionMemory(
                id=previous.id if previous else _stable_id("job", company, role),
                company=company,
                role=role,
                job_key=key,
                job_url=job.get("boss_url") or (previous.job_url if previous else ""),
                salary=job.get("salary") or (previous.salary if previous else ""),
                location=job.get("location") or (previous.location if previous else ""),
                match_reason=self._build_match_reason(job),
                risk_reason=self._build_risk_reason(job),
                missing_skills=missing_skills,
                strengths=strengths,
                current_stage=current_stage,
                interview_result=interview_result,
                skip_reason=skip_reason,
                permanent_skip=permanent_skip,
                allow_retry=not permanent_skip,
                last_action=job.get("apply_note") or "search_sync",
                last_updated=_now(),
                tags=tags,
            )
            next_decisions[key] = decision

            enriched_job = {
                **job,
                "job_key": key,
                "skip_reason": skip_reason,
                "current_stage": current_stage,
                "interview_result": interview_result,
                "permanent_skip": permanent_skip,
            }
            if not permanent_skip:
                next_jobs.append(enriched_job)

        return next_jobs, next_decisions

    def _sync_conversations(
        self,
        messages: list[dict],
        existing_conversations: dict[str, ConversationMemory],
        existing_interviews: dict[str, InterviewMemory],
        job_decisions: dict[str, JobDecisionMemory],
    ) -> tuple[dict[str, ConversationMemory], dict[str, InterviewMemory]]:
        next_conversations = dict(existing_conversations)
        next_interviews = dict(existing_interviews)

        for message in messages:
            company = message.get("company") or "未知公司"
            role = message.get("role") or self._guess_role_from_decisions(company, job_decisions)
            conversation_id = message.get("conversation_id") or _stable_id("conv", company, role or company)
            memory_id = _stable_id("conversation", company, role, conversation_id)
            previous = next_conversations.get(memory_id)

            transcript = self._build_transcript(message, previous)
            if not transcript:
                continue

            last_item = transcript[-1]
            incoming = next((item.content for item in reversed(transcript) if item.speaker == "hr"), last_item.content)
            timestamp = last_item.time or message.get("time") or ""
            common_questions = previous.common_questions[:] if previous else []
            for question in self._extract_questions(incoming):
                if question not in common_questions:
                    common_questions.append(question)

            stage = self._detect_stage(incoming, previous.stage if previous else "new")
            tags = self._extract_tags(company, role, " ".join(item.content for item in transcript[-6:]))
            style = self._detect_style(incoming) or (previous.style if previous else "")

            memory = ConversationMemory(
                id=memory_id,
                company=company,
                role=role,
                conversation_id=conversation_id,
                hr_name=message.get("hr_name") or (previous.hr_name if previous else ""),
                stage=stage,
                style=style,
                common_questions=common_questions[:8],
                last_message_time=timestamp,
                last_sync_time=_now(),
                last_message_summary=incoming[:120],
                full_transcript=transcript,
                synced_message_count=len(transcript),
                follow_up_at="",
                tags=tags,
            )
            next_conversations[memory_id] = memory

            interview = self._build_interview_memory(memory, incoming, timestamp)
            if interview is not None:
                next_interviews[interview.id] = interview

        return next_conversations, next_interviews

    def _build_transcript(self, message: dict, previous: ConversationMemory | None) -> list[ConversationSyncMessage]:
        if previous:
            transcript = list(previous.full_transcript)
        else:
            transcript = []

        raw_transcript = message.get("transcript") or []
        if raw_transcript:
            normalized: list[ConversationSyncMessage] = []
            for item in raw_transcript:
                content = str(item.get("content") or "").strip()
                if not content:
                    continue
                speaker = str(item.get("speaker") or "system")
                if speaker not in {"hr", "candidate", "system"}:
                    speaker = "system"
                normalized.append(
                    ConversationSyncMessage(
                        speaker=speaker,
                        content=content,
                        time=str(item.get("time") or ""),
                    )
                )
            if normalized:
                return normalized

        incoming = str(message.get("incoming") or "").strip()
        reply = str(message.get("reply") or "").strip()
        timestamp = str(message.get("time") or "")

        if incoming and (not transcript or transcript[-1].content != incoming):
            transcript.append(ConversationSyncMessage(speaker="hr", content=incoming, time=timestamp))
        if reply and (not transcript or transcript[-1].content != reply):
            transcript.append(ConversationSyncMessage(speaker="candidate", content=reply, time=str(message.get("reply_time") or timestamp)))
        return transcript

    def _build_knowledge_chunks(
        self,
        conversations: dict[str, ConversationMemory],
        interviews: dict[str, InterviewMemory],
        job_decisions: dict[str, JobDecisionMemory],
    ) -> list[KnowledgeChunk]:
        chunks: list[KnowledgeChunk] = []

        for conversation in conversations.values():
            transcript_preview = "\n".join(
                f"{item.speaker}: {item.content}" for item in conversation.full_transcript[-6:]
            )
            chunks.append(
                KnowledgeChunk(
                    id=f"knowledge-{conversation.id}",
                    title=f"{conversation.company} {conversation.role or 'HR会话'}",
                    kind="conversation",
                    content=(
                        f"公司: {conversation.company}\n"
                        f"岗位: {conversation.role}\n"
                        f"阶段: {conversation.stage}\n"
                        f"风格: {conversation.style}\n"
                        f"常见问题: {' / '.join(conversation.common_questions) or '无'}\n"
                        f"最近消息摘要: {conversation.last_message_summary}\n"
                        f"会话摘录:\n{transcript_preview}"
                    ),
                    tags=conversation.tags,
                )
            )

        for interview in interviews.values():
            chunks.append(
                KnowledgeChunk(
                    id=f"knowledge-{interview.id}",
                    title=f"{interview.company} {interview.role} 面试记录",
                    kind="interview",
                    content=(
                        f"公司: {interview.company}\n"
                        f"岗位: {interview.role}\n"
                        f"轮次: {interview.stage}\n"
                        f"结果: {interview.result}\n"
                        f"时间: {interview.interview_time}\n"
                        f"方式: {interview.interview_mode}\n"
                        f"面试官: {interview.interviewer}\n"
                        f"问题: {' / '.join(interview.questions) or '无'}\n"
                        f"回答总结: {interview.answers_summary or '无'}\n"
                        f"反馈: {interview.feedback or '无'}\n"
                        f"原因: {interview.outcome_reason or '无'}\n"
                        f"原始片段: {interview.source_excerpt}"
                    ),
                    tags=[interview.company, interview.role, interview.result, interview.stage],
                )
            )

        for decision in job_decisions.values():
            kind = "decision" if decision.permanent_skip or decision.skip_reason else "job"
            chunks.append(
                KnowledgeChunk(
                    id=f"knowledge-{decision.id}",
                    title=f"{decision.company} {decision.role} 求职决策",
                    kind=kind,
                    content=(
                        f"公司: {decision.company}\n"
                        f"岗位: {decision.role}\n"
                        f"阶段: {decision.current_stage}\n"
                        f"面试结果: {decision.interview_result}\n"
                        f"跳过原因: {decision.skip_reason or '无'}\n"
                        f"匹配原因: {decision.match_reason or '无'}\n"
                        f"风险原因: {decision.risk_reason or '无'}\n"
                        f"缺失技能: {' / '.join(decision.missing_skills) or '无'}\n"
                        f"优势技能: {' / '.join(decision.strengths) or '无'}\n"
                        f"最后动作: {decision.last_action}\n"
                        f"更新时间: {decision.last_updated}"
                    ),
                    tags=[decision.company, decision.role, decision.current_stage, *decision.tags],
                )
            )

        return chunks

    def _build_match_reason(self, job: dict) -> str:
        tags = " ".join(str(tag) for tag in job.get("tags", []))
        role = str(job.get("role") or "")
        text = f"{role} {tags}".lower()
        matched = [token for token in ["react", "typescript", "ai", "webgl", "前端", "可视化"] if token in text]
        return "命中关键词: " + " / ".join(matched) if matched else "岗位已进入自动筛选列表"

    def _build_risk_reason(self, job: dict) -> str:
        text = f"{job.get('role', '')} {job.get('summary', '')}".lower()
        risky = [token for token in ["外包", "销售", "直播"] if token.lower() in text]
        return "风险标签: " + " / ".join(risky) if risky else ""

    def _guess_role_from_decisions(self, company: str, job_decisions: dict[str, JobDecisionMemory]) -> str:
        normalized_company = _normalize(company)
        for decision in job_decisions.values():
            if _normalize(decision.company) == normalized_company:
                return decision.role
        return ""

    def _extract_questions(self, text: str) -> list[str]:
        questions = []
        for part in re.split(r"[？?\n]", text):
            part = part.strip()
            if part and any(token in part for token in ["负责", "经验", "项目", "到岗", "薪资", "作品"]):
                questions.append(part[:40])
        return questions[:5]

    def _detect_stage(self, text: str, fallback: str) -> str:
        stage_map = {
            "面试通过": "passed",
            "通过": "passed",
            "offer": "passed",
            "未通过": "failed",
            "淘汰": "failed",
            "不合适": "failed",
            "约面": "interview_scheduled",
            "面试": "interviewing",
            "笔试": "assessment",
            "沟通": "chatting",
        }
        lowered = text.lower()
        for token, stage in stage_map.items():
            if token.lower() in lowered:
                return stage
        return fallback

    def _detect_style(self, text: str) -> str:
        if "尽快" in text or "马上" in text:
            return "direct"
        if "方便" in text or "辛苦" in text:
            return "polite"
        if "流程" in text or "安排" in text:
            return "process-driven"
        return ""

    def _extract_tags(self, company: str, role: str, text: str) -> list[str]:
        tags = {company, role}
        for token in ["面试", "笔试", "薪资", "远程", "到岗", "作品集", "通过", "未通过"]:
            if token and token in text:
                tags.add(token)
        return [tag for tag in tags if tag]

    def _build_interview_memory(self, memory: ConversationMemory, text: str, timestamp: str) -> InterviewMemory | None:
        if not any(token in text for token in ["面试", "笔试", "通过", "未通过", "淘汰", "offer", "终面", "一面", "二面"]):
            return None

        result = "unknown"
        reason = ""
        if any(token in text for token in ["面试通过", "通过", "offer"]):
            result = "passed"
            reason = "对话中出现通过或 offer 信号"
        elif any(token in text for token in ["未通过", "淘汰", "不合适", "失败"]):
            result = "failed"
            reason = "对话中出现淘汰或未通过信号"
        elif "面试" in text or "笔试" in text:
            result = "pending"
            reason = "对话中出现面试安排信号"

        stage = "终面" if "终面" in text else "二面" if "二面" in text else "一面" if "一面" in text else "面试"
        mode = "线上" if any(token in text for token in ["线上", "视频", "腾讯会议", "会议"]) else "线下" if "线下" in text else ""

        return InterviewMemory(
            id=_stable_id("interview", memory.company, memory.role, memory.conversation_id, stage),
            company=memory.company,
            role=memory.role,
            conversation_id=memory.conversation_id,
            stage=stage,
            result=result,
            interview_time=timestamp,
            interview_mode=mode,
            interviewer="",
            questions=self._extract_questions(text),
            answers_summary="",
            feedback="",
            outcome_reason=reason,
            source_excerpt=text[:180],
            created_at=_now(),
        )
