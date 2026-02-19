"""
Graph Executor — runs an execution plan produced by the compiler.

Data-flow logic:
  1. For each node (in topological order), look up its parent nodes
     from the edge_map.
  2. Gather each parent's output from context, applying conditional
     edge filtering (__condition__ / __case__) when edges carry a
     "condition" property.
  3. Skip nodes whose conditional parents were all filtered out.
  4. Pass { parent_id: parent_output, ... } as `inputs` to the component.
  5. Store the component's return value in context[node_id].
  6. The last node's output becomes the final result.

Special execution modes:
  - parallel_split: runs immediate children concurrently via asyncio.gather
  - loop_foreach:   4-handle node with in/loop_back/loop_out/done handles;
                    re-executes body nodes per array element
"""

import asyncio
import logging
import time
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Set

from app.components.component_registry import get_component

logger = logging.getLogger("uvicorn.error")


class GraphExecutor:

    def __init__(self, execution_plan: dict):
        self.ordered_nodes: list = execution_plan["ordered_nodes"]
        self.edge_map: Dict[str, List[dict]] = execution_plan.get("edge_map", {})
        self.forward_adj: Dict[str, List[dict]] = execution_plan.get("forward_adj", {})

        self._node_labels: Dict[str, str] = {}
        for n in self.ordered_nodes:
            label = n.get("config", {}).get("label") or n.get("component", n["id"])
            self._node_labels[n["id"]] = label

    # ── helpers ──────────────────────────────────────────────────────

    def _label(self, node_id: str) -> str:
        """Return a human-readable label for a node ID."""
        return self._node_labels.get(node_id, node_id)

    def _label_keys(self, d: Dict[str, Any]) -> Dict[str, Any]:
        """Replace node-ID keys with readable labels for trace display."""
        return {self._label(k): v for k, v in d.items()}

    def _get_forward_targets(self, node_id: str) -> List[str]:
        """Get plain target IDs from the forward adjacency."""
        return [
            e["target"] if isinstance(e, dict) else e
            for e in self.forward_adj.get(node_id, [])
        ]

    def _get_forward_entries_by_handle(
        self, node_id: str, source_handle: str
    ) -> List[str]:
        """Get target IDs for edges from a specific source handle."""
        targets = []
        for entry in self.forward_adj.get(node_id, []):
            if isinstance(entry, dict):
                if entry.get("sourceHandle") == source_handle:
                    targets.append(entry["target"])
            else:
                targets.append(entry)
        return targets

    def _has_conditional_parents(self, node_id: str) -> bool:
        """Return True if at least one incoming edge has a condition."""
        for entry in self.edge_map.get(node_id, []):
            if entry.get("condition") is not None:
                return True
        return False

    def _gather_inputs(
        self, node_id: str, context: Dict[str, Any],
        filter_target_handle: str | None = None,
    ) -> Dict[str, Any]:
        """
        Collect parent outputs for a node, respecting conditional edges.

        If filter_target_handle is set, only edges arriving at that
        specific targetHandle are considered.

        Supports two routing envelopes:
          - __condition__: True/False  (from IfConditionComponent)
          - __case__: "value"          (from SwitchCaseComponent)
        """
        parent_entries = self.edge_map.get(node_id, [])
        inputs: Dict[str, Any] = {}

        for entry in parent_entries:
            pid  = entry["parent"]
            cond = entry.get("condition")

            if filter_target_handle is not None:
                if entry.get("targetHandle") != filter_target_handle:
                    continue

            if pid not in context:
                continue

            parent_output = context[pid]

            if cond is not None and isinstance(parent_output, dict):
                case_val = parent_output.get("__case__")
                if case_val is not None:
                    if cond != str(case_val):
                        continue
                    inputs[pid] = parent_output.get("data", parent_output)
                    continue

                cond_flag = parent_output.get("__condition__")
                if cond_flag is not None:
                    expected = cond.lower() == "true"
                    if cond_flag != expected:
                        continue
                    inputs[pid] = parent_output.get("data", parent_output)
                    continue

                continue

            if isinstance(parent_output, dict):
                if "__condition__" in parent_output:
                    inputs[pid] = parent_output.get("data", parent_output)
                elif "__case__" in parent_output:
                    inputs[pid] = parent_output.get("data", parent_output)
                else:
                    inputs[pid] = parent_output
            else:
                inputs[pid] = parent_output

        return inputs

    async def _execute_node(
        self, component, request_data: dict, inputs: dict, config: dict
    ) -> Any:
        """Run a single component with optional timeout and retry."""
        timeout_sec = config.get("timeout")
        max_retries = config.get("retry", 0)
        last_exc: BaseException | None = None

        for attempt in range(max_retries + 1):
            try:
                coro = component.execute(request_data, inputs, config)
                if timeout_sec:
                    return await asyncio.wait_for(coro, timeout=timeout_sec)
                return await coro
            except asyncio.TimeoutError:
                last_exc = TimeoutError(
                    f"Node timed out after {timeout_sec}s (attempt {attempt + 1}/{max_retries + 1})"
                )
            except Exception as exc:
                last_exc = exc

            if attempt < max_retries:
                logger.warning(
                    f"Retry {attempt + 1}/{max_retries} for component"
                )

        raise last_exc  # type: ignore[misc]

    # ── single-node execution with tracing ───────────────────────────

    async def _run_single_node(
        self,
        node: dict,
        request_data: dict,
        context: Dict[str, Any],
        execution_trace: list,
        skipped: Set[str],
    ) -> Any:
        """Execute one node, record trace, return result (or None if skipped)."""
        node_id   = node["id"]
        comp_name = node["component"]
        config    = node.get("config", {})

        inputs = self._gather_inputs(node_id, context)

        if not inputs and self._has_conditional_parents(node_id):
            skipped.add(node_id)
            execution_trace.append({
                "node_id":     node_id,
                "node_name":   self._label(node_id),
                "component":   comp_name,
                "status":      "skipped",
                "timestamp":   datetime.now(timezone.utc).isoformat(),
                "duration_ms": 0,
                "input":       {},
                "output":      None,
            })
            return None

        trace_entry: dict = {
            "node_id":   node_id,
            "node_name": self._label(node_id),
            "component": comp_name,
            "input":     self._label_keys(inputs),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        t0 = time.perf_counter()
        try:
            component = get_component(comp_name)
            result = await self._execute_node(
                component, request_data, inputs, config
            )
            trace_entry["status"] = "success"
        except Exception as exc:
            logger.error(f"Node {node_id} ({comp_name}) failed: {exc}")
            result = {"error": str(exc)}
            trace_entry["status"] = "failed"
            trace_entry["error"]  = str(exc)

        elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
        trace_entry["output"]      = result
        trace_entry["duration_ms"] = elapsed_ms

        execution_trace.append(trace_entry)
        context[node_id] = result
        return result

    # ── loop helpers ─────────────────────────────────────────────────

    def _collect_loop_body(self, loop_node_id: str) -> List[str]:
        """
        Starting from a loop_foreach node's "loop_out" handle, collect
        all downstream node IDs that form the loop body. Walks forward
        until there are no more outgoing edges (or until we'd circle
        back to the loop node itself via "loop_back").
        """
        loop_out_targets = self._get_forward_entries_by_handle(loop_node_id, "loop_out")
        if not loop_out_targets:
            loop_out_targets = self._get_forward_targets(loop_node_id)

        body_ids: List[str] = []
        node_map = {n["id"]: n for n in self.ordered_nodes}
        visited: set = set()
        queue = list(loop_out_targets)

        while queue:
            nid = queue.pop(0)
            if nid in visited or nid == loop_node_id:
                continue
            visited.add(nid)
            node = node_map.get(nid)
            if not node:
                continue
            comp = node.get("component", "")
            if comp in ("response_builder",):
                continue
            body_ids.append(nid)
            queue.extend(self._get_forward_targets(nid))

        ordered_ids = [n["id"] for n in self.ordered_nodes]
        return [nid for nid in ordered_ids if nid in body_ids]

    async def _execute_loop_body(
        self,
        loop_node_id: str,
        element: Any,
        request_data: dict,
        parent_context: Dict[str, Any],
        execution_trace: list,
    ) -> Any:
        """Run the loop body nodes for a single iteration."""
        body_ids = self._collect_loop_body(loop_node_id)
        node_map = {n["id"]: n for n in self.ordered_nodes}

        iter_context = dict(parent_context)
        iter_context[loop_node_id] = (
            element if isinstance(element, dict) else {"__item__": element}
        )

        last_output = None
        skipped: Set[str] = set()

        for nid in body_ids:
            node = node_map[nid]
            result = await self._run_single_node(
                node, request_data, iter_context, execution_trace, skipped
            )
            if result is not None:
                last_output = result

        return last_output

    # ── main execution loop ──────────────────────────────────────────

    async def execute(self, request_data: dict) -> dict:
        """
        Execute all nodes and return the result with an execution trace.

        Returns:
            { "result": <last node output>, "trace": [...] }
        """
        context: Dict[str, Any] = {}
        execution_trace: list = []
        last_output: Any = None
        skipped: Set[str] = set()
        already_done: Set[str] = set()

        node_map = {n["id"]: n for n in self.ordered_nodes}

        for node in self.ordered_nodes:
            node_id   = node["id"]
            comp_name = node["component"]

            if node_id in already_done or node_id in skipped:
                continue

            result = await self._run_single_node(
                node, request_data, context, execution_trace, skipped
            )

            if node_id in skipped:
                continue

            last_output = result

            # ── parallel_split: run children concurrently ────────
            if comp_name == "parallel_split":
                child_ids = self._get_forward_targets(node_id)
                if child_ids:
                    child_nodes = [node_map[cid] for cid in child_ids if cid in node_map]

                    async def _run_child(child_node):
                        return await self._run_single_node(
                            child_node, request_data, context, execution_trace, skipped
                        )

                    results = await asyncio.gather(
                        *[_run_child(cn) for cn in child_nodes],
                        return_exceptions=True,
                    )
                    for cid, res in zip(child_ids, results):
                        if isinstance(res, Exception):
                            context[cid] = {"error": str(res)}
                        already_done.add(cid)
                        if res is not None and not isinstance(res, Exception):
                            last_output = res

            # ── loop_foreach: 4-handle iteration ─────────────────
            if comp_name == "loop_foreach" and result and isinstance(result, dict):
                array_field = node.get("config", {}).get("array_field", "items")
                data_payload = result.get("data", result)
                items = data_payload.get(array_field, [])

                body_ids = self._collect_loop_body(node_id)
                already_done.update(body_ids)

                # Find nodes connected to the "done" handle
                done_targets = self._get_forward_entries_by_handle(node_id, "done")

                loop_results = []
                for element in items:
                    iter_output = await self._execute_loop_body(
                        node_id, element, request_data,
                        context, execution_trace,
                    )
                    loop_results.append(iter_output)

                loop_output = {
                    "__loop_results__": loop_results,
                    "data": data_payload,
                }
                context[node_id] = loop_output
                last_output = loop_output

        return {"result": last_output, "trace": execution_trace}
