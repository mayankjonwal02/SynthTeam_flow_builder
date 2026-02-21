"""Tool Registry — decorator-based registration of agent tools."""

import logging
from typing import Any, Callable, Dict, List, Type

logger = logging.getLogger("uvicorn.error")

TOOL_REGISTRY: Dict[str, Type] = {}


def register_tool(name: str):
    """Decorator that registers a LangChain-compatible tool class."""
    def decorator(cls):
        TOOL_REGISTRY[name] = cls
        logger.info(f"Registered tool: {name}")
        return cls
    return decorator


def get_tool(name: str, **kwargs) -> Any:
    cls = TOOL_REGISTRY.get(name)
    if cls is None:
        raise ValueError(f"Tool '{name}' not registered. Available: {list(TOOL_REGISTRY.keys())}")
    return cls(**kwargs) if kwargs else cls()


def get_tools(names: List[str], tool_configs: dict = None) -> List[Any]:
    """Instantiate multiple tools by name."""
    tool_configs = tool_configs or {}
    tools = []
    for name in names:
        cfg = tool_configs.get(name, {})
        tools.append(get_tool(name, **cfg))
    return tools


def list_tools() -> list:
    return list(TOOL_REGISTRY.keys())
