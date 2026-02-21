"""Vector delete component.

Reads vector store config from ai_vectorstore handle.
"""

from typing import Any, Dict
from app.components.base import BaseComponent
from app.components.component_registry import register_component
from app.components.ai.ai_handle_mixin import AIHandleMixin


@register_component("vector_delete")
class VectorDeleteComponent(BaseComponent, AIHandleMixin):

    async def execute(self, request_data: dict, inputs: Dict[str, Any], config: dict) -> dict:
        from app.ai.vectorstores.registry import get_vectorstore

        merged: dict = {}
        for output in inputs.values():
            if isinstance(output, dict):
                merged.update(output)

        doc_ids = merged.get("doc_ids", []) or [merged.get("doc_id", "")]

        vs_cfg = self.get_vectorstore_config(config) or {}
        provider = vs_cfg.get("provider") or config.get("provider", "qdrant")
        collection = vs_cfg.get("collection") or config.get("collection", "default")

        store_kwargs = {}
        for src in (vs_cfg, config):
            for k, v in src.items():
                if k not in ("__handle_type__", "provider", "collection"):
                    store_kwargs.setdefault(k, v)

        store = get_vectorstore(provider, **store_kwargs)

        if provider == "chroma":
            coll = store.get_or_create_collection(collection)
            coll.delete(ids=doc_ids)
            return {"deleted": len(doc_ids), "collection": collection}

        if provider == "qdrant":
            from qdrant_client.models import PointIdsList
            store.delete(
                collection_name=collection,
                points_selector=PointIdsList(points=[int(d) for d in doc_ids if d]),
            )
            return {"deleted": len(doc_ids), "collection": collection}

        return {"deleted": 0, "note": f"Implement delete for {provider}"}
