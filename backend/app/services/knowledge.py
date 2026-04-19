from __future__ import annotations

from ..schemas import KnowledgeChunk, RAGSearchResponse
from .vector_store import VectorStore


class KnowledgeService:
    def __init__(self, store: VectorStore) -> None:
        self._store = store

    def ingest(self, chunks: list[KnowledgeChunk]) -> dict:
        count = self._store.upsert(chunks)
        return {"ingested": count, "source": "api"}

    def search(self, query: str, top_k: int) -> RAGSearchResponse:
        return RAGSearchResponse(query=query, results=self._store.search(query, top_k))
