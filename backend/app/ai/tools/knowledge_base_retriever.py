"""Knowledge Base Retriever tool — RAG retrieval for agents.

Embeds the query, searches a vector store collection, and returns
concatenated document chunks as context for the agent.
"""

import asyncio
import logging

from app.ai.tools.registry import register_tool
from app.ai.tools.base import SynthTool

logger = logging.getLogger("uvicorn.error")

_DEFAULT_DESC = (
    "Search the knowledge base for relevant information. "
    "Input: a natural-language search query string."
)


@register_tool("knowledge_base")
class KnowledgeBaseRetrieverTool(SynthTool):
    name: str = "knowledge_base"
    description: str = _DEFAULT_DESC

    collection: str = "default"
    top_k: int = 5
    data_description: str = ""

    embedding_provider: str = "openai"
    embedding_api_key: str = ""
    embedding_model: str = ""

    vectorstore_provider: str = "qdrant"
    vectorstore_url: str = ""
    vectorstore_api_key: str = ""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.data_description:
            self.description = (
                f"Search the knowledge base for relevant information about "
                f"{self.data_description}. Input: a search query string."
            )

    def _run(self, query: str) -> str:
        return asyncio.get_event_loop().run_until_complete(self._arun(query))

    async def _arun(self, query: str) -> str:
        from app.ai.embeddings.registry import get_embeddings
        from app.ai.vectorstores.registry import get_vectorstore

        if not query or not query.strip():
            return "No query provided."

        try:
            embed_model = get_embeddings(
                provider=self.embedding_provider,
                api_key=self.embedding_api_key,
                model=self.embedding_model or None,
            )
            query_vector = await embed_model.aembed_query(query)
        except Exception as exc:
            logger.error(f"KB tool embedding failed: {exc}")
            return f"Embedding failed: {exc}"

        store_kwargs: dict = {}
        if self.vectorstore_url:
            store_kwargs["url"] = self.vectorstore_url
        if self.vectorstore_api_key:
            store_kwargs["api_key"] = self.vectorstore_api_key

        try:
            store = get_vectorstore(self.vectorstore_provider, **store_kwargs)
        except Exception as exc:
            logger.error(f"KB tool vector store init failed: {exc}")
            return f"Vector store connection failed: {exc}"

        try:
            docs = self._search(store, query_vector, query)
        except Exception as exc:
            logger.error(f"KB tool search failed: {exc}")
            return f"Search failed: {exc}"

        if not docs:
            return "No relevant documents found."

        return "\n\n---\n\n".join(docs)

    def _search(self, store, query_vector: list, query_text: str) -> list[str]:
        if self.vectorstore_provider == "chroma":
            coll = store.get_or_create_collection(self.collection)
            results = coll.query(
                query_embeddings=[query_vector], n_results=self.top_k
            )
            return results.get("documents", [[]])[0]

        if self.vectorstore_provider == "qdrant":
            results = store.search(
                collection_name=self.collection,
                query_vector=query_vector,
                limit=self.top_k,
            )
            return [hit.payload.get("text", "") for hit in results]

        if self.vectorstore_provider == "pinecone":
            results = store.query(
                vector=query_vector, top_k=self.top_k, include_metadata=True
            )
            return [
                m.get("metadata", {}).get("text", "")
                for m in results.get("matches", [])
            ]

        return []
