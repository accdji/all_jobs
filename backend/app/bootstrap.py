from __future__ import annotations

from .schemas import (
    AIConfigResponse,
    ChatHistoryItem,
    ChatMessage,
    ChatResponse,
    HeroBlock,
    InterviewBoard,
    InterviewCard,
    InterviewsResponse,
    JobCard,
    JobDetail,
    JobsResponse,
    JobSummary,
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


def seed_overview() -> OverviewResponse:
    return OverviewResponse(
        hero=HeroBlock(
            title="求职自动化概览",
            subtitle="AI 助手正在为您筛选、沟通并准备最值得投入的高匹配岗位。",
            status="Agent Alpha 正在扫描",
        ),
        stats=[
            StatBlock(label="已扫描职位", value="1,284", delta="+18%"),
            StatBlock(label="自动沟通中", value="42", delta="今天 +9"),
            StatBlock(label="面试邀约率", value="88%", delta="近 7 天"),
            StatBlock(label="简历匹配分", value="94", delta="最新版本"),
        ],
        pipeline=[
            PipelineItem(
                company="深途智能",
                role="资深前端工程师",
                salary="35k-50k",
                stage="AI 已生成首轮话术",
                summary="偏地图可视化与多模态交互，匹配你在复杂可视化和性能优化上的经历。",
                message="我过去做过高频实时交互工作台，对复杂数据可视化和前端工程化比较熟，看到贵司的智能座舱方向挺感兴趣。",
            ),
            PipelineItem(
                company="矩阵云图",
                role="Web 可视化专家",
                salary="40k-60k",
                stage="HR 已回复",
                summary="关注 Three.js、数据产品和低延迟渲染链路，适合展开项目案例沟通。",
                message="可以接受线下面试，另外我有一套基于 WebGL 的性能压测经验，应该能和你们当前场景对上。",
            ),
        ],
        threads=[
            ThreadItem(
                company="腾讯 HR",
                time="10:13",
                incoming="看到了，简历很优秀。我们目前团队在深圳，接受异地办公或者搬迁吗？",
                reply="可以接受阶段性异地协作，如果岗位和团队方向匹配，也愿意认真评估搬迁安排。",
            ),
            ThreadItem(
                company="字节跳动 HR",
                time="09:46",
                incoming="你好，关于简历中的微服务治理部分，想深入聊聊细节。",
                reply="可以，我整理一下项目里关于发布链路、容量评估和故障回滚的做法，面试里可以展开讲。",
            ),
        ],
        insight="过去 24 小时内，AI 助手发现 AI 基础设施和企业服务岗位的回复率明显更高，已上调对可视化工程化和系统设计经验的匹配权重。",
    )


def seed_chat() -> ChatResponse:
    return ChatResponse(
        history=[
            ChatHistoryItem(title="资深前端开发职位", preview="已为您筛选了 3 个匹配度超过 90% 的岗位。", time="10 分钟前", active=True),
            ChatHistoryItem(title="产品经理校招", preview="字节跳动、腾讯等大厂的最新岗位已经整理完成。", time="昨天", active=False),
            ChatHistoryItem(title="简历修改意见", preview="关于项目经历的量化表达，我补了一版更锋利的写法。", time="3 月 12 日", active=False),
        ],
        messages=[
            ChatMessage(
                speaker="user",
                content="我想找一些 Base 在北京，薪资在 30k-50k 之间的资深前端岗位，最好是自动驾驶或 AI 相关公司。",
                time="10:42",
            ),
            ChatMessage(
                speaker="assistant",
                content="没问题。我已经根据你的要求筛到 2 个值得优先沟通的机会，并补了第一轮话术。你更偏技术深挖还是希望我先帮你推进回复率？",
                time="10:43",
            ),
        ],
        recommendations=[
            RecommendationItem(title="资深前端工程师（L6）", company="某自动驾驶独角兽 · 北京", tags=["React", "Three.js", "40k-60k"], score=98),
            RecommendationItem(title="可视化开发专家", company="领先 AI 大模型公司 · 北京", tags=["WebGL", "Data Viz", "35k-55k"], score=92),
        ],
        radar=RadarSummary(
            axes=["技术栈", "业务", "工程化", "管理"],
            score=94,
            tip="你的 Three.js 和复杂交互经验与自动驾驶岗位的感知可视化需求高度契合，建议在简历里强调性能指标。",
        ),
    )


def seed_jobs() -> JobsResponse:
    return JobsResponse(
        summary=JobSummary(count="1,284", keyword="资深前端 / AI 可视化 / 北京"),
        filters=["北京", "30k-50k", "前端", "AI 相关", "支持远程沟通"],
        jobs=[
            JobCard(company="深途智能", role="全栈开发工程师（AI方向）", salary="35k-50k", location="北京", tags=["React", "Node.js", "模型工作台"], summary="面向内部智能体调度平台，负责前后端联动与控制台体验。", score=91),
            JobCard(company="启明视觉", role="资深交互设计工程师", salary="28k-45k", location="北京", tags=["Design System", "AI 产品", "C 端"], summary="偏设计工程一体化，强调复杂流程的体验梳理和组件化落地。", score=84),
            JobCard(company="矩阵云图", role="Web 可视化专家", salary="40k-60k", location="北京", tags=["WebGL", "Three.js", "实时渲染"], summary="重点在大屏和实时渲染链路，对性能和工程化要求很高。", score=95),
        ],
        detail=JobDetail(
            role="资深交互设计师",
            company="启明视觉",
            salary="30k-45k",
            meta=["北京", "3-5 年", "本科及以上", "全职"],
            description=[
                "负责 AI 产品核心功能的交互设计与迭代。",
                "需要和前端、算法、运营一起推进复杂流程落地。",
                "有大模型产品或设计工程协作经验者优先。",
            ],
        ),
    )


def seed_ai_config() -> AIConfigResponse:
    return AIConfigResponse(
        models=[
            ModelOption(name="GPT-4o", provider="OpenAI", active=True),
            ModelOption(name="Claude 3.5", provider="Anthropic", active=False),
            ModelOption(name="Gemini Pro", provider="Google", active=False),
        ],
        toggles=[
            ToggleOption(title="智能屏蔽被拒企业", description="自动识别近期拒绝记录，3 个月内降低重复沟通频率。", enabled=True),
            ToggleOption(title="跳过非活跃 HR", description="根据历史回复速度筛除低互动人群，节省投递次数。", enabled=True),
            ToggleOption(title="自动优化投递话术", description="根据每个岗位的 JD 关键词重组简历摘要与招呼语。", enabled=False),
        ],
        push=[
            PushOption(label="飞书 / 钉钉", enabled=True),
            PushOption(label="微信推送", enabled=True),
            PushOption(label="邮件摘要", enabled=False),
        ],
        status=RuntimeStatus(load="12%", credits="$42.80", window="预计可维持 18 天自动化运行"),
    )


def seed_interviews() -> InterviewsResponse:
    return InterviewsResponse(
        pending_count=3,
        cards=[
            InterviewCard(company="Spotify", role="高级产品设计师", mode="Google Meet", time="2026-04-24 15:30", reason="该职位与您在流媒体增长和用户留存项目中的经验重合度达到 94%，HR 明确提到了你对社交功能的理解。", excerpt="您好，我看过您的简历，非常出色。希望能与您约个时间深入聊聊我们最近的云端迁移计划。"),
            InterviewCard(company="Google", role="交互开发工程师（Contract）", mode="现场技术面", time="2026-04-27 10:00", reason="你的设计工程和前端系统化能力对这个岗位非常对口，建议优先确认。", excerpt="想和你进一步聊聊系统组件和视觉规范如何在大团队中稳定执行。"),
        ],
        board=InterviewBoard(
            weekly="04",
            match="88%",
            resume_progress="100%",
            upcoming=[
                UpcomingInterview(date="11/12", title="字节跳动 · 终面", time="14:00 - 15:30 · 线上会议"),
                UpcomingInterview(date="11/15", title="蚂蚁集团 · 技术面", time="10:00 - 11:30 · 杭州 A1"),
            ],
            tip="下周有 3 场面试集中在下午，建议提前准备系统架构和项目指标细节。",
        ),
    )


def seed_resume_lab() -> ResumeLabResponse:
    return ResumeLabResponse(
        score=94,
        quality="优秀",
        analysis="你的项目经验部分已经很有力度，但技术栈分组和量化表达还能更锋利。AI 已准备针对高级产品经理和设计工程岗位生成两套版本。",
        variants=[
            ResumeVariant(name="高级产品经理_v3", tag="当前主版本"),
            ResumeVariant(name="前端 / 设计工程_v2", tag="推荐投递 AI 产品"),
            ResumeVariant(name="原始简历_v1", tag="上传备份"),
        ],
        pitches=[
            PitchVariant(label="AI 产品", content="你好，我过去的工作长期围绕复杂信息架构和高频协作流程展开，看到贵司这个岗位后，感觉我在产品落地和跨团队协同上的经验可以比较快地进入状态。"),
            PitchVariant(label="企业服务", content="我一直在做对稳定性、效率和可扩展性要求比较高的产品形态，也比较擅长把复杂问题拆成用户可以直接感知的体验价值。"),
            PitchVariant(label="设计工程", content="我对设计系统和工程落地之间的断层特别敏感，过去做过从规范到组件库再到业务验证的完整闭环，这也是我关注这个岗位的主要原因。"),
        ],
        progress=68,
    )


def seed_knowledge() -> list[KnowledgeChunk]:
    return [
        KnowledgeChunk(
            id="resume-front-1",
            title="前端主简历",
            kind="resume",
            content="候选人擅长 React、TypeScript、Three.js、复杂工作台和工程化体系建设，做过高频数据可视化和性能优化。",
            tags=["react", "three.js", "前端", "性能优化"],
        ),
        KnowledgeChunk(
            id="project-auto-drive",
            title="自动驾驶可视化项目",
            kind="project",
            content="负责感知结果可视化平台，从渲染链路、地图交互到帧率优化都参与过，重点解决大规模点云和轨迹渲染卡顿问题。",
            tags=["自动驾驶", "可视化", "webgl"],
        ),
        KnowledgeChunk(
            id="preference-city",
            title="求职偏好",
            kind="preference",
            content="优先北京岗位，可接受阶段性异地协作；薪资目标 30k-50k，更偏 AI、自动驾驶、企业服务平台类岗位。",
            tags=["北京", "薪资", "偏好"],
        ),
        KnowledgeChunk(
            id="faq-salary",
            title="常见问题：薪资与到岗",
            kind="faq",
            content="谈薪时先确认岗位级别和期望范围；到岗时间通常以两到四周为宜，避免承诺过于激进的时间表。",
            tags=["薪资", "到岗"],
        ),
        KnowledgeChunk(
            id="conversation-shenzhen",
            title="历史对话：异地办公",
            kind="conversation",
            content="对于深圳岗位，可以表达接受阶段性异地协作；若岗位和团队方向匹配，愿意认真评估搬迁安排。",
            tags=["异地", "深圳", "搬迁"],
        ),
    ]
