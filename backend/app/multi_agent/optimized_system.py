"""Main integration for optimized multi-agent system."""

from __future__ import annotations

import asyncio
import logging
from typing import Optional, Callable, Dict, Any

from app.multi_agent.optimized_orchestrator import OptimizedMultiAgentOrchestrator
from app.multi_agent.optimized_agents import (
    create_optimized_requirement_agent,
    create_optimized_planner_agent,
    create_optimized_builder_agent,
    create_optimized_reviewer_agent,
    create_optimized_feedback_agent
)
from app.multi_agent.performance_monitor import (
    get_performance_monitor,
    log_agent_performance
)
from app.multi_agent.optimized_config import (
    get_agent_config,
    get_performance_threshold,
    get_cache_setting,
    get_batch_setting
)

logger = logging.getLogger("uvicorn.error")

class OptimizedMultiAgentSystem:
    """Main optimized multi-agent system with performance monitoring."""
    
    def __init__(self, llm, session_manager, session_id: str, ws_emitter: Optional[Callable] = None):
        self.llm = llm
        self.session_manager = session_manager
        self.session_id = session_id
        self.ws_emitter = ws_emitter
        self.performance_monitor = get_performance_monitor()
        self._orchestrator = None
        
    async def initialize(self):
        """Initialize the optimized orchestrator."""
        self._orchestrator = OptimizedMultiAgentOrchestrator(
            llm=self.llm,
            session_mgr=self.session_manager,
            session_id=self.session_id,
            ws_emitter=self.ws_emitter
        )
        
        # Start performance monitoring for this session
        self.performance_monitor.start_session(self.session_id)
        
        logger.info(f"Initialized optimized multi-agent system for session {self.session_id}")
        
    async def process_request(self, user_message: str, progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """Process a user request through the optimized pipeline."""
        
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Initialize if not already done
            if not self._orchestrator:
                await self.initialize()
            
            # Run the optimized pipeline
            await self._orchestrator.run_optimized(user_message, progress_callback)
            
            # Get session data
            session = await self.session_manager.get(self.session_id)
            if not session:
                raise ValueError(f"Session {self.session_id} not found")
            
            # Calculate performance metrics
            total_duration = asyncio.get_event_loop().time() - start_time
            
            # Get artifacts and metrics
            artifacts = session.get("artifacts", {})
            performance_metrics = artifacts.get("performance_metrics", {})
            
            # End performance monitoring
            success = session.get("status") in ["approved", "completed"]
            self.performance_monitor.end_session(self.session_id, success)
            
            # Log overall performance
            log_agent_performance(
                "total_pipeline",
                total_duration,
                success,
                session_id=self.session_id,
                status=session.get("status")
            )
            
            return {
                "session_id": self.session_id,
                "status": session.get("status", "unknown"),
                "total_duration": total_duration,
                "success": success,
                "artifacts": {
                    "spec": artifacts.get("spec"),
                    "plan": artifacts.get("plan"),
                    "graph": artifacts.get("graph"),
                    "review": artifacts.get("review")
                },
                "performance_metrics": performance_metrics,
                "optimization_enabled": True
            }
            
        except asyncio.TimeoutError:
            logger.error(f"Session {self.session_id} timed out")
            self.performance_monitor.end_session(self.session_id, False)
            raise
            
        except Exception as exc:
            logger.error(f"Session {self.session_id} failed: {exc}")
            self.performance_monitor.end_session(self.session_id, False)
            raise
            
    async def get_session_status(self) -> Dict[str, Any]:
        """Get current session status and metrics."""
        
        session = await self.session_manager.get(self.session_id)
        if not session:
            return {"error": "Session not found"}
        
        # Get performance metrics for this session
        session_metrics = self.performance_monitor.get_session_metrics(self.session_id)
        
        return {
            "session_id": self.session_id,
            "status": session.get("status", "unknown"),
            "created_at": session.get("created_at"),
            "last_updated": session.get("last_updated"),
            "conversation_length": len(session.get("conversation", [])),
            "artifacts_count": len(session.get("artifacts", {})),
            "performance": session_metrics.__dict__ if session_metrics else None
        }
    
    async def cancel_session(self):
        """Cancel the current session."""
        
        if self._orchestrator:
            # Cancel any running operations
            pass  # Implementation depends on your async cancellation strategy
            
        # Mark session as cancelled
        self.performance_monitor.end_session(self.session_id, False)
        
        logger.info(f"Cancelled session {self.session_id}")

# Factory function for easy creation
async def create_optimized_multi_agent_system(
    llm, 
    session_manager, 
    session_id: str, 
    ws_emitter: Optional[Callable] = None
) -> OptimizedMultiAgentSystem:
    """Factory function to create an optimized multi-agent system."""
    
    system = OptimizedMultiAgentSystem(
        llm=llm,
        session_manager=session_manager,
        session_id=session_id,
        ws_emitter=ws_emitter
    )
    
    await system.initialize()
    return system

# Convenience functions for the API
async def process_optimized_workflow_request(
    user_message: str,
    llm,
    session_manager,
    session_id: Optional[str] = None,
    ws_emitter: Optional[Callable] = None,
    progress_callback: Optional[Callable] = None
) -> Dict[str, Any]:
    """Process a workflow building request through the optimized system."""
    
    # Generate session ID if not provided
    if not session_id:
        session_id = await session_manager.create("optimized_user")
    
    # Create optimized system
    system = await create_optimized_multi_agent_system(
        llm=llm,
        session_manager=session_manager,
        session_id=session_id,
        ws_emitter=ws_emitter
    )
    
    # Process the request
    return await system.process_request(user_message, progress_callback)

def get_system_performance_report() -> Dict[str, Any]:
    """Get comprehensive system performance report."""
    
    monitor = get_performance_monitor()
    return monitor.get_performance_report()

def reset_performance_metrics():
    """Reset all performance metrics (use with caution)."""
    
    monitor = get_performance_monitor()
    # This would need to be implemented in the PerformanceMonitor class
    # For now, just log the attempt
    logger.warning("Performance metrics reset requested")

# Export main classes and functions
__all__ = [
    'OptimizedMultiAgentSystem',
    'create_optimized_multi_agent_system',
    'process_optimized_workflow_request',
    'get_system_performance_report',
    'get_performance_monitor',
    'log_agent_performance'
]