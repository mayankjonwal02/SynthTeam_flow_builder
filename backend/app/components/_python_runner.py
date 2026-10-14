"""
Standalone runner for the Python Function node.

Executed as a separate, isolated process (python -I) so user code can be
killed on timeout and never sees the server's memory or environment.

stdin:  {"code": "<full handler source>", "data": {...}}
stdout: {"ok": true, "result": ...} or {"ok": false, "error": "..."}
"""

import json
import sys

SAFE_BUILTINS = {
    "abs": abs, "all": all, "any": any, "bool": bool, "dict": dict,
    "enumerate": enumerate, "filter": filter, "float": float,
    "int": int, "isinstance": isinstance, "len": len, "list": list,
    "map": map, "max": max, "min": min, "print": print, "range": range,
    "round": round, "set": set, "sorted": sorted, "str": str,
    "sum": sum, "tuple": tuple, "zip": zip,
    "True": True, "False": False, "None": None,
    "Exception": Exception, "ValueError": ValueError, "KeyError": KeyError,
    "TypeError": TypeError,
}


def main() -> None:
    payload = json.loads(sys.stdin.read())
    # User print() output must not corrupt the JSON reply on stdout
    real_stdout, sys.stdout = sys.stdout, sys.stderr
    try:
        namespace: dict = {"__builtins__": SAFE_BUILTINS}
        exec(payload["code"], namespace)
        result = namespace["handler"](payload.get("data", {}))
        reply = {"ok": True, "result": result}
    except Exception as exc:  # report user errors back to the node
        reply = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    real_stdout.write(json.dumps(reply, default=str))


if __name__ == "__main__":
    main()
