import json
from app.ai.tools.registry import register_tool
from app.ai.tools.base import SynthTool


@register_tool("slack_notifier")
class SlackNotifierTool(SynthTool):
    name: str = "slack_notifier"
    description: str = "Send a Slack message via webhook. Input: JSON with 'webhook_url' and 'message'."

    def _run(self, input_str: str) -> str:
        import requests
        try:
            params = json.loads(input_str)
            resp = requests.post(
                params["webhook_url"],
                json={"text": params["message"]},
                timeout=10,
            )
            return f"Slack notification sent (status {resp.status_code})"
        except Exception as e:
            return f"Slack notification failed: {e}"

    async def _arun(self, input_str: str) -> str:
        return self._run(input_str)
