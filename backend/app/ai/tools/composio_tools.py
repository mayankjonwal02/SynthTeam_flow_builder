"""Composio integration — dynamically loads tools from the Composio platform."""

import logging
from app.ai.tools.registry import register_tool
from app.ai.tools.base import SynthTool

logger = logging.getLogger("uvicorn.error")


@register_tool("composio")
class ComposioTool(SynthTool):
    name: str = "composio"
    description: str = "Execute a Composio action. Input: JSON with 'action' name and 'params'."
    api_key: str = ""

    def _run(self, input_str: str) -> str:
        import json
        try:
            from composio_langchain import ComposioToolSet
            params = json.loads(input_str) if isinstance(input_str, str) else input_str
            toolset = ComposioToolSet(api_key=self.api_key)
            action = params.get("action", "")
            action_params = params.get("params", {})
            result = toolset.execute_action(action=action, params=action_params)
            return json.dumps(result, default=str)
        except Exception as e:
            return f"Composio action failed: {e}"

    async def _arun(self, input_str: str) -> str:
        return self._run(input_str)
