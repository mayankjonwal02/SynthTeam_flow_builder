"""Sandboxed Python code execution tool."""

import subprocess
import tempfile
import os
from app.ai.tools.registry import register_tool
from app.ai.tools.base import SynthTool


@register_tool("code_executor")
class CodeExecutorTool(SynthTool):
    name: str = "code_executor"
    description: str = "Execute Python code in a sandboxed environment. Input: Python code string. Returns stdout."

    def _run(self, code: str) -> str:
        try:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
                f.write(code)
                f.flush()
                result = subprocess.run(
                    ["python", f.name],
                    capture_output=True, text=True, timeout=30,
                    env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
                )
                os.unlink(f.name)
                if result.returncode != 0:
                    return f"Error:\n{result.stderr[:2000]}"
                return result.stdout[:2000]
        except subprocess.TimeoutExpired:
            return "Error: Code execution timed out (30s limit)"
        except Exception as e:
            return f"Execution failed: {e}"

    async def _arun(self, code: str) -> str:
        return self._run(code)
