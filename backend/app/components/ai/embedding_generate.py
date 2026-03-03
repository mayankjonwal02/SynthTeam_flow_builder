"""Embedding generation component.

Reads embedding config from ai_embedding handle, falls back to inline config.
"""

from typing import Any, Dict
from app.components.base import BaseComponent
from app.components.component_registry import register_component
from app.components.ai.ai_handle_mixin import AIHandleMixin


@register_component("embedding_generate")
class EmbeddingGenerateComponent(BaseComponent, AIHandleMixin):

    async def execute(self, request_data: dict, inputs: Dict[str, Any], config: dict) -> dict:
        from app.ai.embeddings.registry import get_embeddings
        from app.ai.prompts.template import render_prompt

        merged: dict = {}
        for output in inputs.values():
            if isinstance(output, dict):
                merged.update(output)

        text = config.get("text", "") or merged.get("text", "")
        if not text:
            text = render_prompt(config.get("text_template", "{{input}}"), merged)

        # Handle chunks from text_splitter upstream
        chunks = merged.get("chunks")

        embed_cfg = self.get_embedding_config(config) or {}
        provider = embed_cfg.get("provider") or config.get("provider", "openai")
        api_key = embed_cfg.get("api_key") or config.get("api_key", "")
        model_name = embed_cfg.get("model") or config.get("model")

        embeddings_model = get_embeddings(provider=provider, api_key=api_key, model=model_name)

        if chunks and isinstance(chunks, list):
            vectors = await embeddings_model.aembed_documents(chunks)
            return {
                "embeddings": vectors,
                "chunks": chunks,
                "dimensions": len(vectors[0]) if vectors else 0,
                "count": len(vectors),
            }

        vector = await embeddings_model.aembed_query(text)
        return {"embedding": vector, "dimensions": len(vector), "text": text}
