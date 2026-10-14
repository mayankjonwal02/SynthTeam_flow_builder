from app.ai.llm.registry import register_llm_provider


def _ollama_base_url(**kwargs):
    """Resolve Ollama base_url: kwargs first, then settings (Docker: use host.docker.internal)."""
    if kwargs.get("base_url"):
        return kwargs["base_url"]
    try:
        from app.core.config import settings
        return getattr(settings, "OLLAMA_BASE_URL", "http://localhost:11434") or "http://localhost:11434"
    except Exception:
        return "http://localhost:11434"


@register_llm_provider("ollama")
def create_ollama_llm(model: str, api_key: str = "", **kwargs):
    from langchain_ollama import ChatOllama
    base_url = _ollama_base_url(**kwargs)
    # Timeout so we don't hang when Ollama is unreachable (e.g. wrong host in Docker)
    timeout = kwargs.get("timeout", 120)
    return ChatOllama(
        model=model,
        base_url=base_url,
        temperature=kwargs.get("temperature", 0.7),
        # Passed through to the underlying httpx client
        client_kwargs={"timeout": timeout},
    )
