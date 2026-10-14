"""Python code execution tool for agents (separate, isolated process)."""

import asyncio
import os
import subprocess
import sys
import tempfile

from app.ai.tools.registry import register_tool
from app.ai.tools.base import SynthTool

MAX_TIMEOUT_SECONDS = 60


@register_tool("code_executor")
class CodeExecutorTool(SynthTool):
    name: str = "code_executor"
    description: str = "Execute Python code in a sandboxed environment. Input: Python code string. Returns stdout."
    timeout: int = 10

    def _run(self, code: str) -> str:
        timeout = max(1, min(int(self.timeout or 10), MAX_TIMEOUT_SECONDS))
        try:
            with tempfile.TemporaryDirectory() as workdir:
                script = os.path.join(workdir, "main.py")
                with open(script, "w") as f:
                    f.write(code)
                result = subprocess.run(
                    # -I: isolated mode (ignores PYTHON* env vars and user site-packages)
                    [sys.executable, "-I", script],
                    capture_output=True, text=True, timeout=timeout,
                    cwd=workdir,
                    # Don't hand the server's secrets (DATABASE_URL, API keys, ...) to LLM-written code
                    env={"PATH": os.environ.get("PATH", ""), "PYTHONDONTWRITEBYTECODE": "1"},
                )
            if result.returncode != 0:
                return f"Error:\n{result.stderr[:2000]}"
            return result.stdout[:2000]
        except subprocess.TimeoutExpired:
            return f"Error: Code execution timed out ({timeout}s limit)"
        except Exception as e:
            return f"Execution failed: {e}"

    async def _arun(self, code: str) -> str:
        return await asyncio.to_thread(self._run, code)
