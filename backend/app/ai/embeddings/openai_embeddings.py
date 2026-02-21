from app.ai.embeddings.registry import register_embedding_provider


@register_embedding_provider("openai")
def create_openai_embeddings(api_key: str, **kwargs):
    from langchain_openai import OpenAIEmbeddings
    return OpenAIEmbeddings(
        model=kwargs.get("model", "text-embedding-3-small"),
        api_key=api_key,
    )
