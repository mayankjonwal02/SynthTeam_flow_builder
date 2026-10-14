"""Optimized builder tools with batch operations for faster workflow building."""

from __future__ import annotations

import json
import time
import uuid
from typing import Any, Callable, Optional, List, Dict
from langchain_core.tools import tool

from app.multi_agent.tools import (
    COMPONENT_CATALOG, 
    HANDLE_COMPATIBILITY, 
    fill_config_defaults,
    validate_plan_edges
)

def create_optimized_builder_tools(
    graph_state: dict,
    ws_emitter: Optional[Callable] = None,
) -> list:
    """Return optimized LangChain tools with batch operations."""

    def _emit(event_type: str, data: dict):
        if ws_emitter:
            ws_emitter(event_type, data)

    @tool
    def create_node_batch(nodes_json: str) -> str:
        """Create multiple nodes in a single batch operation.
        
        Args:
            nodes_json: JSON array of node specifications.
                Each node should have: node_type, label, config, position_x, position_y
                
        Returns:
            JSON with created node IDs and any errors.
        """
        try:
            nodes = json.loads(nodes_json)
            if not isinstance(nodes, list):
                return json.dumps({"error": "Expected JSON array"})
        except json.JSONDecodeError:
            return json.dumps({"error": "Invalid JSON format"})
            
        results = []
        errors = []
        
        for i, node_spec in enumerate(nodes):
            try:
                node_type = node_spec.get("node_type")
                label = node_spec.get("label", node_type)
                config = node_spec.get("config", "{}")
                position_x = node_spec.get("position_x", 100 + i * 280)
                position_y = node_spec.get("position_y", 200)
                
                if node_type not in COMPONENT_CATALOG:
                    errors.append(f"Unknown node type: {node_type}")
                    continue
                    
                # Parse and validate config
                try:
                    cfg = json.loads(config) if isinstance(config, str) else config
                except json.JSONDecodeError:
                    cfg = {}
                    
                fill_config_defaults(node_type, cfg)
                
                # Generate unique ID
                node_id = str(uuid.uuid4())[:8]
                
                # Set special flags
                trigger_types = {"http_entry", "webhook_trigger", "cron_trigger", "manual_trigger"}
                if node_type in trigger_types:
                    cfg["is_entry"] = True
                if node_type == "response_builder":
                    cfg["is_response"] = True
                    
                cfg["label"] = label
                
                # Create node
                node = {
                    "id": node_id,
                    "type": node_type,
                    "position": {"x": position_x, "y": position_y},
                    "data": {"label": label, "component": node_type, "config": cfg},
                }
                
                graph_state["nodes"].append(node)
                _emit("node_added", node)
                results.append({"id": node_id, "type": node_type, "label": label})
                
            except Exception as e:
                errors.append(f"Node {i}: {str(e)}")
                
        return json.dumps({
            "created": len(results),
            "nodes": results,
            "errors": errors
        })

    @tool
    def create_edge_batch(edges_json: str) -> str:
        """Create multiple edges in a single batch operation.
        
        Args:
            edges_json: JSON array of edge specifications.
                Each edge should have: source_node_id, target_node_id, source_handle, target_handle
                
        Returns:
            JSON with created edge count and any errors.
        """
        try:
            edges = json.loads(edges_json)
            if not isinstance(edges, list):
                return json.dumps({"error": "Expected JSON array"})
        except json.JSONDecodeError:
            return json.dumps({"error": "Invalid JSON format"})
            
        node_ids = {n["id"] for n in graph_state["nodes"]}
        results = []
        errors = []
        
        for i, edge_spec in enumerate(edges):
            try:
                source_node_id = edge_spec.get("source_node_id")
                target_node_id = edge_spec.get("target_node_id")
                source_handle = edge_spec.get("source_handle", "output")
                target_handle = edge_spec.get("target_handle", "input")
                
                # Validate nodes exist
                if source_node_id not in node_ids:
                    errors.append(f"Source node '{source_node_id}' not found")
                    continue
                if target_node_id not in node_ids:
                    errors.append(f"Target node '{target_node_id}' not found")
                    continue
                    
                # Validate handle compatibility
                src_node = next(n for n in graph_state["nodes"] if n["id"] == source_node_id)
                tgt_node = next(n for n in graph_state["nodes"] if n["id"] == target_node_id)
                
                src_type = src_node["type"]
                tgt_type = tgt_node["type"]
                
                src_info = COMPONENT_CATALOG.get(src_type, {})
                tgt_info = COMPONENT_CATALOG.get(tgt_type, {})
                
                if source_handle not in src_info.get("source_handles", []):
                    errors.append(f"Source '{src_type}' has no handle '{source_handle}'")
                    continue
                if target_handle not in tgt_info.get("target_handles", []):
                    errors.append(f"Target '{tgt_type}' has no handle '{target_handle}'")
                    continue
                    
                compatible = HANDLE_COMPATIBILITY.get(source_handle, [])
                if target_handle not in compatible:
                    errors.append(f"Handle mismatch: '{source_handle}' -> '{target_handle}'")
                    continue
                    
                # Create edge
                edge_id = f"e-{source_node_id}-{target_node_id}"
                edge = {
                    "id": edge_id,
                    "source": source_node_id,
                    "target": target_node_id,
                    "sourceHandle": source_handle,
                    "targetHandle": target_handle,
                }
                
                graph_state["edges"].append(edge)
                _emit("edge_added", edge)
                results.append(edge_id)
                
            except Exception as e:
                errors.append(f"Edge {i}: {str(e)}")
                
        return json.dumps({
            "created": len(results),
            "edges": results,
            "errors": errors
        })

    @tool
    def validate_graph_fast() -> str:
        """Fast validation of the current graph structure.
        
        Returns:
            JSON with validation results and any critical issues.
        """
        issues = []
        warnings = []
        
        nodes = graph_state["nodes"]
        edges = graph_state["edges"]
        
        if not nodes:
            return json.dumps({"valid": False, "issues": ["No nodes in graph"], "warnings": []})
            
        node_ids = {n["id"] for n in nodes}
        node_types = {n["id"]: n["type"] for n in nodes}
        
        # Check for trigger node
        trigger_types = {"http_entry", "webhook_trigger", "cron_trigger", "manual_trigger"}
        has_trigger = any(node_types[nid] in trigger_types for nid in node_ids)
        if not has_trigger:
            issues.append("No trigger node found")
            
        # Check for response node
        has_response = any(node_types[nid] == "response_builder" for nid in node_ids)
        if not has_response and has_trigger:
            issues.append("No response_builder node found")
            
        # Check for orphaned nodes (fast check)
        connected = set()
        for edge in edges:
            connected.add(edge.get("source", ""))
            connected.add(edge.get("target", ""))
            
        orphans = node_ids - connected
        if orphans:
            # Only warn about non-trigger/orphan nodes
            non_critical_orphans = [oid for oid in orphans if node_types.get(oid) not in trigger_types and node_types.get(oid) != "response_builder"]
            if non_critical_orphans:
                warnings.append(f"Nodes not connected: {', '.join(non_critical_orphans[:3])}")
                
        # Fast edge validation
        for edge in edges:
            src = edge.get("source")
            tgt = edge.get("target")
            if src not in node_ids or tgt not in node_ids:
                issues.append(f"Edge references missing node")
                continue
                
        return json.dumps({
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "stats": {
                "nodes": len(nodes),
                "edges": len(edges),
                "connected_nodes": len(connected),
                "orphaned_nodes": len(orphans)
            }
        })

    @tool
    def get_graph_summary() -> str:
        """Get a quick summary of the current graph.
        
        Returns:
            JSON with graph statistics and structure overview.
        """
        nodes = graph_state["nodes"]
        edges = graph_state["edges"]
        
        node_counts = {}
        for node in nodes:
            node_type = node.get("type", "unknown")
            node_counts[node_type] = node_counts.get(node_type, 0) + 1
            
        edge_counts = {}
        for edge in edges:
            src_handle = edge.get("sourceHandle", "output")
            tgt_handle = edge.get("targetHandle", "input")
            connection_type = f"{src_handle}->{tgt_handle}"
            edge_counts[connection_type] = edge_counts.get(connection_type, 0) + 1
            
        return json.dumps({
            "summary": {
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "node_types": node_counts,
                "connection_types": edge_counts
            },
            "has_trigger": any(node.get("type") in ["http_entry", "webhook_trigger", "cron_trigger", "manual_trigger"] for node in nodes),
            "has_response": any(node.get("type") == "response_builder" for node in nodes)
        })

    # Return optimized tools
    return [
        create_node_batch,
        create_edge_batch,
        validate_graph_fast,
        get_graph_summary,
    ]

def create_optimized_planner_tools() -> list:
    """Optimized planner tools with caching and fast lookups."""
    # Import original tools and add optimizations
    from app.multi_agent.tools import (
        list_categories,
        get_components_by_category,
        get_component_details,
        get_compatible_targets,
        validate_connection,
        get_handle_info,
        get_workflow_pattern
    )
    
    # Add caching decorator for expensive operations
    def cache_result(ttl_seconds: int = 300):
        """Simple in-memory cache decorator."""
        cache = {}
        
        def decorator(func):
            def wrapper(*args, **kwargs):
                key = str(args) + str(kwargs)
                if key in cache:
                    result, timestamp = cache[key]
                    if time.time() - timestamp < ttl_seconds:
                        return result
                        
                result = func(*args, **kwargs)
                cache[key] = (result, time.time())
                return result
                
            return wrapper
        return decorator
    
    # Apply caching to expensive operations
    cached_get_components = cache_result()(get_components_by_category)
    cached_get_component_details = cache_result()(get_component_details)
    cached_get_compatible_targets = cache_result()(get_compatible_targets)
    
    return [
        list_categories,
        cached_get_components,
        cached_get_component_details,
        cached_get_compatible_targets,
        validate_connection,
        get_handle_info,
        get_workflow_pattern,
    ]