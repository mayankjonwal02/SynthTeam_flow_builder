"""Vector search component — similarity search in a vector database.

Reads vector store config from ai_vectorstore handle.
"""

from typing import Any, Dict
from app.components.base import BaseComponent
from app.components.component_registry import register_component
from app.components.ai.ai_handle_mixin import AIHandleMixin


@register_component("vector_search")
class VectorSearchComponent(BaseComponent, AIHandleMixin):

    async def execute(self, request_data: dict, inputs: Dict[str, Any], config: dict) -> dict:
        from app.ai.vectorstores.registry import get_vectorstore

        merged: dict = {}
        for output in inputs.values():
            if isinstance(output, dict):
                merged.update(output)

        query_vector = merged.get("embedding", [])
        query_text = merged.get("text", merged.get("query", ""))
        top_k = int(config.get("top_k", 5))

        vs_cfg = self.get_vectorstore_config(config) or {}
        provider = vs_cfg.get("provider") or config.get("provider", "qdrant")
        collection = vs_cfg.get("collection") or config.get("collection", "default")

        store_kwargs = {}
        for src in (vs_cfg, config):
            for k, v in src.items():
                if k not in ("__handle_type__", "provider", "collection", "top_k"):
                    store_kwargs.setdefault(k, v)

        store = get_vectorstore(provider, **store_kwargs)

        if provider == "chroma":
            coll = store.get_or_create_collection(collection)
            if query_vector:
                results = coll.query(query_embeddings=[query_vector], n_results=top_k)
            else:
                results = coll.query(query_texts=[query_text], n_results=top_k)
            docs = results.get("documents", [[]])[0]
            metadatas = results.get("metadatas", [[]])[0]
            return {"documents": docs, "metadatas": metadatas, "count": len(docs)}

        if provider == "qdrant" and query_vector:
            results = store.search(
                collection_name=collection,
                query_vector=query_vector,
                limit=top_k,
            )
            docs = [hit.payload.get("text", "") for hit in results]
            return {"documents": docs, "count": len(docs)}

        return {"documents": [], "count": 0, "note": f"Implement search for {provider}"}
