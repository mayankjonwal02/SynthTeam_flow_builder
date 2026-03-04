"""Optimized multi-agent system for SynthTeam with performance improvements and hallucination reduction."""

from __future__ import annotations

import logging

# Main optimized system components
from .optimized_system import (
    OptimizedMultiAgentSystem,
    create_optimized_multi_agent_system,
    process_optimized_workflow_request,
    get_system_performance_report
)

# Performance monitoring
from .performance_monitor import (
    PerformanceMonitor,
    AgentPerformanceMetrics,
    SessionMetrics,
    get_performance_monitor,
    log_agent_performance
)

# Configuration
from .optimized_config import (
    AGENT_CONFIGS,
    SYSTEM_CONFIG,
    PERFORMANCE_THRESHOLDS,
    HALLUCINATION_SETTINGS,
    CACHE_SETTINGS,
    BATCH_SETTINGS,
    get_agent_config,
    get_performance_threshold,
    get_cache_setting,
    get_batch_setting
)

# Optimized agents and tools
from .optimized_agents import (
    create_optimized_requirement_agent,
    create_optimized_planner_agent,
    create_optimized_builder_agent,
    create_optimized_reviewer_agent,
    create_optimized_feedback_agent
)

from .optimized_tools import (
    create_optimized_builder_tools,
    create_optimized_planner_tools
)

# Version and compatibility info
__version__ = "2.0.0"
__optimized__ = True

# Export main components for easy access
__all__ = [
    # Main system
    "OptimizedMultiAgentSystem",
    "create_optimized_multi_agent_system",
    "process_optimized_workflow_request",
    "get_system_performance_report",
    
    # Performance monitoring
    "PerformanceMonitor",
    "AgentPerformanceMetrics", 
    "SessionMetrics",
    "get_performance_monitor",
    "log_agent_performance",
    
    # Configuration
    "AGENT_CONFIGS",
    "SYSTEM_CONFIG",
    "PERFORMANCE_THRESHOLDS",
    "HALLUCINATION_SETTINGS",
    "get_agent_config",
    "get_performance_threshold",
    
    # Agents and tools
    "create_optimized_requirement_agent",
    "create_optimized_planner_agent",
    "create_optimized_builder_agent",
    "create_optimized_reviewer_agent",
    "create_optimized_builder_tools",
    "create_optimized_planner_tools",
    
    # Version info
    "__version__",
    "__optimized__"
]

# System initialization helper
def initialize_optimized_system():
    """Initialize the optimized multi-agent system."""
    logger = logging.getLogger("uvicorn.error")
    logger.info("Initializing optimized multi-agent system v2.0.0")
    
    # Log configuration
    logger.info(f"Agent timeouts: {get_agent_config('builder').timeout_seconds}s (builder), "
                f"{get_agent_config('planner').timeout_seconds}s (planner)")
    logger.info(f"Performance thresholds: {get_performance_threshold('slow_agent_threshold')}s (slow), "
                f"{get_performance_threshold('fast_agent_threshold')}s (fast)")
    logger.info(f"Optimization features: batch_operations={get_batch_setting('enable_parallel_processing')}, "
                f"caching={get_cache_setting('enable_redis_cache')}")
    
    return True

# Auto-initialize on import
if __name__ != "__main__":
    try:
        initialize_optimized_system()
    except Exception as e:
        logging.warning(f"Failed to initialize optimized system: {e}")