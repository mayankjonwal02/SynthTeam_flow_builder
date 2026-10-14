"""Vision providers — importing this package registers them."""

import logging

logger = logging.getLogger("uvicorn.error")

for _module in ("openai_vision", "gemini_vision", "ollama_vision"):
    try:
        __import__(f"app.ai.vision.{_module}")
    except ImportError as exc:  # optional provider SDK not installed
        logger.warning(f"Vision provider {_module} unavailable: {exc}")
