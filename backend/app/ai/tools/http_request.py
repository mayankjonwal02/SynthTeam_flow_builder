import json
from app.ai.tools.registry import register_tool
from app.ai.tools.base import SynthTool


@register_tool("http_request")
class HttpRequestTool(SynthTool):
    name: str = "http_request"
    description: str = "Make an HTTP request. Input: JSON with 'url', 'method' (GET/POST), optional 'headers' and 'body'."

    def _run(self, input_str: str) -> str:
        import requests
        try:
            params = json.loads(input_str) if isinstance(input_str, str) else input_str
            method = params.get("method", "GET").upper()
            url = params.get("url", "")
            headers = params.get("headers", {})
            body = params.get("body")
            resp = requests.request(method, url, headers=headers, json=body, timeout=30)
            return json.dumps({"status": resp.status_code, "body": resp.text[:2000]})
        except Exception as e:
            return f"HTTP request failed: {e}"

    async def _arun(self, input_str: str) -> str:
        return self._run(input_str)
