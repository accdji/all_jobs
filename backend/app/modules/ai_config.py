from __future__ import annotations

from ..schemas import AIProviderOption


def build_default_subscriptions() -> list[dict]:
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


def build_default_ai_config_state() -> dict:
    return {
        "provider": "openai",
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-4.1-mini",
        "profile": {
            "desired_salary_min": "",
            "desired_salary_max": "",
            "preferred_location": "北京",
            "skills": [],
            "summary": "",
        },
        "subscriptions": build_default_subscriptions(),
    }


def build_provider_options() -> list[AIProviderOption]:
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
