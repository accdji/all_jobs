from __future__ import annotations

from abc import ABC, abstractmethod
from collections import Counter
from re import findall

from ..schemas import KnowledgeChunk, KnowledgeMatch


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in findall(r"[\w\u4e00-\u9fff\.\-]+", text)]


class VectorStore(ABC):
    @abstractmethod
    def upsert(self, chunks: list[KnowledgeChunk]) -> int:
        raise NotImplementedError

    @abstractmethod
    def search(self, query: str, top_k: int = 4) -> list[KnowledgeMatch]:
        raise NotImplementedError


class InMemoryVectorStore(VectorStore):
    def __init__(self, chunks: list[KnowledgeChunk] | None = None) -> None:
        self._chunks: dict[str, KnowledgeChunk] = {}
        if chunks:
            self.upsert(chunks)

    def upsert(self, chunks: list[KnowledgeChunk]) -> int:
        for chunk in chunks:
            self._chunks[chunk.id] = chunk
        return len(chunks)

    def search(self, query: str, top_k: int = 4) -> list[KnowledgeMatch]:
        query_tokens = tokenize(query)
        query_counts = Counter(query_tokens)
        lowered_query = query.lower()
        scored: list[KnowledgeMatch] = []

        for doc in self._chunks.values():
            haystack_tokens = tokenize(f"{doc.title} {doc.content} {' '.join(doc.tags)}")
            haystack_counts = Counter(haystack_tokens)
            overlap = sum(min(query_counts[token], haystack_counts[token]) for token in query_counts)
            substring_hits = 0
            for value in [doc.title, doc.content, *doc.tags]:
                lowered_value = value.lower()
                if lowered_value in lowered_query or any(token in lowered_value for token in query_tokens if len(token) >= 2):
                    substring_hits += 1

            total_score = overlap + substring_hits
            if total_score == 0:
                continue

            scored.append(
                KnowledgeMatch(
                    id=doc.id,
                    title=doc.title,
                    kind=doc.kind,
                    score=round(total_score / max(len(query_tokens), 1), 3),
                    excerpt=doc.content[:120],
                    tags=doc.tags,
                )
            )

        scored.sort(key=lambda item: item.score, reverse=True)
        return scored[:top_k]


class PgVectorStore(VectorStore):
    def __init__(self, dsn: str | None) -> None:
        self._dsn = dsn

    def upsert(self, chunks: list[KnowledgeChunk]) -> int:
        raise NotImplementedError("pgvector backend not wired yet; use InMemoryVectorStore for now")

    def search(self, query: str, top_k: int = 4) -> list[KnowledgeMatch]:
        raise NotImplementedError("pgvector backend not wired yet; use InMemoryVectorStore for now")
