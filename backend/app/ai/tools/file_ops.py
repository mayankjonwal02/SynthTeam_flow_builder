import json
from app.ai.tools.registry import register_tool
from app.ai.tools.base import SynthTool


@register_tool("file_read")
class FileReadTool(SynthTool):
    name: str = "file_read"
    description: str = "Read contents of a file. Input: file path string."

    def _run(self, path: str) -> str:
        try:
            with open(path.strip(), "r") as f:
                return f.read(10000)
        except Exception as e:
            return f"File read failed: {e}"

    async def _arun(self, path: str) -> str:
        return self._run(path)


@register_tool("file_write")
class FileWriteTool(SynthTool):
    name: str = "file_write"
    description: str = "Write content to a file. Input: JSON with 'path' and 'content'."

    def _run(self, input_str: str) -> str:
        try:
            params = json.loads(input_str)
            with open(params["path"], "w") as f:
                f.write(params["content"])
            return f"Written to {params['path']}"
        except Exception as e:
            return f"File write failed: {e}"

    async def _arun(self, input_str: str) -> str:
        return self._run(input_str)
