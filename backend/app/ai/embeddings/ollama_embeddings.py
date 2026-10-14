from app.ai.embeddings.registry import register_embedding_provider
from app.core.config import settings


@register_embedding_provider("ollama")
def create_ollama_embeddings(api_key: str = "", **kwargs):
    from langchain_ollama import OllamaEmbeddings
    return OllamaEmbeddings(
        model=kwargs.get("model", "nomic-embed-text"),
        base_url=kwargs.get("base_url") or settings.OLLAMA_BASE_URL,
    )
