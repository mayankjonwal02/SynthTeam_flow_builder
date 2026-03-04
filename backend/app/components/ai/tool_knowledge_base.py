"""Knowledge Base tool node — RAG retrieval tool for agents, connects via ai_tool handle.

This tool allows agents to query a vector store for relevant documents.
Supports inline config for embedding/vectorstore, or inherits from the
parent agent's ai_embedding / ai_vectorstore handles at tool-creation time.
"""

from typing import Any, Dict
from app.components.base import BaseComponent
from app.components.component_registry import register_component


@register_component("tool_knowledge_base")
class ToolKnowledgeBaseComponent(BaseComponent):

    async def execute(self, request_data: dict, inputs: Dict[str, Any], config: dict) -> dict:
        return {
            "__handle_type__": "ai_tool",
            "tool_name": "knowledge_base",
            "collection": config.get("collection", "default"),
            "top_k": int(config.get("top_k") or 5),
            "data_description": config.get("data_description", ""),
            "embedding_provider": config.get("embedding_provider", "openai"),
            "embedding_api_key": config.get("embedding_api_key", ""),
            "embedding_model": config.get("embedding_model", ""),
            "vectorstore_provider": config.get("vectorstore_provider", "qdrant"),
            "vectorstore_url": config.get("vectorstore_url", ""),
            "vectorstore_api_key": config.get("vectorstore_api_key", ""),
        }
