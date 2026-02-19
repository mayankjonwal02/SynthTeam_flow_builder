"""
Python Function Component — executes user-defined Python code at runtime.

The user writes only the BODY of the handler function. The backend
automatically wraps it inside `def handler(data):` before execution.

Config:
    {
        "code": "return {'greeting': 'Hello ' + data.get('name', 'world')}"
    }

Security: runs in a restricted namespace with no filesystem, network,
or import access beyond safe builtins.
"""

import textwrap
from typing import Any, Dict

from app.components.base import BaseComponent
from app.components.component_registry import register_component

_SAFE_BUILTINS = {
    "abs": abs, "all": all, "any": any, "bool": bool, "dict": dict,
    "enumerate": enumerate, "filter": filter, "float": float,
    "int": int, "isinstance": isinstance, "len": len, "list": list,
    "map": map, "max": max, "min": min, "print": print, "range": range,
    "round": round, "set": set, "sorted": sorted, "str": str,
    "sum": sum, "tuple": tuple, "type": type, "zip": zip,
    "True": True, "False": False, "None": None,
}


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

        restricted_globals: dict = {"__builtins__": _SAFE_BUILTINS}
        restricted_locals: dict = {}

        try:
            exec(full_code, restricted_globals, restricted_locals)
        except Exception as exc:
            return {"error": f"Compilation error: {exc}", "data": merged}

        handler = restricted_locals.get("handler")
        if handler is None or not callable(handler):
            return {"error": "Failed to create handler function", "data": merged}

        try:
            result = handler(merged)
        except Exception as exc:
            return {"error": f"Runtime error: {exc}", "data": merged}

        if isinstance(result, dict):
            return result
        return {"result": result}
