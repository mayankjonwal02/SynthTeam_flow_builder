"""Multi-agent orchestrator — coordinates Requirement → Planner → Builder → Reviewer.

Uses a simple async loop (not LangGraph StateGraph) to keep things straightforward
and compatible with the WebSocket streaming pattern. Each agent is a
``create_react_agent`` instance invoked with ``ainvoke``.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Callable, Optional

from app.multi_agent.agents import (
    create_requirement_agent,
    create_planner_agent,
    create_builder_agent,
    create_reviewer_agent,
    create_feedback_agent,
)
from app.multi_agent.session import SessionManager
from app.multi_agent.tools import validate_plan_edges, validate_plan_required_connections, scan_missing_secrets, fill_config_defaults, HANDLE_COMPATIBILITY, COMPONENT_CATALOG

logger = logging.getLogger("uvicorn.error")

MAX_REVIEW_ITERATIONS = 3


def _extract_json(text: str) -> Optional[dict]:
    """Best-effort JSON extraction from agent output.

    Handles: markdown fences, <think> blocks, surrounding prose.
    """
    if not text:
        return None

    text = text.strip()

    # Strip <think>...</think> blocks (Qwen / DeepSeek reasoning)
    import re
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()

    # Strip markdown code fences
    text = re.sub(r"```(?:json)?\s*\n?", "", text).strip()

    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Find the outermost { ... } block
    depth = 0
    start = -1
    for i, ch in enumerate(text):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start != -1:
                try:
                    return json.loads(text[start : i + 1])
                except json.JSONDecodeError:
                    start = -1

    return None


async def _run_agent(agent, messages: list[dict], recursion_limit: int = 80) -> str:
    """Invoke a create_react_agent and return its final text output."""
    try:
        result = await agent.ainvoke(
            {"messages": messages},
            config={"recursion_limit": recursion_limit},
        )
    except Exception as exc:
        logger.error(f"Agent invocation failed: {exc}")
        return ""

    msgs = result.get("messages", [])
    for msg in reversed(msgs):
        content = getattr(msg, "content", "")
        if isinstance(content, list):
            parts = [p.get("text", "") if isinstance(p, dict) else str(p) for p in content]
            content = "\n".join(parts)
        if content and getattr(msg, "type", "") in ("ai", "assistant"):
            return content
    return ""


class MultiAgentOrchestrator:
    """Runs the 4-agent pipeline for a single session."""

    def __init__(
        self,
        llm,
        session_mgr: SessionManager,
        session_id: str,
        ws_emitter: Optional[Callable] = None,
    ):
        self.llm = llm
        self.session_mgr = session_mgr
        self.session_id = session_id
        self._emit = ws_emitter or (lambda t, d: None)
        self.graph_state: dict = {"nodes": [], "edges": []}
        self._diagnostics: list[dict] = []

    def _diag(self, agent: str, event: str, detail: str = ""):
        """Append a diagnostic entry for the feedback agent."""
        import time
        self._diagnostics.append({
            "agent": agent,
            "event": event,
            "detail": detail[:500],
            "ts": time.time(),
        })

    def _ws(self, event_type: str, data: dict):
        self._emit(event_type, data)

    def _ws_agent(self, agent_name: str, event_type: str, data: dict):
        self._emit(event_type, {"agent": agent_name, **data})

    def _context_limit(self) -> int:
        try:
            from app.core.config import settings
            return int(getattr(settings, "AGENT_BUILDER_CONTEXT_MESSAGES", 60) or 60)
        except Exception:
            return 60

    async def _build_prompt_context(self) -> str:
        """Compact session context (last N messages) for agent prompts."""
        try:
            convo = await self.session_mgr.get_conversation(self.session_id, limit=self._context_limit())
        except Exception:
            session = await self.session_mgr.get(self.session_id)
            convo = (session.get("conversation", []) if session else [])[-self._context_limit():]

        lines: list[str] = []
        for m in convo:
            role = m.get("role", "?")
            agent = m.get("agent", "")
            tag = f"[{agent}]" if agent else ""
            content = (m.get("content", "") or "").strip().replace("\n", " ")
            if len(content) > 400:
                content = content[:400] + "…"
            lines.append(f"{role}{tag}: {content}")
        return "\n".join(lines)

    @staticmethod
    def _validate_graph_state(graph_state: dict) -> list[str]:
        """Deterministic validation of a built graph_state (no LLM tools)."""
        issues: list[str] = []
        nodes = graph_state.get("nodes", [])
        edges = graph_state.get("edges", [])
        node_ids = {n.get("id") for n in nodes if n.get("id")}
        node_types = {n.get("id"): n.get("type") for n in nodes if n.get("id")}

        has_trigger = any(
            node_types.get(nid) in ("http_entry", "webhook_trigger", "cron_trigger", "manual_trigger")
            for nid in node_ids
        )
        if not has_trigger:
            issues.append("No trigger node found.")

        has_response = any(node_types.get(nid) == "response_builder" for nid in node_ids)
        if not has_response and has_trigger:
            issues.append("No response_builder node found.")

        connected = set()
        for e in edges:
            if e.get("source"):
                connected.add(e["source"])
            if e.get("target"):
                connected.add(e["target"])
        orphans = node_ids - connected
        trigger_types = {"http_entry", "webhook_trigger", "cron_trigger", "manual_trigger"}
        for oid in orphans:
            if node_types.get(oid) not in trigger_types and node_types.get(oid) != "response_builder":
                issues.append(f"Node '{oid}' ({node_types.get(oid)}) is not connected.")

        for e in edges:
            src = e.get("source")
            tgt = e.get("target")
            if src not in node_ids:
                issues.append(f"Edge references missing source node '{src}'.")
                continue
            if tgt not in node_ids:
                issues.append(f"Edge references missing target node '{tgt}'.")
                continue

            src_type = node_types.get(src)
            tgt_type = node_types.get(tgt)
            if src_type not in COMPONENT_CATALOG:
                issues.append(f"Edge source node '{src}' has unknown type '{src_type}'.")
                continue
            if tgt_type not in COMPONENT_CATALOG:
                issues.append(f"Edge target node '{tgt}' has unknown type '{tgt_type}'.")
                continue

            src_handle = e.get("sourceHandle", "output")
            tgt_handle = e.get("targetHandle", "input")
            src_info = COMPONENT_CATALOG.get(src_type) or {}
            tgt_info = COMPONENT_CATALOG.get(tgt_type) or {}
            if src_handle not in src_info.get("source_handles", []):
                issues.append(
                    f"Edge {src}->{tgt}: '{src_type}' has no source handle '{src_handle}'."
                )
            if tgt_handle not in tgt_info.get("target_handles", []):
                issues.append(
                    f"Edge {src}->{tgt}: '{tgt_type}' has no target handle '{tgt_handle}'."
                )

            compatible = HANDLE_COMPATIBILITY.get(src_handle, [])
            if tgt_handle not in compatible:
                issues.append(
                    f"Edge {src}->{tgt}: handle mismatch '{src_handle}' -> '{tgt_handle}' (compatible: {compatible})"
                )

        return issues

    @staticmethod
    def _graph_matches_plan(plan: dict, graph_state: dict) -> tuple[bool, str]:
        """Best-effort check that built graph matches the plan semantically."""
        from collections import Counter

        plan_nodes = plan.get("nodes", []) or []
        plan_edges = plan.get("edges", []) or []
        built_nodes = graph_state.get("nodes", []) or []
        built_edges = graph_state.get("edges", []) or []

        if len(built_nodes) != len(plan_nodes):
            return False, f"node_count_mismatch plan={len(plan_nodes)} built={len(built_nodes)}"
        if len(built_edges) != len(plan_edges):
            return False, f"edge_count_mismatch plan={len(plan_edges)} built={len(built_edges)}"

        plan_type_counts = Counter([n.get("type") for n in plan_nodes])
        built_type_counts = Counter([n.get("type") for n in built_nodes])
        if plan_type_counts != built_type_counts:
            return False, f"node_type_mismatch plan={dict(plan_type_counts)} built={dict(built_type_counts)}"

        plan_node_types = {n.get("id"): n.get("type") for n in plan_nodes}
        built_node_types = {n.get("id"): n.get("type") for n in built_nodes}

        def _edge_sig(edges: list[dict], node_types: dict) -> Counter:
            sigs = []
            for e in edges:
                src = e.get("source")
                tgt = e.get("target")
                sigs.append((
                    node_types.get(src, "?"),
                    node_types.get(tgt, "?"),
                    e.get("sourceHandle", "output"),
                    e.get("targetHandle", "input"),
                ))
            return Counter(sigs)

        plan_sigs = _edge_sig(plan_edges, plan_node_types)
        built_sigs = _edge_sig(built_edges, built_node_types)
        if plan_sigs != built_sigs:
            return False, "edge_signature_mismatch"

        issues = MultiAgentOrchestrator._validate_graph_state(graph_state)
        if issues:
            return False, f"graph_invalid: {issues[0]}"

        return True, "ok"

    def _execute_plan_directly(self, plan: dict):
        """Deterministic fallback: build graph from the Planner's plan without LLM.

        Called when the Builder agent's tool calls fail (e.g. model doesn't
        support function calling). Directly constructs nodes and edges in
        graph_state and emits WS events for each.
        """
        import uuid as _uuid

        id_map: dict[str, str] = {}
        trigger_types = {"http_entry", "webhook_trigger", "cron_trigger", "manual_trigger"}

        for node_spec in plan.get("nodes", []):
            plan_id = node_spec.get("id", "")
            node_type = node_spec.get("type", "")
            label = node_spec.get("label", node_type)
            pos = node_spec.get("position", {})
            cfg = node_spec.get("config", {})

            if node_type not in COMPONENT_CATALOG:
                logger.warning(f"Direct builder: skipping unknown type '{node_type}'")
                continue

            fill_config_defaults(node_type, cfg)

            actual_id = str(_uuid.uuid4())[:8]
            id_map[plan_id] = actual_id

            cfg["label"] = label
            if node_type in trigger_types:
                cfg["is_entry"] = True
            if node_type == "response_builder":
                cfg["is_response"] = True

            node = {
                "id": actual_id,
                "type": node_type,
                "position": {"x": pos.get("x", 100), "y": pos.get("y", 200)},
                "data": {"label": label, "component": node_type, "config": cfg},
            }
            self.graph_state["nodes"].append(node)
            self._ws("node_added", node)

        for edge_spec in plan.get("edges", []):
            src_plan = edge_spec.get("source", "")
            tgt_plan = edge_spec.get("target", "")
            src_actual = id_map.get(src_plan, src_plan)
            tgt_actual = id_map.get(tgt_plan, tgt_plan)

            node_ids = {n["id"] for n in self.graph_state["nodes"]}
            if src_actual not in node_ids or tgt_actual not in node_ids:
                logger.warning(f"Direct builder: skipping edge {src_plan}->{tgt_plan} (missing node)")
                continue

            edge = {
                "id": f"e-{src_actual}-{tgt_actual}",
                "source": src_actual,
                "target": tgt_actual,
                "sourceHandle": edge_spec.get("sourceHandle", "output"),
                "targetHandle": edge_spec.get("targetHandle", "input"),
            }
            self.graph_state["edges"].append(edge)
            self._ws("edge_added", edge)

        logger.info(
            f"Direct builder: created {len(self.graph_state['nodes'])} nodes, "
            f"{len(self.graph_state['edges'])} edges"
        )

    @staticmethod
    def _auto_fix_plan_edges(plan: dict):
        """Best-effort fix of invalid plan edges by correcting handle names.

        Mutates the plan dict in place. For each invalid edge, tries to find
        the correct source/target handle pair using the compatibility map.
        """
        node_map = {n["id"]: n["type"] for n in plan.get("nodes", [])}

        for edge in plan.get("edges", []):
            src_type = node_map.get(edge.get("source", ""))
            tgt_type = node_map.get(edge.get("target", ""))
            if not src_type or not tgt_type:
                continue

            src_info = COMPONENT_CATALOG.get(src_type)
            tgt_info = COMPONENT_CATALOG.get(tgt_type)
            if not src_info or not tgt_info:
                continue

            src_handle = edge.get("sourceHandle", "output")
            tgt_handle = edge.get("targetHandle", "input")

            # Check if current handles are already valid
            compatible = HANDLE_COMPATIBILITY.get(src_handle, [])
            if (
                src_handle in src_info["source_handles"]
                and tgt_handle in tgt_info["target_handles"]
                and tgt_handle in compatible
            ):
                continue

            # Try to find a valid handle pair
            for sh in src_info["source_handles"]:
                for th in tgt_info["target_handles"]:
                    if th in HANDLE_COMPATIBILITY.get(sh, []):
                        edge["sourceHandle"] = sh
                        edge["targetHandle"] = th
                        break
                else:
                    continue
                break

    async def _run_feedback_agent(
        self,
        spec: dict,
        plan: dict,
        review: dict,
        iterations: int,
        used_fallback_builder: bool = False,
    ):
        """STEP 5: Feedback Agent — generates a product improvement report and saves it to reports/."""
        import os
        from datetime import datetime

        self._ws("status_change", {"status": "feedback", "agent": "feedback"})
        self._ws("agent_thinking", {"agent": "feedback"})

        session = await self.session_mgr.get(self.session_id)
        conversation = session.get("conversation", []) if session else []

        conversation_summary = ""
        for m in conversation[-20:]:
            role = m.get("role", "?")
            agent = m.get("agent", "")
            tag = f"[{agent}] " if agent else ""
            conversation_summary += f"{role}: {tag}{m.get('content', '')[:200]}\n"

        plan_node_count = len(plan.get("nodes", []))
        plan_edge_count = len(plan.get("edges", []))
        built_node_count = len(self.graph_state["nodes"])
        built_edge_count = len(self.graph_state["edges"])

        diag_text = ""
        for d in self._diagnostics:
            diag_text += f"[{d['agent']}] {d['event']}: {d['detail']}\n"

        context = (
            f"## Agent Diagnostic Context\n\n"
            f"**Session ID:** {self.session_id}\n\n"
            f"### Key Diagnostic Facts\n"
            f"- **Builder used fallback (LLM tool calling FAILED, direct plan execution used):** {used_fallback_builder}\n"
            f"- **Review iterations needed:** {iterations} (max is {MAX_REVIEW_ITERATIONS})\n"
            f"- **Planner output:** {plan_node_count} nodes, {plan_edge_count} edges\n"
            f"- **Builder output:** {built_node_count} nodes, {built_edge_count} edges\n"
            f"- **Node count match (planner vs builder):** {'YES' if plan_node_count == built_node_count else 'NO — MISMATCH'}\n"
            f"- **Edge count match (planner vs builder):** {'YES' if plan_edge_count == built_edge_count else 'NO — MISMATCH'}\n"
            f"- **Reviewer approved on first pass:** {'YES' if iterations == 1 else 'NO'}\n\n"
            f"### Step-by-Step Diagnostic Log (MOST IMPORTANT — analyze each line)\n"
            f"```\n{diag_text}\n```\n\n"
            f"### What the Reviewer Agent said\n```json\n{json.dumps(review, indent=2)}\n```\n\n"
            f"### Conversation summary\n```\n{conversation_summary}\n```\n"
        )

        try:
            feedback_agent = create_feedback_agent(self.llm)
            report_text = await _run_agent(feedback_agent, [
                {"role": "user", "content": context}
            ])
        except Exception as exc:
            logger.error(f"Feedback agent failed: {exc}")
            report_text = f"# Feedback Report\n\nFeedback agent failed: {exc}\n"

        if not report_text or len(report_text.strip()) < 20:
            report_text = (
                f"# Feedback Report\n\n"
                f"Session {self.session_id} completed with {len(self.graph_state['nodes'])} nodes.\n"
                f"Builder fallback used: {used_fallback_builder}\n"
                f"Review iterations: {iterations}\n"
            )

        # Strip <think> blocks from report
        import re
        report_text = re.sub(r"<think>.*?</think>", "", report_text, flags=re.DOTALL).strip()

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        reports_dir = "/app/reports"
        os.makedirs(reports_dir, exist_ok=True)
        report_path = os.path.join(reports_dir, f"report_{timestamp}.md")

        try:
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(report_text)
            logger.info(f"Feedback report saved: {report_path}")
        except Exception as exc:
            logger.error(f"Failed to save feedback report: {exc}")

        await self.session_mgr.update_artifact(self.session_id, "feedback_report", report_text[:3000])
        await self.session_mgr.add_message(
            self.session_id, "assistant",
            f"Feedback report generated and saved.",
            agent="feedback",
        )
        self._ws("agent_message", {
            "agent": "feedback",
            "content": report_text[:1000],
        })
        self._ws("agent_done", {"agent": "feedback", "success": True})

    async def run_initial(self, user_prompt: str):
        """Handle the very first user prompt — runs the full sequential pipeline.

        Flow: Requirement Agent → Planner Agent → Builder Agent → Reviewer Agent
        Each agent completes fully before the next one starts.
        """
        await self.session_mgr.add_message(
            self.session_id, "user", user_prompt
        )

        # ── STEP 1: Requirement Agent ────────────────────────────────
        self._ws("status_change", {"status": "clarifying", "agent": "requirement"})
        self._ws("agent_thinking", {"agent": "requirement"})
        await self.session_mgr.update_status(self.session_id, "clarifying")

        req_agent = create_requirement_agent(self.llm)
        req_output = await _run_agent(req_agent, [
            {"role": "user", "content": user_prompt}
        ])
        self._diag("requirement", "raw_output", req_output[:300])

        spec = _extract_json(req_output)

        if spec and not spec.get("clear", True):
            self._diag("requirement", "asked_clarification", str(spec.get("questions", [])))
            questions = spec.get("questions", [])
            msg = "\n".join(f"- {q}" for q in questions) if questions else req_output
            await self.session_mgr.add_message(
                self.session_id, "assistant", msg, agent="requirement"
            )
            self._ws("agent_message", {"agent": "requirement", "content": msg})
            self._ws("needs_input", {"agent": "requirement", "reason": "clarification"})
            return

        if not spec:
            self._diag("requirement", "json_parse_failed", f"Could not parse JSON from output, used fallback spec. Raw: {req_output[:200]}")
            spec = {"clear": True, "functional_requirements": [user_prompt], "non_functional_requirements": [], "constraints": [], "node_types_needed": []}
        else:
            self._diag("requirement", "success", f"Parsed spec with {len(spec.get('functional_requirements', []))} requirements")

        await self.session_mgr.update_artifact(self.session_id, "spec", spec)
        await self.session_mgr.update_artifact(self.session_id, "requirement_output_raw", req_output)
        await self.session_mgr.add_message(
            self.session_id, "assistant",
            f"Requirements captured.",
            agent="requirement",
        )
        self._ws("agent_message", {"agent": "requirement", "content": json.dumps(spec)})
        self._ws("agent_done", {"agent": "requirement"})

        # ── STEPS 2-4: Sequential Planner → Builder → Reviewer ───────
        await self._run_plan_build_review(spec)

    async def run_followup(self, user_message: str):
        """Handle a follow-up message (answer to clarification, or edit request)."""
        await self.session_mgr.add_message(
            self.session_id, "user", user_message
        )

        session = await self.session_mgr.get(self.session_id)
        if not session:
            return

        status = session.get("status", "active")
        artifacts = session.get("artifacts", {})
        conversation = session.get("conversation", [])

        if status in ("clarifying", "active"):
            original = ""
            for m in conversation:
                if m.get("role") == "user":
                    original = m["content"]
                    break

            self._ws("status_change", {"status": "clarifying", "agent": "requirement"})
            self._ws("agent_thinking", {"agent": "requirement"})

            req_agent = create_requirement_agent(self.llm)
            msgs = [
                {"role": "user", "content": original},
            ]
            for m in conversation[1:]:
                msgs.append({"role": m["role"], "content": m["content"]})

            req_output = await _run_agent(req_agent, msgs)
            spec = _extract_json(req_output)

            if spec and not spec.get("clear", True):
                user_message_count = sum(1 for m in conversation if m.get("role") == "user")
                if user_message_count >= 2:
                    # User already replied at least once; avoid repeated questions — treat as clear
                    spec = {
                        "clear": True,
                        "functional_requirements": [original] + [m.get("content", "") for m in conversation if m.get("role") == "user"][1:],
                        "non_functional_requirements": [],
                        "constraints": [],
                        "node_types_needed": [],
                    }
                else:
                    questions = spec.get("questions", [])
                    msg = "\n".join(f"- {q}" for q in questions) if questions else req_output
                    await self.session_mgr.add_message(
                        self.session_id, "assistant", msg, agent="requirement"
                    )
                    self._ws("agent_message", {"agent": "requirement", "content": msg})
                    self._ws("needs_input", {"agent": "requirement", "reason": "clarification"})
                    return

            if not spec:
                spec = {"clear": True, "functional_requirements": [user_message], "non_functional_requirements": [], "constraints": [], "node_types_needed": []}

            await self.session_mgr.update_artifact(self.session_id, "spec", spec)
            await self.session_mgr.update_artifact(self.session_id, "requirement_output_raw", req_output)
            self._ws("agent_message", {"agent": "requirement", "content": json.dumps(spec)})
            await self._run_plan_build_review(spec)

        elif status == "waiting_for_secrets":
            self._diag("builder", "secrets_received", "User submitted secrets, resuming review")
            graph = artifacts.get("graph")
            if graph:
                self.graph_state = graph
            spec = artifacts.get("spec", {})
            plan = artifacts.get("plan", {})
            review = artifacts.get("review", {})
            await self._run_review_and_finish(spec, plan, review)

        elif status in ("approved", "completed"):
            self._ws("agent_message", {
                "agent": "reviewer",
                "content": "The workflow has already been approved. You can save it or start a new session.",
            })
        else:
            self._ws("agent_message", {
                "agent": "requirement",
                "content": "Processing your feedback...",
            })
            spec = artifacts.get("spec", {})
            spec["functional_requirements"] = spec.get("functional_requirements", []) + [user_message]
            await self.session_mgr.update_artifact(self.session_id, "spec", spec)
            self.graph_state = {"nodes": [], "edges": []}
            await self._run_plan_build_review(spec)

    async def _run_plan_build_review(self, spec: dict):
        """Run Planner → Builder → Reviewer in strict sequential order.

        Each agent must finish completely before the next one starts.
        If the Reviewer rejects, the loop restarts at Planner with feedback.
        """
        iteration = 0
        feedback = ""

        while iteration < MAX_REVIEW_ITERATIONS:
            iteration += 1
            used_fallback_builder = False

            # ── STEP 2: Planner Agent (waits for Requirement to finish) ──
            self._ws("status_change", {"status": "planning", "agent": "planner"})
            self._ws("agent_thinking", {"agent": "planner"})
            await self.session_mgr.update_status(self.session_id, "planning")

            planner = create_planner_agent(self.llm, self.graph_state, self._ws)
            context = await self._build_prompt_context()
            plan_prompt = (
                f"Conversation context (most recent first/last {self._context_limit()} messages):\n"
                f"{context}\n\n"
                f"Specification:\n{json.dumps(spec, indent=2)}"
            )
            if feedback:
                plan_prompt += f"\n\nReviewer feedback from previous iteration:\n{feedback}"

            plan_output = await _run_agent(planner, [
                {"role": "user", "content": plan_prompt}
            ], recursion_limit=120)
            self._diag("planner", "raw_output", plan_output[:400])
            has_think = "<think>" in plan_output
            if has_think:
                self._diag("planner", "had_think_block", "Model output contained <think> tags that had to be stripped")
            plan = _extract_json(plan_output)

            if not plan or "nodes" not in plan:
                self._diag("planner", "json_parse_failed", f"Could not extract valid JSON with 'nodes' key. Raw start: {plan_output[:200]}")
                logger.error(f"Planner JSON extraction failed. Raw output:\n{plan_output[:1000]}")
                self._ws("error", {"agent": "planner", "message": f"Planner failed to produce a valid plan. Raw: {plan_output[:300]}"})
                self._ws("agent_done", {"agent": "planner", "success": False})
                await self.session_mgr.update_status(self.session_id, "failed")
                return
            self._diag("planner", "success", f"Plan: {len(plan['nodes'])} nodes, {len(plan.get('edges',[]))} edges")

            # ── STEP 2b: Pre-validate plan edges against handle compatibility ──
            edge_issues = validate_plan_edges(plan)
            if edge_issues:
                self._diag("planner", "edge_validation_issues", "; ".join(edge_issues[:5]))
                logger.warning(f"Plan edge issues ({len(edge_issues)}): {edge_issues}")
                self._auto_fix_plan_edges(plan)
                fixed_issues = validate_plan_edges(plan)
                if fixed_issues:
                    self._diag("planner", "edge_fix_partial", f"{len(edge_issues) - len(fixed_issues)} edges fixed, {len(fixed_issues)} remaining")
                else:
                    self._diag("planner", "edge_fix_complete", f"All {len(edge_issues)} edge issues auto-fixed")
            else:
                self._diag("planner", "edge_validation_passed", "All plan edges are valid")

            required_issues = validate_plan_required_connections(plan)
            if required_issues:
                self._diag("planner", "required_connections_missing", "; ".join(required_issues[:5]))
                logger.warning(f"Plan missing required config connections: {required_issues}")
                self._ws("error", {"agent": "planner", "message": "Plan incomplete: " + required_issues[0]})
                self._ws("agent_done", {"agent": "planner", "success": False})
                await self.session_mgr.update_status(self.session_id, "failed")
                return

            await self.session_mgr.update_artifact(self.session_id, "plan", plan)
            await self.session_mgr.add_message(
                self.session_id, "assistant",
                f"Plan created with {len(plan['nodes'])} nodes and {len(plan.get('edges', []))} edges.",
                agent="planner",
            )
            self._ws("agent_message", {
                "agent": "planner",
                "content": plan.get("explanation", f"{len(plan['nodes'])} nodes planned."),
            })
            self._ws("agent_done", {"agent": "planner", "success": True})

            # ── STEP 3: Builder Agent — direct from plan (fast, no LLM) ──────
            self._ws("status_change", {"status": "building", "agent": "builder"})
            self._ws("agent_thinking", {"agent": "builder"})
            await self.session_mgr.update_status(self.session_id, "building")

            self.graph_state = {"nodes": [], "edges": []}
            used_fallback_builder = True
            self._diag("builder", "direct_build", "Building directly from plan (optimized path)")
            self._execute_plan_directly(plan)

            await self.session_mgr.update_artifact(self.session_id, "graph", self.graph_state)
            await self.session_mgr.add_message(
                self.session_id, "assistant",
                f"Built {len(self.graph_state['nodes'])} nodes and {len(self.graph_state['edges'])} edges.",
                agent="builder",
            )
            self._ws("agent_message", {
                "agent": "builder",
                "content": f"Built {len(self.graph_state['nodes'])} nodes and {len(self.graph_state['edges'])} edges.",
            })
            self._ws("agent_done", {"agent": "builder", "success": True})

            # ── STEP 3b: Scan for missing secrets ─────────────────────────
            missing_secrets = scan_missing_secrets(self.graph_state)
            if missing_secrets:
                self._diag("builder", "secrets_needed", f"{len(missing_secrets)} secret fields need user input")
                await self.session_mgr.update_status(self.session_id, "waiting_for_secrets")
                self._ws("needs_input", {
                    "agent": "builder",
                    "reason": "secrets_needed",
                    "fields": missing_secrets,
                })
                await self.session_mgr.add_message(
                    self.session_id, "assistant",
                    f"The workflow needs {len(missing_secrets)} secret value(s) (API keys, passwords). Please provide them to continue.",
                    agent="builder",
                )
                return

            # ── STEP 4: Reviewer Agent (waits for Builder to finish) ─────
            self._ws("status_change", {"status": "reviewing", "agent": "reviewer"})
            self._ws("agent_thinking", {"agent": "reviewer"})
            await self.session_mgr.update_status(self.session_id, "reviewing")

            reviewer = create_reviewer_agent(self.llm, self.graph_state, self._ws)
            session = await self.session_mgr.get(self.session_id)
            artifacts = session.get("artifacts", {}) if session else {}
            req_raw = artifacts.get("requirement_output_raw", "")
            context = await self._build_prompt_context()
            review_prompt = (
                f"Conversation context:\n{context}\n\n"
                f"RequirementOutput (raw):\n{req_raw}\n\n"
                f"Review this workflow against the specification.\n\n"
                f"Specification:\n{json.dumps(spec, indent=2)}\n\n"
                f"Call get_current_graph and validate_graph to inspect the built graph."
            )
            review_output = await _run_agent(reviewer, [
                {"role": "user", "content": review_prompt}
            ])
            self._diag("reviewer", "raw_output", review_output[:300])
            review = _extract_json(review_output)

            if not review:
                self._diag("reviewer", "json_parse_failed", f"Could not parse reviewer JSON, auto-approving. Raw: {review_output[:200]}")
                review = {"approved": True, "issues": [], "suggestions": [], "feedback": "Auto-approved (reviewer output not parseable)."}
            else:
                self._diag("reviewer", "parsed", f"approved={review.get('approved')}, issues={len(review.get('issues',[]))}")

            await self.session_mgr.update_artifact(self.session_id, "review", review)

            if review.get("approved", False):
                await self.session_mgr.add_message(
                    self.session_id, "assistant",
                    f"Workflow approved! {review.get('feedback', '')}",
                    agent="reviewer",
                )
                self._ws("agent_message", {
                    "agent": "reviewer",
                    "content": f"Approved: {review.get('feedback', 'Workflow looks good.')}",
                })
                self._ws("agent_done", {"agent": "reviewer", "success": True})
                self._ws("status_change", {"status": "approved"})
                await self.session_mgr.update_status(self.session_id, "approved")

                await self._run_feedback_agent(spec, plan, review, iteration, used_fallback_builder=used_fallback_builder)
                return

            # Reviewer rejected — loop back to Planner with feedback
            feedback = review.get("feedback", "") + "\nIssues: " + json.dumps(review.get("issues", []))
            await self.session_mgr.add_message(
                self.session_id, "assistant",
                f"Review iteration {iteration}: {feedback}",
                agent="reviewer",
            )
            self._ws("agent_message", {
                "agent": "reviewer",
                "content": f"Iteration {iteration} — requesting changes: {feedback}",
            })
            self._ws("agent_done", {"agent": "reviewer", "success": False})

        self._ws("agent_message", {
            "agent": "reviewer",
            "content": "Max review iterations reached. Auto-approving with warnings.",
        })
        self._ws("agent_done", {"agent": "reviewer", "success": True})
        self._ws("status_change", {"status": "approved"})
        await self.session_mgr.update_status(self.session_id, "approved")

        await self._run_feedback_agent(spec, plan, review, iteration, used_fallback_builder=used_fallback_builder)

    async def _run_review_and_finish(self, spec: dict, plan: dict, prev_review: dict):
        """Run Reviewer + Feedback after secrets have been submitted."""
        self._ws("status_change", {"status": "reviewing", "agent": "reviewer"})
        self._ws("agent_thinking", {"agent": "reviewer"})
        await self.session_mgr.update_status(self.session_id, "reviewing")

        reviewer = create_reviewer_agent(self.llm, self.graph_state, self._ws)
        session = await self.session_mgr.get(self.session_id)
        artifacts = session.get("artifacts", {}) if session else {}
        req_raw = artifacts.get("requirement_output_raw", "")
        context = await self._build_prompt_context()
        review_prompt = (
            f"Conversation context:\n{context}\n\n"
            f"RequirementOutput (raw):\n{req_raw}\n\n"
            f"Review this workflow against the specification.\n\n"
            f"Specification:\n{json.dumps(spec, indent=2)}\n\n"
            f"Call get_current_graph and validate_graph to inspect the built graph."
        )
        review_output = await _run_agent(reviewer, [
            {"role": "user", "content": review_prompt}
        ])
        review = _extract_json(review_output)
        if not review:
            review = {"approved": True, "issues": [], "suggestions": [], "feedback": "Auto-approved after secrets submitted."}

        await self.session_mgr.update_artifact(self.session_id, "review", review)

        await self.session_mgr.add_message(
            self.session_id, "assistant",
            f"Workflow {'approved' if review.get('approved') else 'needs changes'}! {review.get('feedback', '')}",
            agent="reviewer",
        )
        self._ws("agent_message", {
            "agent": "reviewer",
            "content": f"{'Approved' if review.get('approved') else 'Issues found'}: {review.get('feedback', '')}",
        })
        self._ws("agent_done", {"agent": "reviewer", "success": review.get("approved", True)})
        self._ws("status_change", {"status": "approved"})
        await self.session_mgr.update_status(self.session_id, "approved")

        await self._run_feedback_agent(spec, plan, review, 1, used_fallback_builder=False)
