"""Performance monitoring and metrics collection for optimized multi-agent system."""

from __future__ import annotations

import time
import logging
import asyncio
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
import json

logger = logging.getLogger("uvicorn.error")

@dataclass
class AgentPerformanceMetrics:
    """Performance metrics for a single agent execution."""
    agent_name: str
    start_time: float
    end_time: Optional[float] = None
    tool_calls: int = 0
    tokens_used: int = 0
    fallback_used: bool = False
    timeout_occurred: bool = False
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    @property
    def duration(self) -> float:
        return (self.end_time or time.time()) - self.start_time
    
    @property
    def is_slow(self) -> bool:
        return self.duration > 45.0  # 45 seconds threshold
    
    @property
    def is_fast(self) -> bool:
        return self.duration < 10.0  # 10 seconds threshold

@dataclass
class SessionMetrics:
    """Metrics for an entire multi-agent session."""
    session_id: str
    start_time: float
    end_time: Optional[float] = None
    total_duration: float = 0.0
    agent_metrics: Dict[str, AgentPerformanceMetrics] = field(default_factory=dict)
    total_tool_calls: int = 0
    total_tokens: int = 0
    fallback_count: int = 0
    error_count: int = 0
    success: bool = True
    
    def add_agent_metric(self, metric: AgentPerformanceMetrics):
        """Add metrics for an individual agent."""
        self.agent_metrics[metric.agent_name] = metric
        self.total_tool_calls += metric.tool_calls
        self.total_tokens += metric.tokens_used
        if metric.fallback_used:
            self.fallback_count += 1
        if metric.errors:
            self.error_count += len(metric.errors)
        if metric.timeout_occurred:
            self.success = False
    
    def finalize(self):
        """Finalize session metrics."""
        self.end_time = time.time()
        self.total_duration = self.end_time - self.start_time
        
        # Calculate aggregated metrics
        agent_durations = [m.duration for m in self.agent_metrics.values()]
        if agent_durations:
            self.avg_agent_duration = sum(agent_durations) / len(agent_durations)
            self.max_agent_duration = max(agent_durations)
            self.min_agent_duration = min(agent_durations)

class PerformanceMonitor:
    """Central performance monitoring for the multi-agent system."""
    
    def __init__(self):
        self.active_sessions: Dict[str, SessionMetrics] = {}
        self.completed_sessions: List[SessionMetrics] = []
        self.system_metrics = {
            "total_sessions": 0,
            "successful_sessions": 0,
            "failed_sessions": 0,
            "total_build_time": 0.0,
            "average_build_time": 0.0,
            "slow_builds": 0,
            "fast_builds": 0,
            "agent_performance": defaultdict(lambda: {
                "total_executions": 0,
                "avg_duration": 0.0,
                "timeouts": 0,
                "fallbacks": 0
            })
        }
        self._lock = asyncio.Lock()
    
    def start_session(self, session_id: str) -> SessionMetrics:
        """Start monitoring a new session."""
        metrics = SessionMetrics(
            session_id=session_id,
            start_time=time.time()
        )
        self.active_sessions[session_id] = metrics
        self.system_metrics["total_sessions"] += 1
        return metrics
    
    def get_session_metrics(self, session_id: str) -> Optional[SessionMetrics]:
        """Get metrics for a specific session."""
        return self.active_sessions.get(session_id) or next(
            (m for m in self.completed_sessions if m.session_id == session_id), None
        )
    
    def start_agent_execution(self, session_id: str, agent_name: str) -> AgentPerformanceMetrics:
        """Start monitoring an agent execution."""
        session = self.active_sessions.get(session_id)
        if not session:
            logger.warning(f"No active session found for {session_id}")
            return AgentPerformanceMetrics(agent_name, time.time())
        
        metrics = AgentPerformanceMetrics(agent_name, time.time())
        return metrics
    
    def end_agent_execution(self, session_id: str, metrics: AgentPerformanceMetrics):
        """End monitoring an agent execution."""
        session = self.active_sessions.get(session_id)
        if session:
            metrics.end_time = time.time()
            session.add_agent_metric(metrics)
            
            # Update system metrics
            agent_stats = self.system_metrics["agent_performance"][metrics.agent_name]
            agent_stats["total_executions"] += 1
            
            if metrics.timeout_occurred:
                agent_stats["timeouts"] += 1
            if metrics.fallback_used:
                agent_stats["fallbacks"] += 1
            
            # Update average duration
            if agent_stats["total_executions"] > 0:
                total_time = agent_stats["avg_duration"] * (agent_stats["total_executions"] - 1) + metrics.duration
                agent_stats["avg_duration"] = total_time / agent_stats["total_executions"]
    
    def end_session(self, session_id: str, success: bool = True):
        """End monitoring a session."""
        session = self.active_sessions.pop(session_id, None)
        if session:
            session.finalize()
            session.success = success
            
            self.completed_sessions.append(session)
            
            # Update system metrics
            if success:
                self.system_metrics["successful_sessions"] += 1
            else:
                self.system_metrics["failed_sessions"] += 1
            
            self.system_metrics["total_build_time"] += session.total_duration
            
            # Update build time statistics
            if self.system_metrics["total_sessions"] > 0:
                self.system_metrics["average_build_time"] = (
                    self.system_metrics["total_build_time"] / self.system_metrics["total_sessions"]
                )
            
            # Categorize build speed
            if session.total_duration > 60:  # 1 minute
                self.system_metrics["slow_builds"] += 1
            elif session.total_duration < 15:  # 15 seconds
                self.system_metrics["fast_builds"] += 1
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report."""
        total_sessions = self.system_metrics["total_sessions"]
        
        if total_sessions == 0:
            return {
                "status": "no_data",
                "message": "No sessions recorded yet"
            }
        
        success_rate = (
            self.system_metrics["successful_sessions"] / total_sessions * 100
        ) if total_sessions > 0 else 0
        
        # Agent performance breakdown
        agent_performance = {}
        for agent_name, stats in self.system_metrics["agent_performance"].items():
            agent_performance[agent_name] = {
                "total_executions": stats["total_executions"],
                "average_duration": round(stats["avg_duration"], 2),
                "timeout_rate": round(stats["timeouts"] / max(stats["total_executions"], 1) * 100, 2),
                "fallback_rate": round(stats["fallbacks"] / max(stats["total_executions"], 1) * 100, 2),
                "performance_grade": self._get_agent_grade(stats["avg_duration"])
            }
        
        return {
            "system_performance": {
                "total_sessions": total_sessions,
                "successful_sessions": self.system_metrics["successful_sessions"],
                "failed_sessions": self.system_metrics["failed_sessions"],
                "success_rate": round(success_rate, 2),
                "average_build_time": round(self.system_metrics["average_build_time"], 2),
                "slow_builds": self.system_metrics["slow_builds"],
                "fast_builds": self.system_metrics["fast_builds"]
            },
            "agent_performance": agent_performance,
            "recent_sessions": self._get_recent_sessions_summary(),
            "performance_alerts": self._get_performance_alerts(),
            "recommendations": self._get_performance_recommendations()
        }
    
    def _get_agent_grade(self, avg_duration: float) -> str:
        """Get performance grade for an agent."""
        if avg_duration < 10:
            return "A+"
        elif avg_duration < 20:
            return "A"
        elif avg_duration < 30:
            return "B+"
        elif avg_duration < 45:
            return "B"
        elif avg_duration < 60:
            return "C"
        else:
            return "D"
    
    def _get_recent_sessions_summary(self) -> List[Dict[str, Any]]:
        """Get summary of recent sessions."""
        recent = self.completed_sessions[-10:]  # Last 10 sessions
        return [
            {
                "session_id": s.session_id,
                "duration": round(s.total_duration, 2),
                "success": s.success,
                "agent_count": len(s.agent_metrics),
                "fallbacks": s.fallback_count,
                "errors": s.error_count
            }
            for s in recent
        ]
    
    def _get_performance_alerts(self) -> List[Dict[str, Any]]:
        """Get current performance alerts."""
        alerts = []
        
        # Check for slow agents
        for agent_name, stats in self.system_metrics["agent_performance"].items():
            if stats["avg_duration"] > 60:  # 1 minute
                alerts.append({
                    "type": "slow_agent",
                    "agent": agent_name,
                    "average_duration": round(stats["avg_duration"], 2),
                    "severity": "high" if stats["avg_duration"] > 120 else "medium"
                })
            
            if stats["timeouts"] / max(stats["total_executions"], 1) > 0.1:  # 10% timeout rate
                alerts.append({
                    "type": "high_timeout_rate",
                    "agent": agent_name,
                    "timeout_rate": round(stats["timeouts"] / max(stats["total_executions"], 1) * 100, 2),
                    "severity": "medium"
                })
        
        # Check overall system performance
        if self.system_metrics["total_sessions"] > 10:
            avg_build_time = self.system_metrics["average_build_time"]
            if avg_build_time > 120:  # 2 minutes
                alerts.append({
                    "type": "slow_system",
                    "average_build_time": round(avg_build_time, 2),
                    "severity": "high"
                })
            
            success_rate = (
                self.system_metrics["successful_sessions"] / self.system_metrics["total_sessions"] * 100
            )
            if success_rate < 80:  # 80% success rate
                alerts.append({
                    "type": "low_success_rate",
                    "success_rate": round(success_rate, 2),
                    "severity": "high"
                })
        
        return alerts
    
    def _get_performance_recommendations(self) -> List[str]:
        """Get performance improvement recommendations."""
        recommendations = []
        
        # Analyze agent performance
        for agent_name, stats in self.system_metrics["agent_performance"].items():
            if stats["avg_duration"] > 45:
                recommendations.append(f"Optimize {agent_name} agent - average execution time is {stats['avg_duration']:.1f}s")
            
            if stats["timeouts"] > 0:
                recommendations.append(f"Investigate {agent_name} timeouts - {stats['timeouts']} occurrences")
            
            if stats["fallbacks"] / max(stats["total_executions"], 1) > 0.2:  # 20% fallback rate
                recommendations.append(f"Reduce {agent_name} fallback usage - {stats['fallbacks']} occurrences")
        
        # System-wide recommendations
        if self.system_metrics["slow_builds"] > self.system_metrics["fast_builds"]:
            recommendations.append("Enable batch operations and caching to improve build speed")
        
        if self.system_metrics["failed_sessions"] > 0:
            recommendations.append("Review error handling and validation logic to reduce failures")
        
        return recommendations[:5]  # Limit to top 5 recommendations

# Global performance monitor instance
performance_monitor = PerformanceMonitor()

# Utility functions for easy access
def get_performance_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance."""
    return performance_monitor

def log_agent_performance(agent_name: str, duration: float, success: bool = True, **kwargs):
    """Log agent performance metrics."""
    monitor = get_performance_monitor()
    
    # Create a simple metric entry
    metric = {
        "agent": agent_name,
        "duration": duration,
        "success": success,
        "timestamp": datetime.utcnow().isoformat(),
        **kwargs
    }
    
    logger.info(f"Agent performance: {json.dumps(metric)}")

def get_system_performance_summary() -> Dict[str, Any]:
    """Get current system performance summary."""
    monitor = get_performance_monitor()
    return monitor.get_performance_report()