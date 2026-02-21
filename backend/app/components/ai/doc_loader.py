"""Document Loader component — loads text from URL, file path, or raw text input."""

import logging
from typing import Any, Dict

from app.components.base import BaseComponent
from app.components.component_registry import register_component

logger = logging.getLogger("uvicorn.error")


@register_component("doc_loader")
class DocLoaderComponent(BaseComponent):

    async def execute(self, request_data: dict, inputs: Dict[str, Any], config: dict) -> dict:
        merged: dict = {}
        for output in inputs.values():
            if isinstance(output, dict):
                merged.update(output)

        source_type = config.get("source_type", "text")
        content = ""

        if source_type == "text":
            content = config.get("text", "") or merged.get("text", "")

        elif source_type == "url":
            url = config.get("url", "") or merged.get("url", "")
            if url:
                try:
                    import requests as req
                    resp = req.get(url, timeout=30)
                    resp.raise_for_status()
                    content = resp.text
                except Exception as exc:
                    logger.error(f"doc_loader URL fetch failed: {exc}")
                    return {"error": str(exc), "documents": [], "source": url}

        elif source_type == "file":
            file_path = config.get("file_path", "") or merged.get("file_path", "")
            if file_path:
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                except Exception as exc:
                    logger.error(f"doc_loader file read failed: {exc}")
                    return {"error": str(exc), "documents": [], "source": file_path}

        return {
            "documents": [content] if content else [],
            "source": config.get("url") or config.get("file_path") or "raw_text",
            "char_count": len(content),
        }
