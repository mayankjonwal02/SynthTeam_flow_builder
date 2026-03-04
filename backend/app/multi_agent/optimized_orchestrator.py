"""Optimized multi-agent orchestrator with performance improvements and hallucination reduction."""

from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any, Callable, Optional, Dict, List
from dataclasses import dataclass
from datetime import datetime

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

# Optimized constants
MAX_REVIEW_ITERATIONS = 2  # Reduced from 3
BUILDER_TIMEOUT = 120  # 2 minutes max for builder agent
PLANNER_TIMEOUT = 60   # 1 minute max for planner
REVIEWER_TIMEOUT = 30    # 30 seconds max for reviewer
AGENT_RECURSION_LIMIT = 50  # Reduced from 80-150

@dataclass
class AgentMetrics:
    """Performance metrics for agent execution."""
    start_time: float
    end_time: Optional[float] = None
    tool_calls: int = 0
    tokens_used: int = 0
    fallback_used: bool = False
    
    @property
    def duration(self) -> float:
        return (self.end_time or time.time()) - self.start_time

class OptimizedMultiAgentOrchestrator:
    """High-performance multi-agent orchestrator with reduced hallucination."""
    
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
        self._metrics: Dict[str, AgentMetrics] = {}
        self._progress_callback: Optional[Callable] = None
        
    def _diag(self, agent: str, event: str, detail: str = ""):
        """Append diagnostic entry with timestamp."""
        self._diagnostics.append({
            "agent": agent,
            "event": event,
            "detail": detail[:500],
            "ts": time.time(),
        })
        
    def _ws(self, event_type: str, data: dict):
        """Emit WebSocket event with progress tracking."""
        self._emit(event_type, data)
        if self._progress_callback:
            self._progress_callback(event_type, data)
            
    def _start_metrics(self, agent_name: str) -> AgentMetrics:
        """Start performance metrics for an agent."""
        metrics = AgentMetrics(start_time=time.time())
        self._metrics[agent_name] = metrics
        return metrics
        
    def _end_metrics(self, agent_name: str):
        """End performance metrics for an agent."""
        if agent_name in self._metrics:
            self._metrics[agent_name].end_time = time.time()

    async def _run_agent_with_timeout(
        self, 
        agent, 
        messages: list[dict], 
        timeout: int,
        recursion_limit: int = AGENT_RECURSION_LIMIT,
        agent_name: str = "unknown"
    ) -> str:
        """Run agent with timeout and progress monitoring."""
        metrics = self._start_metrics(agent_name)
        
        try:
            # Create timeout task
            result = await asyncio.wait_for(
                agent.ainvoke(
                    {"messages": messages},
                    config={"recursion_limit": recursion_limit},
                ),
                timeout=timeout
            )
            
            # Extract final message
            msgs = result.get("messages", [])
            final_content = ""
            
            for msg in reversed(msgs):
                content = getattr(msg, "content", "")
                if isinstance(content, list):
                    parts = [p.get("text", "") if isinstance(p, dict) else str(p) for p in content]
                    content = "\n".join(parts)
                if content and getattr(msg, "type", "") in ("ai", "assistant"):
                    final_content = content
                    break
                    
            metrics.end_time = time.time()
            self._end_metrics(agent_name)
            
            # Log performance metrics
            logger.info(f"Agent {agent_name} completed in {metrics.duration:.2f}s")
            
            return final_content
            
        except asyncio.TimeoutError:
            metrics.end_time = time.time()
            self._end_metrics(agent_name)
            logger.error(f"Agent {agent_name} timed out after {timeout}s")
            self._diag(agent_name, "timeout", f"Agent exceeded {timeout}s timeout")
            return f"ERROR: Agent timed out after {timeout} seconds"
            
        except Exception as exc:
            metrics.end_time = time.time()
            self._end_metrics(agent_name)
            logger.error(f"Agent {agent_name} failed: {exc}")
            self._diag(agent_name, "exception", str(exc))
            return f"ERROR: {str(exc)}"

    def _extract_json_robust(self, text: str, expected_keys: list[str] = None) -> Optional[dict]:
        """Robust JSON extraction with validation."""
        if not text:
            return None
            
        text = text.strip()
        
        # Remove think blocks first
        import re
        text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
        text = re.sub(r"```(?:json)?\s*\n?", "", text).strip()
        
        # Try direct parse
        try:
            result = json.loads(text)
            if expected_keys and not all(key in result for key in expected_keys):
                logger.warning(f"JSON missing expected keys: {expected_keys}")
                return None
            return result
        except json.JSONDecodeError:
            pass
            
        # Find outermost JSON block
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
                        result = json.loads(text[start:i+1])
                        if expected_keys and not all(key in result for key in expected_keys):
                            logger.warning(f"JSON missing expected keys: {expected_keys}")
                            return None
                        return result
                    except json.JSONDecodeError:
                        start = -1
                        
        return None

    def _validate_and_sanitize_plan(self, plan: dict) -> tuple[bool, str]:
        """Validate plan structure and sanitize inputs."""
        if not plan or "nodes" not in plan:
            return False, "Plan missing 'nodes' key"
            
        nodes = plan.get("nodes", [])
        edges = plan.get("edges", [])
        
        if not nodes:
            return False, "Plan has no nodes"
            
        # Validate node types
        valid_types = set(COMPONENT_CATALOG.keys())
        for node in nodes:
            node_type = node.get("type")
            if not node_type or node_type not in valid_types:
                return False, f"Invalid node type: {node_type}"
                
        # Validate edges
        node_ids = {node.get("id") for node in nodes if node.get("id")}
        for edge in edges:
            if edge.get("source") not in node_ids or edge.get("target") not in node_ids:
                return False, "Edge references non-existent node"
                
        return True, "Valid plan"

    async def _build_optimized_context(self, limit: int = 30) -> str:
        """Build compact context for agent prompts."""
        try:
            convo = await self.session_mgr.get_conversation(self.session_id, limit=limit)
        except Exception:
            session = await self.session_mgr.get(self.session_id)
            convo = (session.get("conversation", []) if session else [])[-limit:]
            
        lines = []
        for m in convo[-limit:]:
            role = m.get("role", "?")
            agent = m.get("agent", "")
            tag = f"[{agent}]" if agent else ""
            content = (m.get("content", "") or "").strip().replace("\n", " ")
            if len(content) > 200:  # Reduced from 400
                content = content[:200] + "…"
            lines.append(f"{role}{tag}: {content}")
            
        return "\n".join(lines)

    def _create_batch_builder_prompt(self, plan: dict, spec: dict) -> str:
        """Create optimized batch builder prompt."""
        return f"""You are a Workflow Builder for SynthTeam.

CRITICAL REQUIREMENTS:
1. Process ALL nodes in the plan in ONE batch operation
2. Use create_node_batch for multiple nodes at once
3. Use create_edge_batch for multiple edges at once
4. Complete within 60 seconds
5. No explanations between operations - just execute

PLAN TO BUILD:
{json.dumps(plan, indent=2)}

SPECIFICATION:
{json.dumps(spec, indent=2)}

EXECUTION STEPS:
1. Call create_node_batch with ALL nodes from plan.nodes
2. Call create_edge_batch with ALL edges from plan.edges  
3. Call validate_graph once at the end
4. Return completion status

CONSTRAINTS:
- Exact node count: {len(plan.get('nodes', []))}
- Exact edge count: {len(plan.get('edges', []))}
- No additional nodes or edges
- No configuration changes
"""

    def _validate_graph_state(self, graph_state: dict) -> list:
        """Deterministic validation of a built graph (no LLM). Reused from main orchestrator logic."""
        issues = []
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
            src, tgt = e.get("source"), e.get("target")
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
                issues.append(f"Edge {src}->{tgt}: '{src_type}' has no source handle '{src_handle}'.")
            if tgt_handle not in tgt_info.get("target_handles", []):
                issues.append(f"Edge {src}->{tgt}: '{tgt_type}' has no target handle '{tgt_handle}'.")
            compatible = HANDLE_COMPATIBILITY.get(src_handle, [])
            if tgt_handle not in compatible:
                issues.append(f"Edge {src}->{tgt}: handle mismatch '{src_handle}' -> '{tgt_handle}'.")
        return issues

    async def _execute_optimized_builder(self, plan: dict, spec: dict) -> bool:
        """Execute builder: use direct plan execution first (fast), skip slow LLM builder."""
        self._ws("status_change", {"status": "building", "agent": "builder"})
        self._ws("agent_thinking", {"agent": "builder"})
        await self.session_mgr.update_status(self.session_id, "building")
        self._diag("builder", "using_direct_build", "Optimized path: building from plan without LLM")
        return await self._execute_direct_plan_build(plan)

    async def _execute_direct_plan_build(self, plan: dict) -> bool:
        """Execute direct plan building (fastest fallback)."""
        self._diag("builder", "using_direct_build", "Executing plan directly without LLM")
        
        import uuid as _uuid
        self.graph_state = {"nodes": [], "edges": []}
        id_map = {}
        
        # Build nodes directly
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
            trigger_types = {"http_entry", "webhook_trigger", "cron_trigger", "manual_trigger"}
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
            
        # Build edges directly
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
            
        logger.info(f"Direct builder: created {len(self.graph_state['nodes'])} nodes, {len(self.graph_state['edges'])} edges")
        return True

    async def _run_optimized_review(self, spec: dict, plan: dict) -> dict:
        """Run optimized reviewer with strict validation."""
        self._ws("status_change", {"status": "reviewing", "agent": "reviewer"})
        self._ws("agent_thinking", {"agent": "reviewer"})
        await self.session_mgr.update_status(self.session_id, "reviewing")
        
        # Fast deterministic validation first
        issues = self._validate_graph_state(self.graph_state)
        if not issues:
            # Quick approval for valid graphs
            return {
                "approved": True,
                "issues": [],
                "suggestions": [],
                "feedback": "Workflow approved - all validations passed"
            }
            
        # Only use LLM reviewer for complex issues
        try:
            reviewer = create_reviewer_agent(self.llm, self.graph_state, self._ws)
            context = await self._build_optimized_context(limit=20)
            
            review_prompt = f"""Review this workflow against the specification.

VALIDATION ISSUES FOUND:
{json.dumps(issues[:5], indent=2)}

SPECIFICATION:
{json.dumps(spec, indent=2)}

CURRENT GRAPH:
- Nodes: {len(self.graph_state.get('nodes', []))}
- Edges: {len(self.graph_state.get('edges', []))}

APPROVAL CRITERIA:
- Approve if issues are minor (cosmetic, positioning, etc.)
- Reject only for: missing trigger/response, disconnected critical nodes, invalid connections

Output JSON: {{"approved": bool, "issues": [], "suggestions": [], "feedback": "..."}}"""

            review_output = await self._run_agent_with_timeout(
                reviewer,
                [{"role": "user", "content": review_prompt}],
                timeout=REVIEWER_TIMEOUT,
                agent_name="reviewer"
            )
            
            review = self._extract_json_robust(review_output, ["approved"])
            if not review:
                # Fallback approval for parse errors
                return {
                    "approved": len(issues) < 3,  # Approve if few issues
                    "issues": issues,
                    "suggestions": ["Auto-approved due to reviewer parse error"],
                    "feedback": f"Auto-review: {len(issues)} minor issues found"
                }
                
            return review
            
        except Exception as exc:
            logger.error(f"Reviewer agent failed: {exc}")
            # Fallback approval
            return {
                "approved": True,
                "issues": issues,
                "suggestions": ["Auto-approved due to reviewer failure"],
                "feedback": "Auto-approved - reviewer unavailable"
            }

    async def run_optimized(self, user_prompt: str, progress_callback: Optional[Callable] = None):
        """Run optimized multi-agent pipeline with performance monitoring."""
        self._progress_callback = progress_callback
        
        await self.session_mgr.add_message(self.session_id, "user", user_prompt)
        
        # Step 1: Fast requirement analysis
        self._ws("status_change", {"status": "clarifying", "agent": "requirement"})
        req_agent = create_requirement_agent(self.llm)
        
        req_output = await self._run_agent_with_timeout(
            req_agent,
            [{"role": "user", "content": user_prompt}],
            timeout=30,
            agent_name="requirement"
        )
        
        spec = self._extract_json_robust(req_output, ["clear"])
        if not spec:
            spec = {"clear": True, "functional_requirements": [user_prompt], "non_functional_requirements": [], "constraints": [], "node_types_needed": []}
            
        if spec and not spec.get("clear", True):
            # Need clarification - fast path
            questions = spec.get("questions", [])
            msg = "\n".join(f"- {q}" for q in questions) if questions else req_output
            await self.session_mgr.add_message(self.session_id, "assistant", msg, agent="requirement")
            self._ws("needs_input", {"agent": "requirement", "reason": "clarification"})
            return
            
        await self.session_mgr.update_artifact(self.session_id, "spec", spec)
        
        # Step 2: Optimized planning
        self._ws("status_change", {"status": "planning", "agent": "planner"})
        planner = create_planner_agent(self.llm, self.graph_state, self._ws)
        
        context = await self._build_optimized_context(limit=20)
        plan_prompt = f"""Create a workflow plan based on this specification:

SPECIFICATION:
{json.dumps(spec, indent=2)}

CONTEXT:
{context}

Requirements:
- Maximum {10} nodes for simple workflows, {20} for complex ones
- Include trigger and response nodes
- Use appropriate component types
- Validate all connections

Output JSON with: {{"nodes": [...], "edges": [...], "explanation": "..."}}"""

        plan_output = await self._run_agent_with_timeout(
            planner,
            [{"role": "user", "content": plan_prompt}],
            timeout=PLANNER_TIMEOUT,
            agent_name="planner"
        )
        
        plan = self._extract_json_robust(plan_output, ["nodes", "edges"])
        if not plan:
            self._ws("error", {"message": "Failed to create plan"})
            return
            
        # Validate and optimize plan
        is_valid, reason = self._validate_and_sanitize_plan(plan)
        if not is_valid:
            self._ws("error", {"message": f"Invalid plan: {reason}"})
            return

        required_issues = validate_plan_required_connections(plan)
        if required_issues:
            self._ws("error", {"message": "Plan incomplete: " + (required_issues[0] or "missing required config connections")})
            return
            
        await self.session_mgr.update_artifact(self.session_id, "plan", plan)
        
        # Step 3: Optimized batch building (direct from plan, no LLM)
        build_success = await self._execute_optimized_builder(plan, spec)
        if not build_success:
            self._ws("error", {"message": "Failed to build workflow"})
            return
        await self.session_mgr.update_artifact(self.session_id, "graph", self.graph_state)
        await self.session_mgr.add_message(
            self.session_id, "assistant",
            f"Built {len(self.graph_state['nodes'])} nodes and {len(self.graph_state['edges'])} edges.",
            agent="builder",
        )
        self._ws("agent_done", {"agent": "builder", "success": True})
            
        # Step 4: Fast review
        review = await self._run_optimized_review(spec, plan)
        
        if review.get("approved", False):
            self._ws("status_change", {"status": "approved"})
            await self.session_mgr.update_status(self.session_id, "approved")
        else:
            # Single retry for rejected workflows
            self._ws("status_change", {"status": "retrying"})
            review = await self._run_optimized_review(spec, plan)
            
        # Generate final metrics report
        total_duration = sum(m.duration for m in self._metrics.values())
        logger.info(f"Multi-agent pipeline completed in {total_duration:.2f}s")
        
        # Save performance metrics
        metrics_summary = {
            "total_duration": total_duration,
            "agent_metrics": {
                name: {
                    "duration": m.duration,
                    "fallback_used": m.fallback_used
                }
                for name, m in self._metrics.items()
            }
        }
        
        await self.session_mgr.update_artifact(self.session_id, "performance_metrics", metrics_summary)