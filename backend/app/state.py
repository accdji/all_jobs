from __future__ import annotations

import json
from pathlib import Path
from threading import Lock
from typing import Any


class LocalStateStore:
    def __init__(self, file_path: str) -> None:
        self._path = Path(file_path)
        self._lock = Lock()
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            self._write(self._default_state())

    def _default_state(self) -> dict[str, Any]:
        return {
            "login": {"status": "unknown", "last_checked": None},
            "jobs": [],
            "messages": [],
            "knowledge": [],
        }

    def _read(self) -> dict[str, Any]:
        try:
            return json.loads(self._path.read_text(encoding="utf-8"))
        except Exception:
            return self._default_state()

    def _write(self, value: dict[str, Any]) -> None:
        self._path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return self._read()

    def update(self, updater) -> dict[str, Any]:
        with self._lock:
            state = self._read()
            next_state = updater(state)
            self._write(next_state)
            return next_state

    def set_login(self, status: str, last_checked: str | None) -> None:
        self.update(
            lambda state: {
                **state,
                "login": {
                    "status": status,
                    "last_checked": last_checked,
                },
            }
        )

    def set_jobs(self, jobs: list[dict[str, Any]]) -> None:
        self.update(lambda state: {**state, "jobs": jobs})

    def set_messages(self, messages: list[dict[str, Any]]) -> None:
        self.update(lambda state: {**state, "messages": messages})

    def upsert_knowledge(self, chunks: list[dict[str, Any]]) -> None:
        def _merge(state: dict[str, Any]) -> dict[str, Any]:
            existing = {item["id"]: item for item in state.get("knowledge", [])}
            for chunk in chunks:
                existing[chunk["id"]] = chunk
            return {**state, "knowledge": list(existing.values())}

        self.update(_merge)
