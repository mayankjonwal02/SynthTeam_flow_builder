from app.ai.vectorstores.registry import register_vectorstore


@register_vectorstore("chroma")
def create_chroma(**kwargs):
    import chromadb
    if kwargs.get("host"):
        return chromadb.HttpClient(host=kwargs["host"], port=kwargs.get("port", 8000))
    return chromadb.Client()
