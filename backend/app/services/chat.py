from __future__ import annotations

from ..schemas import ChatReplyResponse, KnowledgeMatch
from .rag import RAGService


class ChatAgentService:
    def __init__(self, rag_service: RAGService) -> None:
        self._rag = rag_service

    def generate_reply(self, message: str) -> ChatReplyResponse:
        intent = self._classify_intent(message)
        retrieved = self._rag.search(message, top_k=4)
        draft = self._compose_reply(message, intent, retrieved)
        suggested_action = "review_then_send" if intent in {"salary", "interview", "relocation"} else "send_now"
        confidence = min(0.98, 0.55 + len(retrieved) * 0.08)

        return ChatReplyResponse(
            user_message=message,
            intent=intent,
            retrieved=retrieved,
            draft_reply=draft,
            suggested_action=suggested_action,
            confidence=round(confidence, 2),
        )

    def _classify_intent(self, message: str) -> str:
        lowered = message.lower()
        if any(token in lowered for token in ["薪资", "工资", "期望", "package"]):
            return "salary"
        if any(token in lowered for token in ["面试", "约", "时间", "meeting"]):
            return "interview"
        if any(token in lowered for token in ["深圳", "异地", "搬迁", "remote"]):
            return "relocation"
        if any(token in lowered for token in ["项目", "细节", "经历", "three.js", "webgl"]):
            return "project_experience"
        return "general_followup"

    def _compose_reply(self, message: str, intent: str, retrieved: list[KnowledgeMatch]) -> str:
        context_hint = retrieved[0].excerpt if retrieved else "我这边会结合你的简历和项目经历来补充。"

        if intent == "relocation":
            return "可以接受阶段性异地协作。如果岗位方向和团队目标匹配，我也愿意认真评估搬迁安排。补充一点，" + context_hint
        if intent == "salary":
            return "薪资我希望先结合岗位级别、职责范围和面试进展来沟通，目前大致区间可以对齐市场中高位。如果方便的话，也想先了解你们这个岗位的预算范围。"
        if intent == "interview":
            return "可以，这个时间我可以先预留出来。你把具体安排发我一下，我会提前准备相关项目案例和技术细节。"
        if intent == "project_experience":
            return "这部分我可以展开讲。我之前在复杂可视化和工程化方向上做过比较多深入工作，尤其是性能优化、渲染链路和协作流程这几块，" + context_hint
        return "收到，我这边理解你的关注点了。我会结合岗位要求把相关经历讲清楚，也欢迎你告诉我团队当前最关心的是哪一段能力。"
