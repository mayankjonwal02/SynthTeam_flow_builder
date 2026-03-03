"""Autonomous agent — plans steps dynamically and selects tools."""

import json
import logging
import time
from typing import Any, Dict, List

logger = logging.getLogger("uvicorn.error")


async def run_autonomous_agent(
    llm,
    tools: List[Any],
    goal: str,
    max_steps: int = 10,
    system_prompt: str = None,
    subagent_configs: List[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Agent that plans steps, selects tools, and executes autonomously."""
    from app.ai.agents.react_agent import run_react_agent

    t0 = time.perf_counter()
    system_prompt = (system_prompt or "").strip()
    subagent_configs = subagent_configs or []

    tool_descriptions = "\n".join(
        f"- {t.name}: {t.description}" for t in tools
    )

    planning_prompt = (
        f"Given a high-level goal, create a step-by-step plan.\n\n"
        f"Available tools:\n{tool_descriptions}\n\n"
        f"Goal: {goal}\n\n"
        f"Output a JSON array of steps: "
        f'[{{"step": 1, "action": "description", "tool": "tool_name or none"}}]'
    )

    plan_result = await run_react_agent(llm, [], planning_prompt, max_iterations=3, system_prompt=system_prompt or None)

    try:
        steps = json.loads(plan_result["output"])
    except (json.JSONDecodeError, TypeError):
        steps = [{"step": 1, "action": goal, "tool": "none"}]

    execution_log = []
    accumulated_context = ""

    for i, step in enumerate(steps[:max_steps]):
        action = step.get("action", "")
        step_prompt = (
            f"Execute this step: {action}\n\n"
            f"Context from previous steps:\n{accumulated_context}"
        )
        step_result = await run_react_agent(llm, tools, step_prompt, max_iterations=5, system_prompt=system_prompt or None)
        execution_log.append({
            "step": i + 1,
            "action": action,
            "result": step_result["output"][:500],
            "tools_called": step_result.get("tools_called", []),
        })
        accumulated_context += f"\nStep {i+1} ({action}): {step_result['output'][:300]}\n"

    final_prompt = f"Summarize the results of completing the goal: {goal}\n\nExecution log:\n{accumulated_context}"
    final = await run_react_agent(llm, [], final_prompt, max_iterations=2, system_prompt=system_prompt or None)

    elapsed = round((time.perf_counter() - t0) * 1000, 2)
    return {
        "output": final["output"],
        "plan": steps,
        "execution_log": execution_log,
        "total_steps": len(execution_log),
        "latency_ms": elapsed,
    }
