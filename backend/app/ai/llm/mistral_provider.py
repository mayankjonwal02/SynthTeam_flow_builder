from app.ai.llm.registry import register_llm_provider


@register_llm_provider("mistral")
def create_mistral_llm(model: str, api_key: str, **kwargs):
    from langchain_mistralai import ChatMistralAI
    return ChatMistralAI(
        model=model,
        api_key=api_key,
        temperature=kwargs.get("temperature", 0.7),
        max_tokens=kwargs.get("max_tokens"),
    )
