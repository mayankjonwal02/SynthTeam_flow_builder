"""LLM Provider Registry — decorator-based registration of chat model factories."""

import logging
from typing import Any, Callable, Dict

logger = logging.getLogger("uvicorn.error")

LLM_PROVIDER_REGISTRY: Dict[str, Callable] = {}


def register_llm_provider(name: str):
    """Decorator that registers an LLM provider factory function."""
    def decorator(factory_fn: Callable):
        LLM_PROVIDER_REGISTRY[name] = factory_fn
        logger.info(f"Registered LLM provider: {name}")
        return factory_fn
    return decorator


def get_llm(provider: str, model: str, api_key: str, **kwargs) -> Any:
    """Instantiate a LangChain chat model from the registry."""
    factory = LLM_PROVIDER_REGISTRY.get(provider)
    if factory is None:
        available = list(LLM_PROVIDER_REGISTRY.keys())
        raise ValueError(f"LLM provider '{provider}' not registered. Available: {available}")
    return factory(model=model, api_key=api_key, **kwargs)


def list_llm_providers() -> list:
    return list(LLM_PROVIDER_REGISTRY.keys())
