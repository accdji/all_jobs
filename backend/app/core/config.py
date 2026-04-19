from __future__ import annotations

from pydantic import BaseModel


class Settings(BaseModel):
    api_title: str = "Boss Agent Backend"
    frontend_origin: str = "http://localhost:3000"
    boss_base_url: str = "https://www.zhipin.com"
    browser_state_dir: str = ".runtime/playwright"
    browser_headless: bool = False
    vector_store_backend: str = "memory"
    pgvector_dsn: str | None = None
    state_file: str = ".runtime/agent-state.json"


settings = Settings()
