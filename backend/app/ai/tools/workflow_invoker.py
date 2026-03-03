import json
from app.ai.tools.registry import register_tool
from app.ai.tools.base import SynthTool


@register_tool("workflow_invoker")
class WorkflowInvokerTool(SynthTool):
    name: str = "workflow_invoker"
    description: str = "Invoke another SynthTeam deployed workflow. Input: JSON with 'url' and optional 'body'."

    def _run(self, input_str: str) -> str:
        import requests
        try:
            params = json.loads(input_str)
            url = params.get("url", "")
            body = params.get("body", {})
            method = params.get("method", "POST").upper()
            resp = requests.request(method, url, json=body, timeout=60)
            return json.dumps({"status": resp.status_code, "data": resp.json()}, default=str)
        except Exception as e:
            return f"Workflow invocation failed: {e}"

    async def _arun(self, input_str: str) -> str:
        return self._run(input_str)
