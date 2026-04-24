from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

LEGACY_PROVIDER_ENV_MAP = {
    "openai": "BOSS_AGENT_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
    "bailian": "DASHSCOPE_API_KEY",
    "volcengine": "ARK_API_KEY",
    "custom": "CUSTOM_LLM_API_KEY",
}


def bootstrap_env() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    example_path = repo_root / ".env.example"
    env_path = repo_root / ".env"
    state_path = repo_root / ".runtime" / "agent-state.json"

    if not env_path.exists() and example_path.exists():
        env_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(example_path, env_path)

    _migrate_legacy_llm_key(state_path, env_path)

    if env_path.exists():
        _load_env_file(env_path)


def upsert_env_value(key: str, value: str) -> None:
    repo_root = Path(__file__).resolve().parents[3]
    example_path = repo_root / ".env.example"
    env_path = repo_root / ".env"

    if not env_path.exists() and example_path.exists():
        env_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(example_path, env_path)

    if not env_path.exists():
        env_path.parent.mkdir(parents=True, exist_ok=True)
        env_path.write_text("", encoding="utf-8")

    _upsert_env_value(env_path, key, value)
    os.environ[key] = value


def _load_env_file(path: Path) -> None:
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        env_key = key.strip()
        if not env_key or env_key in os.environ:
            continue
        os.environ[env_key] = _strip_quotes(value.strip())


def _strip_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def _migrate_legacy_llm_key(state_path: Path, env_path: Path) -> None:
    if not state_path.exists() or not env_path.exists():
        return

    try:
        snapshot = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return

    ai_config = snapshot.get("ai_config") or {}
    legacy_key = str(ai_config.get("api_key") or "").strip()
    if not legacy_key:
        return

    provider = str(ai_config.get("provider") or "custom").strip().lower()
    env_name = LEGACY_PROVIDER_ENV_MAP.get(provider, "CUSTOM_LLM_API_KEY")
    if os.getenv(env_name):
        return

    _upsert_env_value(env_path, env_name, legacy_key)


def _upsert_env_value(path: Path, key: str, value: str) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    target_prefix = f"{key}="
    next_lines: list[str] = []
    replaced = False

    for line in lines:
        if line.startswith(target_prefix):
            next_lines.append(f"{key}={value}")
            replaced = True
        else:
            next_lines.append(line)

    if not replaced:
        if next_lines and next_lines[-1] != "":
            next_lines.append("")
        next_lines.append(f"{key}={value}")

    path.write_text("\n".join(next_lines) + "\n", encoding="utf-8")
