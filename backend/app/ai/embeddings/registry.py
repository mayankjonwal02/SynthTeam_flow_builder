"""Embedding Provider Registry."""

import logging
from typing import Any, Callable, Dict

logger = logging.getLogger("uvicorn.error")

EMBEDDING_REGISTRY: Dict[str, Callable] = {}


def register_embedding_provider(name: str):
    def decorator(factory_fn: Callable):
        EMBEDDING_REGISTRY[name] = factory_fn
        logger.info(f"Registered embedding provider: {name}")
        return factory_fn
    return decorator


def get_embeddings(provider: str, api_key: str = "", **kwargs) -> Any:
    factory = EMBEDDING_REGISTRY.get(provider)
    if factory is None:
        raise ValueError(f"Embedding provider '{provider}' not registered. Available: {list(EMBEDDING_REGISTRY.keys())}")
    return factory(api_key=api_key, **kwargs)
