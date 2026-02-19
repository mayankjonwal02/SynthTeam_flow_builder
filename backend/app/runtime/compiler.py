"""
Graph Compiler — turns a ReactFlow graph (nodes + edges) into a
deterministic execution plan with proper data-flow relationships.

Output:
  {
    "method":         "POST",
    "path":           "/api/custom/...",
    "request_model":  <DynamicPydanticModel> | None,
    "response_model": <DynamicPydanticModel> | None,
    "query_model":    <DynamicPydanticModel> | None,
    "path_params":    { "user_id": "int", ... } | None,
    "ordered_nodes":  [ { id, component, config }, ... ],
    "edge_map":       { target_id: [ { parent, condition }, ... ], ... },
    "forward_adj":    { source_id: [ target_id, ... ], ... },
    "rate_limit":     { "requests": 100, "window_seconds": 60 } | None,
    "has_cron":       bool,
    "cron_expression": str | None,
  }
"""

import re
from collections import defaultdict, deque
from datetime import date, datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import HTTPException
from pydantic import create_model


class GraphCompiler:

    def __init__(self, graph: Dict[str, Any]):
        self.nodes = {n["id"]: n for n in graph.get("nodes", [])}
        self.edges = graph.get("edges", [])

    # ── adjacency / in-degree ───────────────────────────────────────
    def _build_adjacency(self):
        adj: Dict[str, List[str]] = defaultdict(list)
        indegree: Dict[str, int] = defaultdict(int)

        for edge in self.edges:
            if edge.get("targetHandle") == "loop_back":
                continue
            src = edge["source"]
            tgt = edge["target"]
            adj[src].append(tgt)
            indegree[tgt] += 1

        return adj, indegree

    # ── edge map (target -> [{ parent, condition, sourceHandle, targetHandle }])
    def _build_edge_map(self) -> Dict[str, List[dict]]:
        """Build a reverse adjacency with optional condition and handle metadata."""
        edge_map: Dict[str, List[dict]] = defaultdict(list)
        for edge in self.edges:
            edge_map[edge["target"]].append({
                "parent":       edge["source"],
                "condition":    edge.get("condition"),
                "sourceHandle": edge.get("sourceHandle"),
                "targetHandle": edge.get("targetHandle"),
            })
        return dict(edge_map)

    # ── forward adjacency (source -> [{ target, sourceHandle, targetHandle }])
    def _build_forward_adj(self) -> Dict[str, List[dict]]:
        """Build forward adjacency with handle metadata."""
        adj: Dict[str, List[dict]] = defaultdict(list)
        for edge in self.edges:
            adj[edge["source"]].append({
                "target":       edge["target"],
                "sourceHandle": edge.get("sourceHandle"),
                "targetHandle": edge.get("targetHandle"),
            })
        return dict(adj)

    # ── topological sort (Kahn's algorithm) ─────────────────────────
    def _topological_sort(self) -> List[str]:
        adj, indegree = self._build_adjacency()

        queue = deque(
            nid for nid in self.nodes if indegree[nid] == 0
        )
        ordered: List[str] = []

        while queue:
            nid = queue.popleft()
            ordered.append(nid)
            for neighbour in adj[nid]:
                indegree[neighbour] -= 1
                if indegree[neighbour] == 0:
                    queue.append(neighbour)

        if len(ordered) != len(self.nodes):
            raise HTTPException(
                status_code=422,
                detail="Graph contains a cycle — cannot compile",
            )

        return ordered

    # ── graph validation ────────────────────────────────────────────
    def validate_graph(self) -> None:
        """
        Validate graph structure before compilation.

        Checks:
          1. Exactly one entry node (is_entry == True)
          2. At least one response node (is_response == True)
          3. No cycles (via topological sort)
          4. All nodes reachable from entry
          5. Response nodes are terminal (no outgoing edges)
        """
        entry_nodes = []
        response_nodes = []

        for nid, node in self.nodes.items():
            cfg = node.get("data", {}).get("config", {})
            if cfg.get("is_entry"):
                entry_nodes.append(nid)
            if cfg.get("is_response"):
                response_nodes.append(nid)

        if len(entry_nodes) == 0:
            raise HTTPException(
                status_code=422,
                detail="Graph must have exactly one entry node (is_entry: true). Found 0.",
            )
        if len(entry_nodes) > 1:
            raise HTTPException(
                status_code=422,
                detail=f"Graph must have exactly one entry node. Found {len(entry_nodes)}: {entry_nodes}",
            )

        if len(response_nodes) == 0:
            raise HTTPException(
                status_code=422,
                detail="Graph must have at least one response node (is_response: true). Found 0.",
            )

        self._topological_sort()

        adj, _ = self._build_adjacency()
        entry_id = entry_nodes[0]
        visited: set = set()
        queue = deque([entry_id])
        while queue:
            nid = queue.popleft()
            if nid in visited:
                continue
            visited.add(nid)
            for neighbour in adj[nid]:
                if neighbour not in visited:
                    queue.append(neighbour)

        unreachable = set(self.nodes.keys()) - visited
        if unreachable:
            raise HTTPException(
                status_code=422,
                detail=f"Nodes not reachable from entry node: {sorted(unreachable)}",
            )

        for rid in response_nodes:
            if adj.get(rid):
                raise HTTPException(
                    status_code=422,
                    detail=f"Response node '{rid}' must be terminal but has outgoing edges to: {adj[rid]}",
                )

    # ── execution plan ──────────────────────────────────────────────
    def _build_execution_plan(self) -> list:
        ordered_ids = self._topological_sort()
        plan = []
        for nid in ordered_ids:
            node = self.nodes[nid]
            data = node.get("data", {})
            plan.append({
                "id":        nid,
                "component": data.get("component", "unknown"),
                "config":    data.get("config", {}),
            })
        return plan

    # ── dynamic Pydantic model from schema dict ─────────────────────
    @staticmethod
    def _create_schema_model(fields: Dict[str, Any], name: str):
        """
        Build a Pydantic model from a { field_name: type_string } dict.

        Supports nested objects (field value is a dict) and arrays
        (field value is {"__array_of__": { ... }}).
        """
        type_map = {
            "string":   str,
            "int":      int,
            "float":    float,
            "bool":     bool,
            "list":     list,
            "dict":     dict,
            "json":     dict,
            "base64":   str,
            "bytes":    str,
            "image":    str,
            "audio":    str,
            "video":    str,
            "file":     str,
            "date":     date,
            "datetime": datetime,
            "url":      str,
            "email":    str,
            "uuid":     UUID,
            "any":      Any,
        }
        model_fields = {}
        for fname, ftype in fields.items():
            if isinstance(ftype, dict):
                if "__array_of__" in ftype:
                    inner = GraphCompiler._create_schema_model(
                        ftype["__array_of__"], f"{name}_{fname}_Item"
                    )
                    model_fields[fname] = (List[inner], ...)  # type: ignore[valid-type]
                else:
                    nested = GraphCompiler._create_schema_model(ftype, f"{name}_{fname}")
                    model_fields[fname] = (nested, ...)
            else:
                py_type = type_map.get(ftype, str)
                model_fields[fname] = (py_type, ...)
        return create_model(name, **model_fields)

    # ── detect special nodes ────────────────────────────────────────
    def _find_special_nodes(self):
        entry: Optional[dict] = None
        response: Optional[dict] = None

        for node in self.nodes.values():
            cfg = node.get("data", {}).get("config", {})
            if cfg.get("is_entry"):
                entry = node
            if cfg.get("is_response"):
                response = node

        return entry, response

    # ── public compile ──────────────────────────────────────────────
    def compile(self) -> dict:
        """Validate the graph and produce an execution plan."""
        self.validate_graph()

        ordered_nodes = self._build_execution_plan()
        edge_map      = self._build_edge_map()
        forward_adj   = self._build_forward_adj()

        entry_node, response_node = self._find_special_nodes()

        if not entry_node:
            raise HTTPException(
                status_code=422,
                detail="No entry node defined (is_entry: true)",
            )

        entry_config = entry_node["data"]["config"]

        method = entry_config.get("method", "POST")
        path   = entry_config.get("path", "/deployed")

        # API versioning: prepend version prefix
        version = entry_config.get("version")
        if version:
            path = f"/{version}{path}" if not path.startswith(f"/{version}") else path

        # Request / response schemas
        req_fields  = entry_config.get("request_schema", {})
        resp_fields = entry_config.get("response_schema", {})
        if not resp_fields and response_node:
            resp_fields = response_node["data"]["config"].get("response_schema", {})

        RequestModel  = self._create_schema_model(req_fields,  "DynReq")  if req_fields  else None
        ResponseModel = self._create_schema_model(resp_fields, "DynResp") if resp_fields else None

        # Query parameter model
        query_fields = entry_config.get("query_params", {})
        QueryModel = self._create_schema_model(query_fields, "DynQuery") if query_fields else None

        # Path parameters
        path_params = entry_config.get("path_params")

        # Rate limiting config
        rate_limit = entry_config.get("rate_limit")

        # Cron trigger detection
        entry_component = entry_node["data"].get("component", "")
        has_cron = entry_component == "cron_trigger"
        cron_expression = entry_config.get("cron_expression") if has_cron else None

        return {
            "method":          method,
            "path":            path,
            "request_model":   RequestModel,
            "response_model":  ResponseModel,
            "query_model":     QueryModel,
            "path_params":     path_params,
            "ordered_nodes":   ordered_nodes,
            "edge_map":        edge_map,
            "forward_adj":     forward_adj,
            "rate_limit":      rate_limit,
            "has_cron":        has_cron,
            "cron_expression": cron_expression,
        }
