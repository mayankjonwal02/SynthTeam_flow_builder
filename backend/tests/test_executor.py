from fastapi import HTTPException

from app.components.base import BaseComponent
from app.components.component_registry import register_component
from app.runtime import registry
from app.runtime.executor import GraphExecutor

CALLS = []


@register_component("test_record")
class Record(BaseComponent):
    async def execute(self, request_data, inputs, config):
        CALLS.append({"label": config.get("label"), "owner": config.get("__owner_id__")})
        return {"from": config.get("label")}


@register_component("test_reject")
class Reject(BaseComponent):
    async def execute(self, request_data, inputs, config):
        raise HTTPException(status_code=401, detail="Missing required header: x-api-key")


@register_component("test_fail")
class Fail(BaseComponent):
    async def execute(self, request_data, inputs, config):
        raise RuntimeError("boom")


@register_component("test_false_branch")
class FalseBranch(BaseComponent):
    async def execute(self, request_data, inputs, config):
        return {"__condition__": False, "data": {"x": 1}}


def make_plan(nodes, edges, owner_id="user_1"):
    edge_map, forward = {}, {}
    for parent, target, cond in edges:
        edge_map.setdefault(target, []).append({"parent": parent, "condition": cond})
        forward.setdefault(parent, []).append(target)
    return {
        "ordered_nodes": [{"id": n, "component": c, "config": {"label": n}} for n, c in nodes],
        "edge_map": edge_map,
        "forward_adj": forward,
        "owner_id": owner_id,
    }


def setup_function():
    CALLS.clear()


async def test_auth_gate_rejection_stops_the_workflow():
    plan = make_plan(
        [("entry", "test_record"), ("gate", "test_reject"), ("db_insert", "test_record")],
        [("entry", "gate", None), ("gate", "db_insert", None)],
    )
    execution = await GraphExecutor(plan).execute({})
    assert execution["halted"] == {"status_code": 401, "detail": "Missing required header: x-api-key"}
    assert [c["label"] for c in CALLS] == ["entry"]  # db_insert never ran

    response = await registry._handle_result(execution, None, debug=False)
    assert response.status_code == 401


async def test_children_of_skipped_branch_are_skipped():
    plan = make_plan(
        [("if", "test_false_branch"), ("b", "test_record"), ("c", "test_record")],
        [("if", "b", True), ("b", "c", None)],  # boolean condition must not crash
    )
    execution = await GraphExecutor(plan).execute({})
    assert CALLS == []
    statuses = {t["node_id"]: t["status"] for t in execution["trace"]}
    assert statuses == {"if": "success", "b": "skipped", "c": "skipped"}


async def test_failure_skips_descendants_and_returns_500():
    plan = make_plan([("a", "test_fail"), ("b", "test_record")], [("a", "b", None)])
    execution = await GraphExecutor(plan).execute({})
    assert CALLS == []
    response = await registry._handle_result(execution, None, debug=False)
    assert response.status_code == 500
    assert b"boom" in response.body


async def test_owner_id_is_passed_to_nodes():
    await GraphExecutor(make_plan([("a", "test_record")], [], owner_id="user_42")).execute({})
    assert CALLS[0]["owner"] == "user_42"


async def test_sensitive_headers_redacted_from_results():
    execution = {
        "result": {"__headers__": {"Authorization": "Bearer abc", "Cookie": "s=1", "host": "x"}},
        "trace": [],
    }
    result = await registry._handle_result(execution, None, debug=False)
    assert result["__headers__"] == {"Authorization": "[redacted]", "Cookie": "[redacted]", "host": "x"}
