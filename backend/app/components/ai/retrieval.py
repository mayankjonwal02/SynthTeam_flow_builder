"""RAG Retrieval component — embed query, search vector DB, return context.

Reads embedding config from ai_embedding handle, vector store from ai_vectorstore handle.
"""

from typing import Any, Dict
from app.components.base import BaseComponent
from app.components.component_registry import register_component
from app.components.ai.ai_handle_mixin import AIHandleMixin


@register_component("retrieval")
class RetrievalComponent(BaseComponent, AIHandleMixin):

    async def execute(self, request_data: dict, inputs: Dict[str, Any], config: dict) -> dict:
        from app.ai.embeddings.registry import get_embeddings
        from app.ai.vectorstores.registry import get_vectorstore

        merged: dict = {}
        for output in inputs.values():
            if isinstance(output, dict):
                merged.update(output)

        query = merged.get("query", merged.get("text", merged.get("input", "")))
        top_k = int(config.get("top_k") or 5)

        embed_cfg = self.get_embedding_config(config) or {}
        embed_provider = embed_cfg.get("provider") or config.get("embedding_provider", "openai")
        embed_api_key = embed_cfg.get("api_key") or config.get("api_key", "")
        embed_model_name = embed_cfg.get("model") or config.get("embedding_model")

        embed_model = get_embeddings(
            provider=embed_provider,
            api_key=embed_api_key,
            model=embed_model_name,
        )
        query_vector = await embed_model.aembed_query(query)

        vs_cfg = self.get_vectorstore_config(config) or {}
        vs_provider = vs_cfg.get("provider") or config.get("vector_provider", "qdrant")
        collection = vs_cfg.get("collection") or config.get("collection", "default")

        store_kwargs = {}
        for src in (vs_cfg, config):
            for k, v in src.items():
                if k not in ("__handle_type__", "provider", "collection", "top_k", "api_key",
                             "embedding_provider", "embedding_model", "vector_provider"):
                    store_kwargs.setdefault(k, v)

        store = get_vectorstore(vs_provider, **store_kwargs)

        if vs_provider == "chroma":
            coll = store.get_or_create_collection(collection)
            results = coll.query(query_embeddings=[query_vector], n_results=top_k)
            docs = results.get("documents", [[]])[0]
            context = "\n\n".join(docs)
            return {"context": context, "documents": docs, "query": query, "count": len(docs)}

        if vs_provider == "qdrant":
            from qdrant_client.models import PointStruct
            results = store.search(
                collection_name=collection,
                query_vector=query_vector,
                limit=top_k,
            )
            docs = [hit.payload.get("text", "") for hit in results]
            context = "\n\n".join(docs)
            return {"context": context, "documents": docs, "query": query, "count": len(docs)}

        return {"context": "", "documents": [], "query": query, "count": 0}
