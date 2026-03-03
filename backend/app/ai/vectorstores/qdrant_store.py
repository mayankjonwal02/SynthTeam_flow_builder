from app.ai.vectorstores.registry import register_vectorstore


@register_vectorstore("qdrant")
def create_qdrant(**kwargs):
    from qdrant_client import QdrantClient
    return QdrantClient(
        url=kwargs.get("url", "http://localhost:6333"),
        api_key=kwargs.get("api_key"),
    )
