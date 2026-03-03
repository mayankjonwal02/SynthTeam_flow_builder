from app.ai.vectorstores.registry import register_vectorstore


@register_vectorstore("pinecone")
def create_pinecone(**kwargs):
    from pinecone import Pinecone
    return Pinecone(api_key=kwargs.get("api_key", ""))
