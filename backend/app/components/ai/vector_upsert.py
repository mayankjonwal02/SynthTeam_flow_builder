"""Vector upsert component — insert/update vectors in a vector database.

Reads vector store config from ai_vectorstore handle.
"""

from typing import Any, Dict
from app.components.base import BaseComponent
from app.components.component_registry import register_component
from app.components.ai.ai_handle_mixin import AIHandleMixin


@register_component("vector_upsert")
class VectorUpsertComponent(BaseComponent, AIHandleMixin):

    async def execute(self, request_data: dict, inputs: Dict[str, Any], config: dict) -> dict:
        from app.ai.vectorstores.registry import get_vectorstore

        merged: dict = {}
        for output in inputs.values():
            if isinstance(output, dict):
                merged.update(output)

        vs_cfg = self.get_vectorstore_config(config) or {}
        provider = vs_cfg.get("provider") or config.get("provider", "qdrant")
        collection = vs_cfg.get("collection") or config.get("collection", "default")

        store_kwargs = {}
        for src in (vs_cfg, config):
            for k, v in src.items():
                if k not in ("__handle_type__", "provider", "collection"):
                    store_kwargs.setdefault(k, v)

        store = get_vectorstore(provider, **store_kwargs)

        # Batch upsert from embedding_generate with chunks
        embeddings = merged.get("embeddings")
        chunks = merged.get("chunks")
        if embeddings and chunks and isinstance(embeddings, list):
            metadata = merged.get("metadata", {})
            if provider == "chroma":
                coll = store.get_or_create_collection(collection)
                ids = [str(hash(c))[:16] for c in chunks]
                coll.upsert(
                    ids=ids,
                    embeddings=embeddings,
                    documents=chunks,
                    metadatas=[metadata] * len(chunks) if metadata else None,
                )
                return {"status": "upserted", "collection": collection, "count": len(chunks)}

            if provider == "qdrant":
                from qdrant_client.models import PointStruct
                points = [
                    PointStruct(id=i, vector=vec, payload={"text": txt, **metadata})
                    for i, (vec, txt) in enumerate(zip(embeddings, chunks))
                ]
                store.upsert(collection_name=collection, points=points)
                return {"status": "upserted", "collection": collection, "count": len(points)}

        # Single vector upsert
        vectors = merged.get("embedding") or merged.get("vectors", [])
        text = merged.get("text", "")
        metadata = merged.get("metadata", {})
        doc_id = metadata.get("id", str(hash(text))[:16])

        if provider == "chroma":
            coll = store.get_or_create_collection(collection)
            emb = [vectors] if isinstance(vectors, list) and vectors and isinstance(vectors[0], float) else vectors
            coll.upsert(ids=[doc_id], embeddings=emb, documents=[text], metadatas=[metadata])
            return {"status": "upserted", "collection": collection, "doc_id": doc_id}

        if provider == "qdrant":
            from qdrant_client.models import PointStruct
            point = PointStruct(id=abs(hash(doc_id)) % (2**63), vector=vectors, payload={"text": text, **metadata})
            store.upsert(collection_name=collection, points=[point])
            return {"status": "upserted", "collection": collection, "doc_id": doc_id}

        return {"status": "upserted", "provider": provider, "note": "Generic upsert"}
