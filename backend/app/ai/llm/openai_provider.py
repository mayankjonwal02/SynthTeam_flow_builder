from app.ai.llm.registry import register_llm_provider


@register_llm_provider("openai")
def create_openai_llm(model: str, api_key: str, **kwargs):
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(
        model=model,
        **({"api_key": api_key} if api_key else {}),  # empty -> provider env var
        temperature=kwargs.get("temperature", 0.7),
        max_tokens=kwargs.get("max_tokens"),
    )
