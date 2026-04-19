from __future__ import annotations

from ..schemas import KnowledgeMatch
from .vector_store import VectorStore


class RAGService:
    def __init__(self, store: VectorStore) -> None:
        self._store = store

    def search(self, query: str, top_k: int = 4) -> list[KnowledgeMatch]:
        return self._store.search(query, top_k)
