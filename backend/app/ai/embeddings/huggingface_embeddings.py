from app.ai.embeddings.registry import register_embedding_provider


@register_embedding_provider("huggingface")
def create_hf_embeddings(api_key: str = "", **kwargs):
    from langchain_community.embeddings import HuggingFaceEmbeddings
    return HuggingFaceEmbeddings(
        model_name=kwargs.get("model", "sentence-transformers/all-MiniLM-L6-v2"),
    )
