from __future__ import annotations

import os
from typing import ClassVar

from pydantic import BaseModel

from .env import bootstrap_env


bootstrap_env()


class Settings(BaseModel):
    provider_key_envs: ClassVar[dict[str, tuple[str, ...]]] = {
        "openai": ("BOSS_AGENT_API_KEY", "OPENAI_API_KEY"),
        "gemini": ("GEMINI_API_KEY", "GOOGLE_API_KEY"),
        "deepseek": ("DEEPSEEK_API_KEY",),
        "bailian": ("DASHSCOPE_API_KEY", "BAILIAN_API_KEY"),
        "volcengine": ("ARK_API_KEY", "VOLCENGINE_API_KEY"),
        "custom": ("CUSTOM_LLM_API_KEY",),
    }

    api_title: str = "Boss Agent Backend"
    frontend_origin: str = "http://localhost:3000"
    boss_base_url: str = "https://www.zhipin.com"
    browser_state_dir: str = ".runtime/playwright"
    browser_headless: bool = False
    vector_store_backend: str = "memory"
    pgvector_dsn: str | None = None
    state_file: str = ".runtime/agent-state.json"

    def resolve_llm_api_key_env(self, provider: str, custom_env: str | None = None) -> str:
        candidate = (custom_env or "").strip()
        if candidate:
            return candidate

        options = self.provider_key_envs.get(provider, self.provider_key_envs["custom"])
        for env_name in options:
            if os.getenv(env_name):
                return env_name
        return options[0]

    def resolve_llm_api_key(self, provider: str, custom_env: str | None = None) -> str:
        env_name = self.resolve_llm_api_key_env(provider, custom_env)
        return os.getenv(env_name, "")


settings = Settings()
