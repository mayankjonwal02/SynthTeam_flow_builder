"""ReAct agent using LangGraph create_react_agent."""

import logging
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger("uvicorn.error")


def _message_to_dict(msg: Any) -> dict:
    """Convert a LangChain message object to a plain dict for storage."""
    role = getattr(msg, "type", None) or getattr(msg, "role", None)
    if role == "ai":
        role = "assistant"
    content = getattr(msg, "content", "") or ""
    if isinstance(content, list):
        content = str(content)
    return {"role": role or "user", "content": content}


async def run_react_agent(
    llm,
    tools: List[Any],
    user_input: str,
    max_iterations: int = 10,
    memory: Optional[Any] = None,
    system_prompt: Optional[str] = None,
    previous_messages: Optional[List[dict]] = None,
) -> Dict[str, Any]:
    """Execute a ReAct agent and return output + trace.

    If previous_messages is provided (e.g. from a memory backend), they are prepended
    so the agent sees conversation history (multi-turn). The returned "messages" in
    result can be used to persist the conversation.
    """
    from langgraph.prebuilt import create_react_agent

    agent = create_react_agent(llm, tools)

    t0 = time.perf_counter()
    messages: List[dict] = []
    if system_prompt and system_prompt.strip():
        messages.append({"role": "system", "content": system_prompt.strip()})
    messages.extend(previous_messages or [])
    messages.append({"role": "user", "content": user_input})
    inputs = {"messages": messages}
    # Each ReAct "iteration" can use several graph steps (agent -> tools -> agent). Default recursion_limit
    # may be too low; set explicitly so the agent can run multiple tool-call rounds.
    recursion_limit = max(max_iterations * 10, 25)
    config = {"recursion_limit": recursion_limit}

    result = await agent.ainvoke(inputs, config=config)

    elapsed = round((time.perf_counter() - t0) * 1000, 2)

    messages = result.get("messages", [])
    final_output = ""
    tools_called = []
    reasoning_trace = []

    for msg in messages:
        msg_type = getattr(msg, "type", "")
        content = getattr(msg, "content", "")

        if msg_type == "ai":
            final_output = content
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tc in msg.tool_calls:
                    tools_called.append(tc.get("name", "unknown"))
        reasoning_trace.append({"type": msg_type, "content": str(content)[:500]})

    return {
        "output": final_output,
        "tools_called": tools_called,
        "reasoning_trace": reasoning_trace,
        "iterations": len([m for m in messages if getattr(m, "type", "") == "ai"]),
        "latency_ms": elapsed,
        "messages": messages,
    }
