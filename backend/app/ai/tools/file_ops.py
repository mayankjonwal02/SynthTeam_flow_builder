import asyncio
import json
from pathlib import Path

from app.ai.tools.registry import register_tool
from app.ai.tools.base import SynthTool


def resolve_in_base(base_path: str, path: str) -> Path:
    """Resolve `path` inside `base_path`; raise ValueError if it escapes it."""
    base = Path(base_path or "/tmp").resolve()
    target = Path(path.strip())
    if not target.is_absolute():
        target = base / target
    target = target.resolve()
    if target != base and base not in target.parents:
        raise ValueError(f"Path must be inside {base}")
    return target


@register_tool("file_read")
class FileReadTool(SynthTool):
    name: str = "file_read"
    description: str = "Read contents of a file. Input: file path string (relative to the tool's base directory)."
    base_path: str = "/tmp"

    def _run(self, path: str) -> str:
        try:
            with open(resolve_in_base(self.base_path, path), "r") as f:
                return f.read(10000)
        except Exception as e:
            return f"File read failed: {e}"

    async def _arun(self, path: str) -> str:
        return await asyncio.to_thread(self._run, path)


@register_tool("file_write")
class FileWriteTool(SynthTool):
    name: str = "file_write"
    description: str = "Write content to a file. Input: JSON with 'path' (relative to the tool's base directory) and 'content'."
    base_path: str = "/tmp"

    def _run(self, input_str: str) -> str:
        try:
            params = json.loads(input_str)
            target = resolve_in_base(self.base_path, params["path"])
            target.parent.mkdir(parents=True, exist_ok=True)
            with open(target, "w") as f:
                f.write(params["content"])
            return f"Written to {target}"
        except Exception as e:
            return f"File write failed: {e}"

    async def _arun(self, input_str: str) -> str:
        return await asyncio.to_thread(self._run, input_str)
