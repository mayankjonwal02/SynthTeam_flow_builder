"""Hierarchical agent system — supervisor delegates to sub-agents."""

import logging
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger("uvicorn.error")


async def run_hierarchical(
    supervisor_config: Dict[str, Any],
    sub_agents: List[Dict[str, Any]],
    user_input: str,
    llm_factory=None,
    tool_factory=None,
) -> Dict[str, Any]:
    """Supervisor agent delegates tasks to sub-agents and aggregates results."""
    from app.ai.agents.react_agent import run_react_agent

    t0 = time.perf_counter()

    sub_descriptions = "\n".join(
        f"- {a['id']}: {a.get('description', a.get('system_prompt', 'general assistant'))}"
        for a in sub_agents
    )

    supervisor_llm = llm_factory(supervisor_config) if llm_factory else None
    supervisor_prompt = (
        f"You are a supervisor agent. Delegate the following task to the appropriate sub-agents.\n"
        f"Available agents:\n{sub_descriptions}\n\n"
        f"Task: {user_input}\n\n"
        f"Respond with a JSON array of delegations: "
        f'[{{"agent_id": "...", "task": "..."}}]'
    )

    supervisor_result = await run_react_agent(
        supervisor_llm, [], supervisor_prompt, max_iterations=3,
    )

    import json
    try:
        delegations = json.loads(supervisor_result["output"])
    except (json.JSONDecodeError, TypeError):
        delegations = [{"agent_id": sub_agents[0]["id"], "task": user_input}] if sub_agents else []

    sub_results = {}
    agent_map = {a["id"]: a for a in sub_agents}

    for delegation in delegations:
        agent_id = delegation.get("agent_id", "")
        task = delegation.get("task", user_input)
        agent_cfg = agent_map.get(agent_id)
        if not agent_cfg:
            continue

        llm = llm_factory(agent_cfg) if llm_factory else None
        tools = tool_factory(agent_cfg.get("tools", [])) if tool_factory else []
        result = await run_react_agent(llm, tools, task, max_iterations=agent_cfg.get("max_iterations", 5))
        sub_results[agent_id] = result

    aggregation_prompt = (
        f"Original task: {user_input}\n\n"
        f"Sub-agent results:\n" +
        "\n".join(f"- {k}: {v.get('output', '')[:500]}" for k, v in sub_results.items()) +
        "\n\nSynthesize a final answer."
    )
    final = await run_react_agent(supervisor_llm, [], aggregation_prompt, max_iterations=3)

    elapsed = round((time.perf_counter() - t0) * 1000, 2)
    return {
        "output": final["output"],
        "delegations": delegations,
        "sub_results": {k: v.get("output", "") for k, v in sub_results.items()},
        "supervisor_trace": supervisor_result.get("reasoning_trace", []),
        "latency_ms": elapsed,
    }
