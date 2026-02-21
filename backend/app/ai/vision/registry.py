"""Vision provider registry."""

import logging
from typing import Any, Callable, Dict

logger = logging.getLogger("uvicorn.error")

VISION_REGISTRY: Dict[str, Callable] = {}


def register_vision_provider(name: str):
    def decorator(fn: Callable):
        VISION_REGISTRY[name] = fn
        logger.info(f"Registered vision provider: {name}")
        return fn
    return decorator


async def analyze_image(provider: str, image_input: str, prompt: str, api_key: str = "", **kwargs) -> dict:
    fn = VISION_REGISTRY.get(provider)
    if fn is None:
        raise ValueError(f"Vision provider '{provider}' not registered. Available: {list(VISION_REGISTRY.keys())}")
    return await fn(image_input=image_input, prompt=prompt, api_key=api_key, **kwargs)
