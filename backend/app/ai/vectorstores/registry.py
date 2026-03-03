"""Vector Store Registry."""

import logging
from typing import Any, Callable, Dict

logger = logging.getLogger("uvicorn.error")

VECTORSTORE_REGISTRY: Dict[str, Callable] = {}


def register_vectorstore(name: str):
    def decorator(factory_fn: Callable):
        VECTORSTORE_REGISTRY[name] = factory_fn
        logger.info(f"Registered vector store: {name}")
        return factory_fn
    return decorator


def get_vectorstore(provider: str, **kwargs) -> Any:
    factory = VECTORSTORE_REGISTRY.get(provider)
    if factory is None:
        raise ValueError(f"Vector store '{provider}' not registered. Available: {list(VECTORSTORE_REGISTRY.keys())}")
    return factory(**kwargs)
