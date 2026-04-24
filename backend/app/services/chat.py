from __future__ import annotations

import json
from urllib import error, request

from ..repositories import DashboardRepository
from ..schemas import ChatReplyResponse, KnowledgeMatch
from .rag import RAGService


class ChatAgentService:
    def __init__(self, rag_service: RAGService, repository: DashboardRepository) -> None:
        self._rag = rag_service
        self._repository = repository

    def generate_reply(self, message: str) -> ChatReplyResponse:
        intent = self._classify_intent(message)
        retrieved = self._rag.search(message, top_k=4)
        config = self._repository.current_ai_runtime_config()
        provider = str(config.get("provider") or "local-fallback")
        model = str(config.get("model") or "local-fallback")
        draft = self._request_model_reply(message, intent, retrieved, config)
        suggested_action = "review_then_send" if intent in {"salary", "interview", "relocation"} else "send_now"
        confidence = min(0.98, 0.58 + len(retrieved) * 0.07)

        return ChatReplyResponse(
            user_message=message,
            intent=intent,
            retrieved=retrieved,
            draft_reply=draft,
            suggested_action=suggested_action,
            confidence=round(confidence, 2),
            provider=provider,
            model=model,
        )

    def _request_model_reply(
        self,
        message: str,
        intent: str,
        retrieved: list[KnowledgeMatch],
        config: dict,
    ) -> str:
        api_key = str(config.get("api_key") or "").strip()
        base_url = str(config.get("base_url") or "").strip().rstrip("/")
        model = str(config.get("model") or "").strip()
        if not api_key or not base_url or not model:
            return self._compose_fallback_reply(message, intent, retrieved)

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": self._build_system_prompt(retrieved)},
                {"role": "user", "content": message},
            ],
            "temperature": 0.4,
        }
        endpoint = f"{base_url}/chat/completions"
        req = request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=45) as response:
                body = json.loads(response.read().decode("utf-8"))
        except (error.URLError, error.HTTPError, TimeoutError, json.JSONDecodeError):
            return self._compose_fallback_reply(message, intent, retrieved)

        choices = body.get("choices") or []
        if not choices:
            return self._compose_fallback_reply(message, intent, retrieved)
        content = choices[0].get("message", {}).get("content", "")
        if isinstance(content, list):
            parts = [item.get("text", "") for item in content if isinstance(item, dict)]
            content = "\n".join(part for part in parts if part)
        reply = str(content or "").strip()
        return reply or self._compose_fallback_reply(message, intent, retrieved)

    def _build_system_prompt(self, retrieved: list[KnowledgeMatch]) -> str:
        snapshot = self._repository.snapshot()
        ai_config = snapshot.get("ai_config", {})
        profile = ai_config.get("profile", {})
        conversations = snapshot.get("conversations", [])[-4:]
        interviews = snapshot.get("interviews", [])[-4:]
        decisions = snapshot.get("job_decisions", [])[-6:]

        knowledge_block = "\n".join(
            f"- {item.title} ({item.kind})：{item.excerpt}" for item in retrieved
        ) or "- 当前没有命中额外知识片段"
        conversation_block = "\n".join(
            f"- {item.get('company', '未知公司')} / {item.get('role', '')}：{item.get('last_message_summary', '')}"
            for item in conversations
        ) or "- 暂无近期会话"
        interview_block = "\n".join(
            f"- {item.get('company', '未知公司')} / {item.get('role', '')}：{item.get('result', 'unknown')} / {item.get('stage', '')}"
            for item in interviews
        ) or "- 暂无面试记录"
        decision_block = "\n".join(
            f"- {item.get('company', '未知公司')} / {item.get('role', '')}：{item.get('current_stage', 'discovered')} / skip={item.get('permanent_skip', False)}"
            for item in decisions
        ) or "- 暂无岗位决策记录"

        return (
            "你是用户的求职 AI 助手，同时也是 AI 自测面板里使用的同一模型。"
            "你的任务是基于当前保存的求职档案、面试记录、会话记忆和岗位决策来回答。"
            "如果用户问你对他的了解程度，要优先总结你掌握到的事实、边界和不确定点，不要编造。"
            f"\n\n用户档案："
            f"\n- 期望城市：{profile.get('preferred_location', '')}"
            f"\n- 期望薪资：{profile.get('desired_salary_min', '')} - {profile.get('desired_salary_max', '')}"
            f"\n- 技能：{', '.join(profile.get('skills', [])) or '暂无'}"
            f"\n- 自我介绍：{profile.get('summary', '') or '暂无'}"
            f"\n\n检索到的知识：\n{knowledge_block}"
            f"\n\n近期会话摘要：\n{conversation_block}"
            f"\n\n面试信息：\n{interview_block}"
            f"\n\n岗位决策：\n{decision_block}"
        )

    def _classify_intent(self, message: str) -> str:
        lowered = message.lower()
        if any(token in lowered for token in ["薪资", "工资", "期望", "package"]):
            return "salary"
        if any(token in lowered for token in ["面试", "约", "时间", "meeting"]):
            return "interview"
        if any(token in lowered for token in ["异地", "搬迁", "remote", "远程"]):
            return "relocation"
        if any(token in lowered for token in ["项目", "经历", "细节", "three.js", "webgl"]):
            return "project_experience"
        return "general_followup"

    def _compose_fallback_reply(self, message: str, intent: str, retrieved: list[KnowledgeMatch]) -> str:
        context_hint = retrieved[0].excerpt if retrieved else "我会结合你当前保存的求职档案、项目经历和会话记录来回答。"

        if intent == "relocation":
            return "我可以结合岗位方向和团队目标来评估是否接受异地或远程安排。" + context_hint
        if intent == "salary":
            return "薪资我更适合结合岗位级别、职责范围和面试进展来沟通，也希望先了解预算范围。" + context_hint
        if intent == "interview":
            return "如果面试时间合适，我可以配合安排，并提前准备相关项目案例和技术细节。" + context_hint
        if intent == "project_experience":
            return "我可以展开讲项目经验，尤其是复杂前端工程、性能优化和协作落地部分。" + context_hint
        if "了解" in message or "认识" in message:
            return "目前我对你的了解主要来自 AI 配置里的个人档案、RAG 知识片段、历史会话和面试记录；如果某些经历没有写入知识库，我就无法准确知道。"
        return "收到，我会基于你当前保存的档案、项目、会话和岗位记录来回答。" + context_hint
