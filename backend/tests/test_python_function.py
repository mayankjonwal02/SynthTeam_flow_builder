import time

import pytest

from app.components.python_function import PythonFunctionComponent, _run_isolated, validate_code


async def run(code, data=None, **config):
    return await PythonFunctionComponent().execute({}, {"p": data or {"name": "bob"}}, {"code": code, **config})


async def test_runs_handler_and_returns_dict():
    assert await run("return {'greeting': 'Hi ' + data['name']}") == {"greeting": "Hi bob"}


async def test_non_dict_result_is_wrapped():
    assert await run("return [x * 2 for x in range(3)]") == {"result": [0, 2, 4]}


@pytest.mark.parametrize("code", [
    "return ().__class__.__base__.__subclasses__()",
    "import os\nreturn {}",
    "g = (i for i in [1])\nreturn {'f': g.gi_frame}",
    "return __builtins__",
])
def test_escape_attempts_are_rejected(code):
    with pytest.raises(ValueError):
        validate_code(f"def handler(data):\n    " + code.replace("\n", "\n    "))


async def test_rejected_code_reports_error():
    result = await run("return ().__class__")
    assert "Code rejected" in result["error"]


async def test_runtime_errors_are_reported():
    result = await run("return 1/0")
    assert "ZeroDivisionError" in result["error"]


async def test_isolated_process_has_no_server_secrets(monkeypatch, tmp_path):
    # Even if user code escaped the restricted namespace, the subprocess's
    # environment holds no secrets. Swap in a runner that just dumps its env.
    import app.components.python_function as pf

    dump = tmp_path / "dump_env.py"
    dump.write_text("import json, os, sys\nsys.stdin.read()\nprint(json.dumps({'ok': True, 'result': dict(os.environ)}))")
    monkeypatch.setattr(pf, "_RUNNER", dump)
    monkeypatch.setenv("SUPER_SECRET", "x")

    reply = await _run_isolated("", {}, timeout=10)
    assert reply["ok"]
    assert "SUPER_SECRET" not in reply["result"]
    assert "DATABASE_URL" not in reply["result"]


async def test_infinite_loop_is_killed():
    start = time.monotonic()
    result = await run("while True:\n    pass", timeout=1)
    assert "timed out" in result["error"]
    assert time.monotonic() - start < 5
