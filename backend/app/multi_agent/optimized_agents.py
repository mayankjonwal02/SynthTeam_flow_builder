"""Optimized agent factory functions with performance improvements."""

from __future__ import annotations

from typing import Callable, Optional
from langgraph.prebuilt import create_react_agent

from app.multi_agent.optimized_tools import (
    create_optimized_builder_tools,
    create_optimized_planner_tools
)
from app.multi_agent.optimized_prompts import (
    OPTIMIZED_REQUIREMENT_PROMPT,
    OPTIMIZED_PLANNER_PROMPT, 
    OPTIMIZED_BUILDER_PROMPT,
    OPTIMIZED_REVIEWER_PROMPT,
    get_structured_output_prompt,
    REQUIREMENT_SCHEMA,
    PLAN_SCHEMA,
    REVIEW_SCHEMA
)

def create_optimized_requirement_agent(llm):
    """Create optimized requirement agent with structured output."""
    # Add structured output enforcement
    structured_prompt = get_structured_output_prompt(
        REQUIREMENT_SCHEMA,
        "Analyze user requirements and determine if clarification is needed"
    )
    
    return create_react_agent(
        llm, 
        tools=[], 
        prompt=OPTIMIZED_REQUIREMENT_PROMPT + "\n\n" + structured_prompt
    )

def create_optimized_planner_agent(llm, graph_state: dict, ws_emitter: Optional[Callable] = None):
    """Create optimized planner agent with cached tools."""
    tools = create_optimized_planner_tools()
    
    # Add structured output enforcement
    structured_prompt = get_structured_output_prompt(
        PLAN_SCHEMA,
        "Create a complete workflow plan with nodes and edges"
    )
    
    return create_react_agent(
        llm, 
        tools=tools, 
        prompt=OPTIMIZED_PLANNER_PROMPT + "\n\n" + structured_prompt
    )

def create_optimized_builder_agent(llm, graph_state: dict, ws_emitter: Optional[Callable] = None):
    """Create optimized builder agent with batch operations."""
    tools = create_optimized_builder_tools(graph_state, ws_emitter)
    
    return create_react_agent(
        llm, 
        tools=tools, 
        prompt=OPTIMIZED_BUILDER_PROMPT
    )

def create_optimized_reviewer_agent(llm, graph_state: dict, ws_emitter: Optional[Callable] = None):
    """Create optimized reviewer agent with fast validation."""
    # Use minimal tools for fast validation
    from app.multi_agent.tools import get_current_graph, validate_graph_fast
    
    tools = [get_current_graph, validate_graph_fast]
    
    # Add structured output enforcement
    structured_prompt = get_structured_output_prompt(
        REVIEW_SCHEMA,
        "Review the built workflow and approve or reject with specific issues"
    )
    
    return create_react_agent(
        llm, 
        tools=tools, 
        prompt=OPTIMIZED_REVIEWER_PROMPT + "\n\n" + structured_prompt
    )

def create_optimized_feedback_agent(llm):
    """Create optimized feedback agent for post-session analysis."""
    # Simplified feedback agent without complex reasoning
    FEEDBACK_PROMPT = """You are a Multi-Agent System Analyst.

Generate a brief performance report covering:
1. Which agents succeeded/failed
2. Any timeouts or errors encountered  
3. Overall system performance (1-10 scale)
4. One key improvement suggestion

Keep it under 200 words. Focus on facts, not speculation."""
    
    return create_react_agent(llm, tools=[], prompt=FEEDBACK_PROMPT)

# Export optimized factory functions
__all__ = [
    'create_optimized_requirement_agent',
    'create_optimized_planner_agent', 
    'create_optimized_builder_agent',
    'create_optimized_reviewer_agent',
    'create_optimized_feedback_agent'
]