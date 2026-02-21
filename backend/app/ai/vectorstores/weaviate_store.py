from app.ai.vectorstores.registry import register_vectorstore


@register_vectorstore("weaviate")
def create_weaviate(**kwargs):
    import weaviate
    return weaviate.connect_to_local(
        host=kwargs.get("host", "localhost"),
        port=kwargs.get("port", 8080),
    )
