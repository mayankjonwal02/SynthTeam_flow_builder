"""Configuration for optimized multi-agent system."""

from typing import Dict, Any
from dataclasses import dataclass

@dataclass
class AgentConfig:
    """Configuration for individual agents."""
    timeout_seconds: int
    max_recursion: int
    max_retries: int
    batch_size: int
    
@dataclass 
class SystemConfig:
    """System-wide configuration."""
    max_concurrent_agents: int
    enable_caching: bool
    enable_batch_operations: bool
    enable_progress_tracking: bool
    log_level: str
    
# Optimized agent configurations
AGENT_CONFIGS = {
    "requirement": AgentConfig(
        timeout_seconds=30,
        max_recursion=25,
        max_retries=1,
        batch_size=1
    ),
    "planner": AgentConfig(
        timeout_seconds=60,
        max_recursion=40,
        max_retries=1,
        batch_size=1
    ),
    "builder": AgentConfig(
        timeout_seconds=120,
        max_recursion=30,
        max_retries=1,
        batch_size=50  # Batch operations for efficiency
    ),
    "reviewer": AgentConfig(
        timeout_seconds=30,
        max_recursion=20,
        max_retries=1,
        batch_size=1
    ),
    "feedback": AgentConfig(
        timeout_seconds=15,
        max_recursion=15,
        max_retries=1,
        batch_size=1
    )
}

# System configuration
SYSTEM_CONFIG = SystemConfig(
    max_concurrent_agents=5,
    enable_caching=True,
    enable_batch_operations=True,
    enable_progress_tracking=True,
    log_level="INFO"
)

# Performance thresholds
PERFORMANCE_THRESHOLDS = {
    "agent_timeout_warning": 0.8,  # 80% of timeout
    "slow_agent_threshold": 45,      # seconds
    "fast_agent_threshold": 10,      # seconds
    "max_plan_nodes": 20,           # Maximum nodes in a plan
    "max_plan_edges": 30,           # Maximum edges in a plan
    "max_context_messages": 30,     # Maximum context messages
    "max_retry_attempts": 2           # Maximum retry attempts
}

# Hallucination reduction settings
HALLUCINATION_SETTINGS = {
    "enable_structured_output": True,
    "enforce_json_schema": True,
    "strip_think_blocks": True,
    "validate_tool_calls": True,
    "max_tool_calls_per_agent": 100,
    "enable_fallback_validation": True
}

# Caching configuration
CACHE_SETTINGS = {
    "component_catalog_ttl": 300,    # 5 minutes
    "workflow_patterns_ttl": 600,    # 10 minutes  
    "validation_cache_ttl": 60,       # 1 minute
    "max_cache_size": 1000,          # Maximum cached items
    "enable_redis_cache": True         # Enable Redis caching
}

# Batch operation settings
BATCH_SETTINGS = {
    "max_nodes_per_batch": 20,         # Maximum nodes per batch
    "max_edges_per_batch": 30,         # Maximum edges per batch
    "enable_parallel_processing": True,  # Enable parallel processing
    "batch_timeout_seconds": 30,        # Batch operation timeout
    "retry_failed_batches": True       # Retry failed batch operations
}

def get_agent_config(agent_name: str) -> AgentConfig:
    """Get configuration for specific agent."""
    return AGENT_CONFIGS.get(agent_name, AgentConfig(
        timeout_seconds=30,
        max_recursion=25,
        max_retries=1,
        batch_size=1
    ))

def get_performance_threshold(key: str) -> Any:
    """Get performance threshold value."""
    return PERFORMANCE_THRESHOLDS.get(key)

def get_cache_setting(key: str) -> Any:
    """Get cache setting value."""
    return CACHE_SETTINGS.get(key)

def get_batch_setting(key: str) -> Any:
    """Get batch setting value."""
    return BATCH_SETTINGS.get(key)