"""
Centralized component registry using a decorator pattern.

Components self-register when their module is imported:

    @register_component("my_component")
    class MyComponent(BaseComponent):
        ...
"""

import logging
from typing import Dict, Type

logger = logging.getLogger("uvicorn.error")

COMPONENT_REGISTRY: Dict[str, Type] = {}


def register_component(name: str):
    """Decorator that registers a component class by name."""
    def decorator(cls):
        COMPONENT_REGISTRY[name] = cls
        logger.info(f"Registered component: {name}")
        return cls
    return decorator


def get_component(name: str):
    """Instantiate and return a component by its registered name."""
    cls = COMPONENT_REGISTRY.get(name)
    if cls is None:
        raise ValueError(f"Component '{name}' is not registered")
    return cls()


def list_components() -> list:
    """Return all registered component names."""
    return list(COMPONENT_REGISTRY.keys())
