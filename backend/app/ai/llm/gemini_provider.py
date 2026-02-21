from app.ai.llm.registry import register_llm_provider


@register_llm_provider("gemini")
def create_gemini_llm(model: str, api_key: str, **kwargs):
    from langchain_google_genai import ChatGoogleGenerativeAI
    return ChatGoogleGenerativeAI(
        model=model,
        google_api_key=api_key,
        temperature=kwargs.get("temperature", 0.7),
        max_output_tokens=kwargs.get("max_tokens"),
    )
