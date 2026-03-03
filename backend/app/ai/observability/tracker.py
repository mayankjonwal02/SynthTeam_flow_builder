"""AI Observability — tracks tokens, latency, and tool calls per AI node execution."""

import time
import logging
from typing import Any, Dict, List, Optional
from contextlib import asynccontextmanager

logger = logging.getLogger("uvicorn.error")


class AITracker:
    """Context manager that collects AI execution metrics."""

    def __init__(self, node_id: str, component: str):
        self.node_id = node_id
        self.component = component
        self.start_time: float = 0
        self.metrics: Dict[str, Any] = {
            "node_id": node_id,
            "component": component,
            "model": "",
            "provider": "",
            "tokens_used": {"prompt": 0, "completion": 0, "total": 0},
            "latency_ms": 0,
            "tools_called": [],
            "error": None,
        }

    def set_model(self, provider: str, model: str):
        self.metrics["provider"] = provider
        self.metrics["model"] = model

    def set_tokens(self, prompt_tokens: int = 0, completion_tokens: int = 0):
        self.metrics["tokens_used"] = {
            "prompt": prompt_tokens,
            "completion": completion_tokens,
            "total": prompt_tokens + completion_tokens,
        }

    def add_tool_call(self, tool_name: str):
        self.metrics["tools_called"].append(tool_name)

    def set_error(self, error: str):
        self.metrics["error"] = error

    def start(self):
        self.start_time = time.perf_counter()

    def stop(self):
        self.metrics["latency_ms"] = round((time.perf_counter() - self.start_time) * 1000, 2)

    def to_dict(self) -> dict:
        return self.metrics


def extract_token_usage(response) -> Dict[str, int]:
    """Extract token usage from a LangChain response if available."""
    usage = {}
    if hasattr(response, "response_metadata"):
        meta = response.response_metadata
        token_usage = meta.get("token_usage", meta.get("usage", {}))
        if token_usage:
            usage["prompt"] = token_usage.get("prompt_tokens", token_usage.get("input_tokens", 0))
            usage["completion"] = token_usage.get("completion_tokens", token_usage.get("output_tokens", 0))
            usage["total"] = usage["prompt"] + usage["completion"]
    return usage
