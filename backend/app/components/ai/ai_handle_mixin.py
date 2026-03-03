"""Mixin for AI components to read typed-handle inputs from __ai_inputs__."""

from typing import Any, Dict, List, Optional


class AIHandleMixin:
    """Helpers to extract config injected by typed AI handles."""

    @staticmethod
    def _ai(config: dict) -> Dict[str, list]:
        return config.get("__ai_inputs__", {})

    @staticmethod
    def get_model_config(config: dict) -> Optional[dict]:
        models = AIHandleMixin._ai(config).get("ai_model", [])
        return models[0] if models else None

    @staticmethod
    def get_tool_configs(config: dict) -> List[dict]:
        return AIHandleMixin._ai(config).get("ai_tool", [])

    @staticmethod
    def get_memory_config(config: dict) -> Optional[dict]:
        mems = AIHandleMixin._ai(config).get("ai_memory", [])
        return mems[0] if mems else None

    @staticmethod
    def get_structure_config(config: dict) -> Optional[dict]:
        structs = AIHandleMixin._ai(config).get("ai_structure", [])
        return structs[0] if structs else None

    @staticmethod
    def get_subagent_configs(config: dict) -> List[dict]:
        return AIHandleMixin._ai(config).get("ai_subagent", [])

    @staticmethod
    def get_embedding_config(config: dict) -> Optional[dict]:
        embeds = AIHandleMixin._ai(config).get("ai_embedding", [])
        return embeds[0] if embeds else None

    @staticmethod
    def get_vectorstore_config(config: dict) -> Optional[dict]:
        stores = AIHandleMixin._ai(config).get("ai_vectorstore", [])
        return stores[0] if stores else None

    @staticmethod
    def enrich_kb_tool_config(kw: dict, embed_cfg: dict, vs_cfg: dict) -> dict:
        """Inject shared embedding / vectorstore config into a knowledge_base
        tool's kwargs when the tool's own fields are empty."""
        if embed_cfg:
            kw.setdefault("embedding_provider", embed_cfg.get("provider", ""))
            if not kw.get("embedding_api_key"):
                kw["embedding_api_key"] = embed_cfg.get("api_key", "")
            if not kw.get("embedding_model"):
                kw["embedding_model"] = embed_cfg.get("model", "")
        if vs_cfg:
            kw.setdefault("vectorstore_provider", vs_cfg.get("provider", ""))
            if not kw.get("vectorstore_url"):
                kw["vectorstore_url"] = vs_cfg.get("url", "")
            if not kw.get("vectorstore_api_key"):
                kw["vectorstore_api_key"] = vs_cfg.get("api_key", "")
            if not kw.get("collection"):
                kw["collection"] = vs_cfg.get("collection", "default")
        return kw
