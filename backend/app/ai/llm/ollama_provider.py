from app.ai.llm.registry import register_llm_provider


@register_llm_provider("ollama")
def create_ollama_llm(model: str, api_key: str = "", **kwargs):
    from langchain_ollama import ChatOllama
    return ChatOllama(
        model=model,
        base_url=kwargs.get("base_url", "http://localhost:11434"),
        temperature=kwargs.get("temperature", 0.7),
    )
