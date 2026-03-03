from app.ai.llm.registry import register_llm_provider


@register_llm_provider("groq")
def create_groq_llm(model: str, api_key: str, **kwargs):
    from langchain_groq import ChatGroq
    return ChatGroq(
        model=model,
        api_key=api_key,
        temperature=kwargs.get("temperature", 0.7),
        max_tokens=kwargs.get("max_tokens", 8192),
    )
