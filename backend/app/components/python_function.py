"""
Python Function Component — executes user-defined Python code at runtime.

The user writes only the BODY of the handler function. The backend
automatically wraps it inside `def handler(data):` before execution.

Config:
    {
        "code": "return {'greeting': 'Hello ' + data.get('name', 'world')}"
    }

Security: runs in a restricted namespace with no filesystem, network,
or import access beyond safe builtins. The code is checked before it runs:
imports, private/dunder attributes (e.g. ``().__class__``) and frame/code
object attributes are rejected, which closes the usual escapes from
restricted ``exec``. The handler then runs in a separate isolated Python
process (no server memory or environment variables) that is killed when
the timeout expires. This is a guard rail, not a hard
sandbox -- only let trusted users author workflows.
"""

import ast
import asyncio
import json
import os
import sys
import tempfile
import textwrap
from pathlib import Path
from typing import Any, Dict

from app.components.base import BaseComponent
from app.components.component_registry import register_component

DEFAULT_TIMEOUT_SECONDS = 10

# Attributes that expose interpreter internals (frames, code objects, globals)
_BLOCKED_ATTRS = frozenset({
    "gi_frame", "gi_code", "gi_yieldfrom", "cr_frame", "cr_code", "cr_await",
    "ag_frame", "ag_code", "f_globals", "f_locals", "f_builtins", "f_back",
    "f_code", "tb_frame", "tb_next", "co_code", "func_globals", "mro",
})


def validate_code(code: str) -> None:
    """Raise ValueError if the code uses constructs that can escape the namespace."""
    tree = ast.parse(code)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom, ast.Global, ast.Nonlocal)):
            raise ValueError("imports and global/nonlocal statements are not allowed")
        if isinstance(node, ast.Attribute) and (
            node.attr.startswith("_") or node.attr in _BLOCKED_ATTRS
        ):
            raise ValueError(f"access to attribute '{node.attr}' is not allowed")
        if isinstance(node, ast.Name) and node.id.startswith("__"):
            raise ValueError(f"use of name '{node.id}' is not allowed")


_RUNNER = Path(__file__).with_name("_python_runner.py")


async def _run_isolated(code: str, data: dict, timeout: float) -> dict:
    """Run the handler in a separate isolated Python process; kill it on timeout."""
    with tempfile.TemporaryDirectory() as workdir:
        proc = await asyncio.create_subprocess_exec(
            sys.executable, "-I", str(_RUNNER),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=workdir,
            # No inherited secrets (DATABASE_URL, API keys, ...)
            env={"PATH": os.environ.get("PATH", ""), "PYTHONDONTWRITEBYTECODE": "1"},
        )
        payload = json.dumps({"code": code, "data": data}, default=str).encode()
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(payload), timeout)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            raise
    try:
        return json.loads(stdout.decode() or "{}")
    except json.JSONDecodeError:
        return {"ok": False, "error": stderr.decode(errors="replace")[-500:] or "no output"}


def _wrap_handler(body: str) -> str:
    """Wrap user-provided body code inside a def handler(data): block."""
    dedented = textwrap.dedent(body)
    indented = textwrap.indent(dedented, "    ")
    return f"def handler(data):\n{indented}"


@register_component("python_function")
class PythonFunctionComponent(BaseComponent):
    """Executes a user-defined Python handler function on upstream data."""

    async def execute(
        self,
        request_data: dict,
        inputs: Dict[str, Any],
        config: dict,
    ) -> dict:
        merged: dict = {}
        for output in inputs.values():
            if isinstance(output, dict):
                merged.update(output)

        raw_code = config.get("code", "")
        if not raw_code.strip():
            return merged

        full_code = _wrap_handler(raw_code)
        try:
            validate_code(full_code)
        except SyntaxError as exc:
            return {"error": f"Compilation error: {exc}", "data": merged}
        except ValueError as exc:
            return {"error": f"Code rejected: {exc}", "data": merged}

        try:
            timeout = float(config.get("timeout") or DEFAULT_TIMEOUT_SECONDS)
        except (TypeError, ValueError):
            timeout = DEFAULT_TIMEOUT_SECONDS

        try:
            reply = await _run_isolated(full_code, merged, timeout)
        except asyncio.TimeoutError:
            return {"error": f"Runtime error: timed out after {timeout:g}s", "data": merged}
        if not reply.get("ok"):
            return {"error": f"Runtime error: {reply.get('error')}", "data": merged}
        result = reply.get("result")

        if isinstance(result, dict):
            return result
        return {"result": result}
