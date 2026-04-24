from __future__ import annotations

import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi import UploadFile
from markitdown import MarkItDown

from ..schemas import KnowledgeChunk, KnowledgeUploadResponse


class DocumentIngestService:
    def __init__(self) -> None:
        self._converter = MarkItDown()

    async def convert_upload(
        self,
        upload: UploadFile,
        *,
        kind: str,
        title: str | None = None,
        tags: list[str] | None = None,
    ) -> tuple[list[KnowledgeChunk], KnowledgeUploadResponse]:
        filename = upload.filename or "document"
        safe_title = (title or Path(filename).stem or "Imported Document").strip()
        safe_tags = [item.strip() for item in (tags or []) if item.strip()]

        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir) / filename
            temp_path.write_bytes(await upload.read())
            result = self._converter.convert(str(temp_path))

        markdown = str(getattr(result, "text_content", "") or "").strip()
        chunks = self._build_chunks(markdown, safe_title, kind, safe_tags)
        response = KnowledgeUploadResponse(
            source="markitdown",
            filename=filename,
            title=safe_title,
            kind=kind,
            ingested=len(chunks),
            chunks=len(chunks),
            tags=safe_tags,
        )
        return chunks, response

    def _build_chunks(
        self,
        markdown: str,
        title: str,
        kind: str,
        tags: list[str],
        *,
        max_chars: int = 1200,
    ) -> list[KnowledgeChunk]:
        normalized = "\n".join(line.rstrip() for line in markdown.splitlines()).strip()
        if not normalized:
            return []

        sections: list[str] = []
        buffer: list[str] = []
        current_len = 0

        for paragraph in [part.strip() for part in normalized.split("\n\n") if part.strip()]:
            projected = current_len + len(paragraph) + (2 if buffer else 0)
            if buffer and projected > max_chars:
                sections.append("\n\n".join(buffer))
                buffer = [paragraph]
                current_len = len(paragraph)
                continue

            buffer.append(paragraph)
            current_len = projected

        if buffer:
            sections.append("\n\n".join(buffer))

        return [
            KnowledgeChunk(
                id=self._build_chunk_id(title, index, section),
                title=f"{title} / Part {index + 1}",
                kind=kind,
                content=section,
                tags=tags,
            )
            for index, section in enumerate(sections)
        ]

    def _build_chunk_id(self, title: str, index: int, section: str) -> str:
        digest = hashlib.sha1(f"{title}:{index}:{section[:80]}".encode("utf-8")).hexdigest()[:16]
        return f"upload-{digest}"
