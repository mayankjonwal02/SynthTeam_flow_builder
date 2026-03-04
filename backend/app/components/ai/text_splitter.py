"""Text Splitter component — chunks documents for embedding/vector storage."""

from typing import Any, Dict, List

from app.components.base import BaseComponent
from app.components.component_registry import register_component


def _split_by_chars(text: str, chunk_size: int, overlap: int) -> List[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
        if start >= len(text):
            break
    return [c for c in chunks if c.strip()]


def _split_by_separator(text: str, separator: str, chunk_size: int, overlap: int) -> List[str]:
    parts = text.split(separator)
    chunks = []
    current = ""
    for part in parts:
        candidate = current + separator + part if current else part
        if len(candidate) > chunk_size and current:
            chunks.append(current.strip())
            overlap_text = current[-(overlap):] if overlap else ""
            current = overlap_text + part
        else:
            current = candidate
    if current.strip():
        chunks.append(current.strip())
    return chunks


@register_component("text_splitter")
class TextSplitterComponent(BaseComponent):

    async def execute(self, request_data: dict, inputs: Dict[str, Any], config: dict) -> dict:
        merged: dict = {}
        for output in inputs.values():
            if isinstance(output, dict):
                merged.update(output)

        documents = merged.get("documents", [])
        if isinstance(documents, str):
            documents = [documents]

        strategy = config.get("strategy", "character")
        chunk_size = int(config.get("chunk_size") or 1000)
        overlap = int(config.get("overlap") or 200)
        separator = config.get("separator", "\n\n")

        all_chunks = []
        for doc in documents:
            if not isinstance(doc, str) or not doc.strip():
                continue
            if strategy == "separator":
                chunks = _split_by_separator(doc, separator, chunk_size, overlap)
            else:
                chunks = _split_by_chars(doc, chunk_size, overlap)
            all_chunks.extend(chunks)

        return {
            "chunks": all_chunks,
            "chunk_count": len(all_chunks),
            "strategy": strategy,
        }
