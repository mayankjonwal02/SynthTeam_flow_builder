"""Tools for the multi-agent workflow builder.

Three tool layers:
  1. **Discovery tools** — stateless catalog/handle/pattern queries (Planner, Reviewer)
  2. **Mutation tools**  — graph-state create/update/delete (Builder)
  3. **Inspection tools** — read-only graph queries and validation (Builder, Reviewer)

All stateful tools operate on a shared ``graph_state`` dict
``{"nodes": [], "edges": []}`` and optionally emit WebSocket events
via the ``ws_emitter`` callback.
"""

from __future__ import annotations

import json
import uuid
from collections import defaultdict
from typing import Any, Callable, Optional

from langchain_core.tools import tool

COMPONENT_CATALOG: dict[str, dict] = {
    "http_entry": {
        "description": "API endpoint entry point — defines method, path, and request/response schema",
        "category": "trigger",
        "fields": ["method", "path", "request_schema", "response_schema"],
        "source_handles": ["output"],
        "target_handles": [],
    },
    "webhook_trigger": {
        "description": "Receive external webhook payloads",
        "category": "trigger",
        "fields": [],
        "source_handles": ["output"],
        "target_handles": [],
    },
    "cron_trigger": {
        "description": "Time-based trigger using cron expressions",
        "category": "trigger",
        "fields": ["cron_expression"],
        "source_handles": ["output"],
        "target_handles": [],
    },
    "manual_trigger": {
        "description": "Manual test entry point",
        "category": "trigger",
        "fields": [],
        "source_handles": ["output"],
        "target_handles": [],
    },
    "processor": {
        "description": "Transform and relay data with field mappings",
        "category": "logic",
        "fields": ["field_mappings"],
        "source_handles": ["output"],
        "target_handles": ["input"],
    },
    "if_condition": {
        "description": "Branch execution into true/false paths based on a condition",
        "category": "logic",
        "fields": ["field", "operator", "value"],
        "source_handles": ["output"],
        "target_handles": ["input"],
    },
    "switch_case": {
        "description": "Multi-way branching based on a field's value",
        "category": "logic",
        "fields": ["field", "cases"],
        "source_handles": ["output"],
        "target_handles": ["input"],
    },
    "python_function": {
        "description": "Execute custom Python code",
        "category": "logic",
        "fields": ["code"],
        "source_handles": ["output"],
        "target_handles": ["input"],
    },
    "response_builder": {
        "description": "Build the API response (terminal node)",
        "category": "output",
        "fields": ["field_mappings", "response_schema"],
        "source_handles": [],
        "target_handles": ["input"],
    },
    "loop_foreach": {
        "description": "Iterate over an array, executing body nodes for each element",
        "category": "flow",
        "fields": ["array_field"],
        "source_handles": ["loop_out", "done"],
        "target_handles": ["in", "loop_back"],
    },
    "parallel_split": {
        "description": "Run downstream children concurrently",
        "category": "flow",
        "fields": [],
        "source_handles": ["output"],
        "target_handles": ["input"],
    },
    "merge_join": {
        "description": "Merge outputs from parallel branches",
        "category": "flow",
        "fields": [],
        "source_handles": ["output"],
        "target_handles": ["input"],
    },
    "delay": {
        "description": "Pause execution for N seconds",
        "category": "flow",
        "fields": ["seconds"],
        "source_handles": ["output"],
        "target_handles": ["input"],
    },
    "header_extractor": {
        "description": "Extract specific HTTP headers from the request",
        "category": "middleware",
        "fields": ["headers"],
        "source_handles": ["output"],
        "target_handles": ["input"],
    },
    "auth_node": {
        "description": "Validate API keys or auth tokens",
        "category": "middleware",
        "fields": [],
        "source_handles": ["output"],
        "target_handles": ["input"],
    },
    "llm_model": {
        "description": "Configure LLM provider and model (config node)",
        "category": "ai_config",
        "fields": ["provider", "model", "api_key", "temperature"],
        "source_handles": ["ai_model"],
        "target_handles": ["input"],
    },
    "embedding_model": {
        "description": "Configure embedding provider (config node)",
        "category": "ai_config",
        "fields": ["provider", "model", "api_key"],
        "source_handles": ["ai_embedding"],
        "target_handles": ["input"],
    },
    "vectorstore_config": {
        "description": "Configure vector DB connection (config node)",
        "category": "ai_config",
        "fields": ["provider", "collection", "url", "api_key"],
        "source_handles": ["ai_vectorstore"],
        "target_handles": ["input"],
    },
    "memory_config": {
        "description": "Configure agent memory backend (config node)",
        "category": "ai_config",
        "fields": ["backend", "session_id", "max_messages", "redis_url"],
        "source_handles": ["ai_memory"],
        "target_handles": ["input"],
    },
    "output_structure": {
        "description": "JSON schema for structured LLM output (config node)",
        "category": "ai_config",
        "fields": ["schema"],
        "source_handles": ["ai_structure"],
        "target_handles": ["input"],
    },
    "llm_call": {
        "description": "Invoke an LLM with system prompt and user prompt",
        "category": "ai_exec",
        "fields": ["system_prompt", "prompt_template"],
        "source_handles": ["output"],
        "target_handles": ["input", "ai_model", "ai_structure"],
    },
    "agent_run": {
        "description": "ReAct agent that reasons and uses tools iteratively",
        "category": "ai_exec",
        "fields": ["system_prompt", "prompt_template", "max_iterations"],
        "source_handles": ["output"],
        "target_handles": ["input", "ai_model", "ai_tool", "ai_memory", "ai_structure", "ai_embedding", "ai_vectorstore", "ai_subagent"],
    },
    "autonomous_agent": {
        "description": "Autonomous planning agent that creates and executes a step-by-step plan",
        "category": "ai_exec",
        "fields": ["system_prompt", "goal", "max_iterations"],
        "source_handles": ["output"],
        "target_handles": ["input", "ai_model", "ai_tool", "ai_memory", "ai_embedding", "ai_vectorstore", "ai_subagent"],
    },
    "retrieval": {
        "description": "RAG retrieval — embed query, search vector DB, return context",
        "category": "rag",
        "fields": ["top_k"],
        "source_handles": ["output"],
        "target_handles": ["input", "ai_embedding", "ai_vectorstore"],
    },
    "doc_loader": {
        "description": "Load text from URL, file, or raw text",
        "category": "rag",
        "fields": ["source_type", "text", "url", "file_path"],
        "source_handles": ["default"],
        "target_handles": ["input"],
    },
    "text_splitter": {
        "description": "Chunk documents for embedding",
        "category": "rag",
        "fields": ["strategy", "chunk_size", "overlap", "separator"],
        "source_handles": ["default"],
        "target_handles": ["input"],
    },
    "embedding_generate": {
        "description": "Generate text embeddings from chunks or text",
        "category": "rag",
        "fields": ["text_template"],
        "source_handles": ["output"],
        "target_handles": ["input", "ai_embedding"],
    },
    "vector_upsert": {
        "description": "Insert embeddings into a vector database",
        "category": "rag",
        "fields": [],
        "source_handles": ["output"],
        "target_handles": ["input", "ai_vectorstore"],
    },
    "vector_search": {
        "description": "Similarity search in a vector database",
        "category": "rag",
        "fields": ["top_k"],
        "source_handles": ["output"],
        "target_handles": ["input", "ai_vectorstore"],
    },
    "tool_web_search": {
        "description": "Web search tool for agents (Tavily)",
        "category": "ai_tool",
        "fields": ["api_key"],
        "source_handles": ["ai_tool"],
        "target_handles": ["input"],
    },
    "tool_http_request": {
        "description": "HTTP request tool for agents",
        "category": "ai_tool",
        "fields": ["allowed_methods", "timeout"],
        "source_handles": ["ai_tool"],
        "target_handles": ["input"],
    },
    "tool_calculator": {
        "description": "Math calculator tool for agents",
        "category": "ai_tool",
        "fields": [],
        "source_handles": ["ai_tool"],
        "target_handles": ["input"],
    },
    "tool_knowledge_base": {
        "description": "RAG knowledge base retrieval tool for agents",
        "category": "ai_tool",
        "fields": ["data_description", "collection", "top_k", "embedding_provider", "vectorstore_provider"],
        "source_handles": ["ai_tool"],
        "target_handles": ["input"],
    },
    "tool_gmail": {
        "description": "Gmail sending tool for agents",
        "category": "ai_tool",
        "fields": ["email", "app_password"],
        "source_handles": ["ai_tool"],
        "target_handles": ["input"],
    },
    "tool_code_executor": {
        "description": "Sandboxed Python code executor tool for agents",
        "category": "ai_tool",
        "fields": ["timeout"],
        "source_handles": ["ai_tool"],
        "target_handles": ["input"],
    },
    "tool_db_query": {
        "description": "Database query tool for agents",
        "category": "ai_tool",
        "fields": ["db_type", "connection_id"],
        "source_handles": ["ai_tool"],
        "target_handles": ["input"],
    },
    "tool_slack": {
        "description": "Slack webhook notifier tool for agents",
        "category": "ai_tool",
        "fields": ["webhook_url"],
        "source_handles": ["ai_tool"],
        "target_handles": ["input"],
    },
    "tool_email": {
        "description": "SMTP email sender tool for agents",
        "category": "ai_tool",
        "fields": ["smtp_host", "smtp_port", "username", "password", "from_email"],
        "source_handles": ["ai_tool"],
        "target_handles": ["input"],
    },
    "pg_find": {"description": "Query PostgreSQL rows", "category": "database", "fields": ["table", "filter", "columns", "limit"], "source_handles": ["output"], "target_handles": ["input"]},
    "pg_insert": {"description": "Insert into PostgreSQL", "category": "database", "fields": ["table", "data"], "source_handles": ["output"], "target_handles": ["input"]},
    "pg_update": {"description": "Update PostgreSQL rows", "category": "database", "fields": ["table", "filter", "data"], "source_handles": ["output"], "target_handles": ["input"]},
    "pg_delete": {"description": "Delete PostgreSQL rows", "category": "database", "fields": ["table", "filter"], "source_handles": ["output"], "target_handles": ["input"]},
    "pg_raw_query": {"description": "Raw SQL on PostgreSQL", "category": "database", "fields": ["query"], "source_handles": ["output"], "target_handles": ["input"]},
    "mongo_find": {"description": "Find MongoDB documents", "category": "database", "fields": ["collection", "filter"], "source_handles": ["output"], "target_handles": ["input"]},
    "mongo_insert": {"description": "Insert MongoDB document", "category": "database", "fields": ["collection", "document"], "source_handles": ["output"], "target_handles": ["input"]},
    "mongo_update": {"description": "Update MongoDB documents", "category": "database", "fields": ["collection", "filter", "update"], "source_handles": ["output"], "target_handles": ["input"]},
    "mongo_delete": {"description": "Delete MongoDB documents", "category": "database", "fields": ["collection", "filter"], "source_handles": ["output"], "target_handles": ["input"]},
    "vision_analyze": {"description": "Analyze images with AI vision models", "category": "ai_exec", "fields": ["image_url", "prompt"], "source_handles": ["output"], "target_handles": ["input", "ai_model"]},
    "speech_to_text": {"description": "Transcribe audio to text", "category": "ai_exec", "fields": ["provider", "audio_path"], "source_handles": ["output"], "target_handles": ["input", "ai_model"]},
    "text_to_speech": {"description": "Convert text to audio", "category": "ai_exec", "fields": ["provider", "voice", "text_template"], "source_handles": ["output"], "target_handles": ["input", "ai_model"]},
}

# ---------------------------------------------------------------------------
# Category metadata — describes each category's purpose and workflow role
# ---------------------------------------------------------------------------

CATEGORY_INFO: dict[str, dict] = {
    "trigger": {
        "description": "Entry points that start workflow execution",
        "role": "Every workflow must start with exactly one trigger node",
    },
    "logic": {
        "description": "Data transformation, branching, and custom code execution",
        "role": "Process, transform, and route data between nodes",
    },
    "output": {
        "description": "Terminal nodes that build and return the API response",
        "role": "Every API workflow must end with a response_builder node",
    },
    "flow": {
        "description": "Control flow: loops, parallel execution, merging, delays",
        "role": "Orchestrate complex execution patterns within workflows",
    },
    "middleware": {
        "description": "Request preprocessing: header extraction, authentication",
        "role": "Intercept and validate requests before main processing",
    },
    "ai_config": {
        "description": "Configuration nodes for AI models, embeddings, vectorstores, memory, and output structure",
        "role": "Provide config to ai_exec/rag nodes via typed handles (ai_model, ai_embedding, etc.)",
    },
    "ai_exec": {
        "description": "AI execution: LLM calls, ReAct agents, autonomous agents, vision, speech",
        "role": "Run AI inference; require ai_config nodes connected via typed handles",
    },
    "rag": {
        "description": "Retrieval-augmented generation pipeline components",
        "role": "Document loading, chunking, embedding generation, vector upsert/search, retrieval",
    },
    "ai_tool": {
        "description": "Tools that AI agents can use during execution (search, code, email, etc.)",
        "role": "Connect to agent_run or autonomous_agent via the ai_tool handle",
    },
    "database": {
        "description": "Database CRUD operations for PostgreSQL and MongoDB",
        "role": "Read and write data from/to databases within the pipeline",
    },
}

# ---------------------------------------------------------------------------
# Handle compatibility — which source handles may connect to which targets
# ---------------------------------------------------------------------------

HANDLE_COMPATIBILITY: dict[str, list[str]] = {
    "output": ["input", "in"],
    "default": ["input"],
    "ai_model": ["ai_model"],
    "ai_embedding": ["ai_embedding"],
    "ai_vectorstore": ["ai_vectorstore"],
    "ai_tool": ["ai_tool"],
    "ai_memory": ["ai_memory"],
    "ai_structure": ["ai_structure"],
    "ai_subagent": ["ai_subagent"],
    "loop_out": ["input"],
    "done": ["input"],
}

# ---------------------------------------------------------------------------
# Workflow pattern templates — common starting points the Planner can adapt
# ---------------------------------------------------------------------------

WORKFLOW_PATTERNS: dict[str, dict] = {
    "basic_api": {
        "description": "Simple REST API: receive request, process, respond",
        "nodes": [
            {"id": "n1", "type": "http_entry", "label": "API Entry", "config": {"method": "POST", "path": "/api/endpoint"}, "position": {"x": 100, "y": 200}},
            {"id": "n2", "type": "processor", "label": "Process Data", "config": {}, "position": {"x": 380, "y": 200}},
            {"id": "n3", "type": "response_builder", "label": "Response", "config": {}, "position": {"x": 660, "y": 200}},
        ],
        "edges": [
            {"source": "n1", "target": "n2", "sourceHandle": "output", "targetHandle": "input"},
            {"source": "n2", "target": "n3", "sourceHandle": "output", "targetHandle": "input"},
        ],
    },
    "authenticated_api": {
        "description": "API with header extraction and auth validation before processing",
        "nodes": [
            {"id": "n1", "type": "http_entry", "label": "API Entry", "config": {"method": "POST", "path": "/api/secure"}, "position": {"x": 100, "y": 200}},
            {"id": "n2", "type": "header_extractor", "label": "Extract Headers", "config": {}, "position": {"x": 380, "y": 200}},
            {"id": "n3", "type": "auth_node", "label": "Validate Auth", "config": {}, "position": {"x": 660, "y": 200}},
            {"id": "n4", "type": "processor", "label": "Process Data", "config": {}, "position": {"x": 940, "y": 200}},
            {"id": "n5", "type": "response_builder", "label": "Response", "config": {}, "position": {"x": 1220, "y": 200}},
        ],
        "edges": [
            {"source": "n1", "target": "n2", "sourceHandle": "output", "targetHandle": "input"},
            {"source": "n2", "target": "n3", "sourceHandle": "output", "targetHandle": "input"},
            {"source": "n3", "target": "n4", "sourceHandle": "output", "targetHandle": "input"},
            {"source": "n4", "target": "n5", "sourceHandle": "output", "targetHandle": "input"},
        ],
    },
    "chatbot_agent": {
        "description": "Conversational AI agent with tools and memory",
        "nodes": [
            {"id": "n1", "type": "http_entry", "label": "Chat Entry", "config": {"method": "POST", "path": "/api/chat"}, "position": {"x": 100, "y": 200}},
            {"id": "n2", "type": "llm_model", "label": "LLM Config", "config": {"provider": "openai", "model": "gpt-4o-mini"}, "position": {"x": 380, "y": 400}},
            {"id": "n3", "type": "memory_config", "label": "Memory", "config": {"backend": "in_memory"}, "position": {"x": 660, "y": 400}},
            {"id": "n4", "type": "agent_run", "label": "Chat Agent", "config": {"system_prompt": "You are a helpful assistant."}, "position": {"x": 660, "y": 200}},
            {"id": "n5", "type": "response_builder", "label": "Response", "config": {}, "position": {"x": 940, "y": 200}},
        ],
        "edges": [
            {"source": "n1", "target": "n4", "sourceHandle": "output", "targetHandle": "input"},
            {"source": "n2", "target": "n4", "sourceHandle": "ai_model", "targetHandle": "ai_model"},
            {"source": "n3", "target": "n4", "sourceHandle": "ai_memory", "targetHandle": "ai_memory"},
            {"source": "n4", "target": "n5", "sourceHandle": "output", "targetHandle": "input"},
        ],
    },
    "rag_ingest": {
        "description": "RAG ingestion pipeline: load docs, chunk, embed, store in vector DB",
        "nodes": [
            {"id": "n1", "type": "http_entry", "label": "Ingest Entry", "config": {"method": "POST", "path": "/api/ingest"}, "position": {"x": 100, "y": 200}},
            {"id": "n2", "type": "doc_loader", "label": "Load Document", "config": {}, "position": {"x": 380, "y": 200}},
            {"id": "n3", "type": "text_splitter", "label": "Chunk Text", "config": {"chunk_size": 500, "overlap": 50}, "position": {"x": 660, "y": 200}},
            {"id": "n4", "type": "embedding_model", "label": "Embedding Config", "config": {"provider": "openai"}, "position": {"x": 940, "y": 400}},
            {"id": "n5", "type": "embedding_generate", "label": "Generate Embeddings", "config": {}, "position": {"x": 940, "y": 200}},
            {"id": "n6", "type": "vectorstore_config", "label": "VectorDB Config", "config": {"provider": "chroma"}, "position": {"x": 1220, "y": 400}},
            {"id": "n7", "type": "vector_upsert", "label": "Store Embeddings", "config": {}, "position": {"x": 1220, "y": 200}},
            {"id": "n8", "type": "response_builder", "label": "Response", "config": {}, "position": {"x": 1500, "y": 200}},
        ],
        "edges": [
            {"source": "n1", "target": "n2", "sourceHandle": "output", "targetHandle": "input"},
            {"source": "n2", "target": "n3", "sourceHandle": "default", "targetHandle": "input"},
            {"source": "n3", "target": "n5", "sourceHandle": "default", "targetHandle": "input"},
            {"source": "n4", "target": "n5", "sourceHandle": "ai_embedding", "targetHandle": "ai_embedding"},
            {"source": "n5", "target": "n7", "sourceHandle": "output", "targetHandle": "input"},
            {"source": "n6", "target": "n7", "sourceHandle": "ai_vectorstore", "targetHandle": "ai_vectorstore"},
            {"source": "n7", "target": "n8", "sourceHandle": "output", "targetHandle": "input"},
        ],
    },
    "database_crud": {
        "description": "Simple database query API: receive request, query DB, respond",
        "nodes": [
            {"id": "n1", "type": "http_entry", "label": "API Entry", "config": {"method": "POST", "path": "/api/query"}, "position": {"x": 100, "y": 200}},
            {"id": "n2", "type": "pg_find", "label": "Query Database", "config": {}, "position": {"x": 380, "y": 200}},
            {"id": "n3", "type": "response_builder", "label": "Response", "config": {}, "position": {"x": 660, "y": 200}},
        ],
        "edges": [
            {"source": "n1", "target": "n2", "sourceHandle": "output", "targetHandle": "input"},
            {"source": "n2", "target": "n3", "sourceHandle": "output", "targetHandle": "input"},
        ],
    },
}

# ---------------------------------------------------------------------------
# Stateless discovery tools — no graph_state dependency
# ---------------------------------------------------------------------------


@tool
def list_categories() -> str:
    """List all available component categories with descriptions and roles.

    Returns:
        JSON with each category name, description, role, and component count.
    """
    result = {}
    for cat, info in CATEGORY_INFO.items():
        count = sum(1 for c in COMPONENT_CATALOG.values() if c["category"] == cat)
        result[cat] = {**info, "component_count": count}
    return json.dumps(result, indent=2)


@tool
def get_components_by_category(category: str) -> str:
    """Get all components belonging to a specific category with their full details.

    Args:
        category: Category name (e.g. 'trigger', 'ai_exec', 'database').

    Returns:
        JSON list of components with type, description, fields, source_handles,
        and target_handles. Returns an error if the category is unknown.
    """
    if category not in CATEGORY_INFO:
        available = ", ".join(sorted(CATEGORY_INFO.keys()))
        return f"Error: Unknown category '{category}'. Available: {available}"

    components = []
    for name, info in COMPONENT_CATALOG.items():
        if info["category"] == category:
            components.append({
                "type": name,
                "description": info["description"],
                "fields": info["fields"],
                "source_handles": info["source_handles"],
                "target_handles": info["target_handles"],
            })
    return json.dumps({"category": category, **CATEGORY_INFO[category], "components": components}, indent=2)


@tool
def get_component_details(component_type: str) -> str:
    """Get full details for a specific component type including fields and handles.

    Args:
        component_type: The component type name (e.g. 'llm_call', 'agent_run').

    Returns:
        JSON with type, category, description, fields, source_handles, target_handles.
    """
    info = COMPONENT_CATALOG.get(component_type)
    if not info:
        return f"Error: Unknown component '{component_type}'."
    return json.dumps({"type": component_type, **info}, indent=2)


@tool
def get_compatible_targets(source_component_type: str) -> str:
    """Given a source component, find which components and handles it can connect TO.

    For each source handle on the component, looks up compatible target handles
    and lists all components that accept those target handles.

    Args:
        source_component_type: The source component type name.

    Returns:
        JSON mapping each source handle to a list of compatible target components
        with the target handle to use.
    """
    info = COMPONENT_CATALOG.get(source_component_type)
    if not info:
        return f"Error: Unknown component '{source_component_type}'."

    result: dict[str, list] = {}
    for src_handle in info["source_handles"]:
        compatible_target_handles = HANDLE_COMPATIBILITY.get(src_handle, [])
        targets = []
        for comp_name, comp_info in COMPONENT_CATALOG.items():
            if comp_name == source_component_type:
                continue
            for tgt_handle in comp_info["target_handles"]:
                if tgt_handle in compatible_target_handles:
                    targets.append({
                        "component": comp_name,
                        "target_handle": tgt_handle,
                        "category": comp_info["category"],
                        "description": comp_info["description"],
                    })
        result[src_handle] = targets

    return json.dumps({
        "source_component": source_component_type,
        "source_handles": info["source_handles"],
        "connections": result,
    }, indent=2)


@tool
def validate_connection(
    source_type: str,
    source_handle: str,
    target_type: str,
    target_handle: str,
) -> str:
    """Validate whether a specific edge connection is valid.

    Checks that:
      1. Both component types exist
      2. The source component has the given source handle
      3. The target component has the given target handle
      4. The handle pair is compatible per the handle compatibility rules

    Args:
        source_type: Source component type name.
        source_handle: Handle ID on the source component.
        target_type: Target component type name.
        target_handle: Handle ID on the target component.

    Returns:
        JSON with {valid: bool, reason: str}.
    """
    src_info = COMPONENT_CATALOG.get(source_type)
    if not src_info:
        return json.dumps({"valid": False, "reason": f"Unknown source component '{source_type}'"})

    tgt_info = COMPONENT_CATALOG.get(target_type)
    if not tgt_info:
        return json.dumps({"valid": False, "reason": f"Unknown target component '{target_type}'"})

    if source_handle not in src_info["source_handles"]:
        return json.dumps({
            "valid": False,
            "reason": f"'{source_type}' does not have source handle '{source_handle}'. Available: {src_info['source_handles']}",
        })

    if target_handle not in tgt_info["target_handles"]:
        return json.dumps({
            "valid": False,
            "reason": f"'{target_type}' does not have target handle '{target_handle}'. Available: {tgt_info['target_handles']}",
        })

    compatible_targets = HANDLE_COMPATIBILITY.get(source_handle, [])
    if target_handle not in compatible_targets:
        return json.dumps({
            "valid": False,
            "reason": f"Handle mismatch: source '{source_handle}' can connect to {compatible_targets}, not '{target_handle}'",
        })

    return json.dumps({"valid": True, "reason": "Connection is valid"})


@tool
def get_handle_info(component_type: str) -> str:
    """Get detailed information about a component's handles and what they connect to.

    Explains what each source and target handle does, and which handle types
    are compatible.

    Args:
        component_type: The component type name.

    Returns:
        JSON with source_handles and target_handles, each with compatible
        connection info.
    """
    info = COMPONENT_CATALOG.get(component_type)
    if not info:
        return f"Error: Unknown component '{component_type}'."

    handle_descriptions = {
        "output": "Standard data output — connects to 'input' on downstream nodes",
        "default": "Default data output — connects to 'input' on downstream nodes",
        "input": "Standard data input — receives from 'output' or 'default' of upstream nodes",
        "in": "Loop body input — receives from 'loop_out' of a loop_foreach node",
        "ai_model": "LLM model configuration — connects ai_config to ai_exec nodes",
        "ai_embedding": "Embedding model configuration — connects to embedding/retrieval nodes",
        "ai_vectorstore": "Vector store configuration — connects to vector/retrieval nodes",
        "ai_tool": "Agent tool — connects tool nodes to agent_run/autonomous_agent",
        "ai_memory": "Memory configuration — connects to agent_run/autonomous_agent",
        "ai_structure": "Output structure schema — connects to llm_call/agent_run",
        "ai_subagent": "Sub-agent reference — connects to agent_run/autonomous_agent",
        "loop_out": "Loop body output — connects to nodes inside the loop body",
        "loop_back": "Loop feedback input — receives results from the last loop body node",
        "done": "Loop completion output — connects to nodes after the loop finishes",
    }

    source_details = []
    for h in info["source_handles"]:
        compatible = HANDLE_COMPATIBILITY.get(h, [])
        source_details.append({
            "handle": h,
            "description": handle_descriptions.get(h, "Data output"),
            "connects_to_target_handles": compatible,
        })

    target_details = []
    for h in info["target_handles"]:
        receives_from = [sh for sh, targets in HANDLE_COMPATIBILITY.items() if h in targets]
        target_details.append({
            "handle": h,
            "description": handle_descriptions.get(h, "Data input"),
            "receives_from_source_handles": receives_from,
        })

    return json.dumps({
        "component": component_type,
        "category": info["category"],
        "source_handles": source_details,
        "target_handles": target_details,
    }, indent=2)


@tool
def get_workflow_pattern(pattern_name: str) -> str:
    """Get a pre-built workflow pattern template as a starting point.

    Available patterns: basic_api, authenticated_api, chatbot_agent,
    rag_ingest, database_crud.

    Args:
        pattern_name: Name of the pattern (e.g. 'chatbot_agent').

    Returns:
        JSON with description, nodes, and edges for the pattern.
        Returns available patterns if the name is unknown.
    """
    pattern = WORKFLOW_PATTERNS.get(pattern_name)
    if not pattern:
        available = [
            {"name": k, "description": v["description"]}
            for k, v in WORKFLOW_PATTERNS.items()
        ]
        return json.dumps({"error": f"Unknown pattern '{pattern_name}'", "available_patterns": available}, indent=2)
    return json.dumps({"pattern": pattern_name, **pattern}, indent=2)


# ---------------------------------------------------------------------------
# Programmatic edge validation (used by orchestrator, not an LLM tool)
# ---------------------------------------------------------------------------

def validate_plan_edges(plan: dict) -> list[str]:
    """Validate all edges in a plan dict against HANDLE_COMPATIBILITY.

    Returns a list of issue strings (empty if all edges are valid).
    """
    issues: list[str] = []
    node_map = {n["id"]: n["type"] for n in plan.get("nodes", [])}

    for edge in plan.get("edges", []):
        src_id = edge.get("source", "")
        tgt_id = edge.get("target", "")
        src_handle = edge.get("sourceHandle", "output")
        tgt_handle = edge.get("targetHandle", "input")

        src_type = node_map.get(src_id)
        tgt_type = node_map.get(tgt_id)

        if not src_type:
            issues.append(f"Edge references unknown source node '{src_id}'")
            continue
        if not tgt_type:
            issues.append(f"Edge references unknown target node '{tgt_id}'")
            continue

        src_info = COMPONENT_CATALOG.get(src_type)
        tgt_info = COMPONENT_CATALOG.get(tgt_type)

        if not src_info:
            issues.append(f"Unknown source component type '{src_type}' on node '{src_id}'")
            continue
        if not tgt_info:
            issues.append(f"Unknown target component type '{tgt_type}' on node '{tgt_id}'")
            continue

        if src_handle not in src_info["source_handles"]:
            issues.append(
                f"Edge {src_id}->{tgt_id}: '{src_type}' has no source handle '{src_handle}' "
                f"(available: {src_info['source_handles']})"
            )

        if tgt_handle not in tgt_info["target_handles"]:
            issues.append(
                f"Edge {src_id}->{tgt_id}: '{tgt_type}' has no target handle '{tgt_handle}' "
                f"(available: {tgt_info['target_handles']})"
            )

        compatible = HANDLE_COMPATIBILITY.get(src_handle, [])
        if tgt_handle not in compatible:
            issues.append(
                f"Edge {src_id}->{tgt_id}: handle mismatch — source '{src_handle}' "
                f"cannot connect to target '{tgt_handle}' (compatible: {compatible})"
            )

    return issues


# All standalone discovery tools in one list for easy assembly
DISCOVERY_TOOLS = [
    list_categories,
    get_components_by_category,
    get_component_details,
    get_compatible_targets,
    validate_connection,
    get_handle_info,
    get_workflow_pattern,
]


def _auto_layout(nodes: list[dict]) -> list[dict]:
    """Assign basic left-to-right positions if positions are at origin."""
    for i, node in enumerate(nodes):
        pos = node.get("position", {})
        if pos.get("x", 0) == 0 and pos.get("y", 0) == 0:
            node["position"] = {"x": 200 + i * 280, "y": 100 + (i % 3) * 150}
    return nodes


def create_builder_tools(
    graph_state: dict,
    ws_emitter: Optional[Callable] = None,
):
    """Return a list of LangChain tools bound to the given graph_state dict."""

    def _emit(event_type: str, data: dict):
        if ws_emitter:
            ws_emitter(event_type, data)

    @tool
    def create_node(
        node_type: str,
        label: str,
        config: Optional[str] = None,
        position_x: int = 0,
        position_y: int = 0,
    ) -> str:
        """Create a new node in the workflow graph.

        Args:
            node_type: The component type (e.g. 'http_entry', 'llm_call', 'pg_find').
            label: Display label for the node.
            config: JSON string of config fields for the node. Defaults to empty.
            position_x: X coordinate on the canvas.
            position_y: Y coordinate on the canvas.

        Returns:
            The ID of the created node.
        """
        if node_type not in COMPONENT_CATALOG:
            return f"Error: Unknown component type '{node_type}'. Use list_available_components to see options."

        node_id = str(uuid.uuid4())[:8]
        cfg = {}
        if config:
            try:
                cfg = json.loads(config)
            except json.JSONDecodeError:
                cfg = {}

        cfg["label"] = label
        trigger_types = {"http_entry", "webhook_trigger", "cron_trigger", "manual_trigger"}
        if node_type in trigger_types:
            cfg["is_entry"] = True
        if node_type == "response_builder":
            cfg["is_response"] = True

        node = {
            "id": node_id,
            "type": node_type,
            "position": {"x": position_x, "y": position_y},
            "data": {"label": label, "component": node_type, "config": cfg},
        }
        graph_state["nodes"].append(node)
        _emit("node_added", node)
        return f"Created node '{label}' (id={node_id}, type={node_type})"

    @tool
    def create_edge(
        source_node_id: str,
        target_node_id: str,
        source_handle: str = "output",
        target_handle: str = "input",
    ) -> str:
        """Create an edge connecting two nodes.

        Args:
            source_node_id: ID of the source node.
            target_node_id: ID of the target node.
            source_handle: The source handle id (e.g. 'output', 'ai_model', 'ai_tool').
            target_handle: The target handle id (e.g. 'input', 'ai_model', 'ai_tool').

        Returns:
            Confirmation message.
        """
        node_ids = {n["id"] for n in graph_state["nodes"]}
        if source_node_id not in node_ids:
            return f"Error: Source node '{source_node_id}' not found."
        if target_node_id not in node_ids:
            return f"Error: Target node '{target_node_id}' not found."

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
        return f"Created edge {source_node_id} -> {target_node_id} ({source_handle} -> {target_handle})"

    @tool
    def update_node_config(node_id: str, config_json: str) -> str:
        """Update a node's config fields.

        Args:
            node_id: The node ID to update.
            config_json: JSON string with config fields to merge.

        Returns:
            Confirmation or error.
        """
        for node in graph_state["nodes"]:
            if node["id"] == node_id:
                try:
                    new_cfg = json.loads(config_json)
                except json.JSONDecodeError:
                    return "Error: Invalid JSON."
                node["data"]["config"].update(new_cfg)
                _emit("node_updated", {"id": node_id, "config": node["data"]["config"]})
                return f"Updated config for node {node_id}."
        return f"Error: Node '{node_id}' not found."

    @tool
    def delete_node(node_id: str) -> str:
        """Delete a node and all its connected edges.

        Args:
            node_id: The node ID to delete.

        Returns:
            Confirmation or error.
        """
        before = len(graph_state["nodes"])
        graph_state["nodes"] = [n for n in graph_state["nodes"] if n["id"] != node_id]
        if len(graph_state["nodes"]) == before:
            return f"Error: Node '{node_id}' not found."
        graph_state["edges"] = [
            e for e in graph_state["edges"]
            if e["source"] != node_id and e["target"] != node_id
        ]
        _emit("node_deleted", {"id": node_id})
        return f"Deleted node {node_id} and its edges."

    @tool
    def validate_graph() -> str:
        """Validate the current graph for structural issues.

        Checks: orphan nodes, missing trigger, missing response, invalid edge
        references, and handle compatibility on every edge.

        Returns:
            JSON with {valid: bool, issues: []}.
        """
        issues = []
        nodes = graph_state["nodes"]
        edges = graph_state["edges"]
        node_ids = {n["id"] for n in nodes}
        node_types = {n["id"]: n["type"] for n in nodes}

        has_trigger = any(
            node_types[nid] in ("http_entry", "webhook_trigger", "cron_trigger", "manual_trigger")
            for nid in node_ids
        )
        if not has_trigger:
            issues.append("No trigger node found. Add an HTTP Entry, Webhook, Cron, or Manual Trigger.")

        has_response = any(node_types[nid] == "response_builder" for nid in node_ids)
        if not has_response and has_trigger:
            issues.append("No Response node found. Add a Response node to return API output.")

        connected = set()
        for e in edges:
            connected.add(e["source"])
            connected.add(e["target"])
        orphans = node_ids - connected
        trigger_types = {"http_entry", "webhook_trigger", "cron_trigger", "manual_trigger"}
        for oid in orphans:
            if node_types.get(oid) not in trigger_types and node_types.get(oid) != "response_builder":
                issues.append(f"Node '{oid}' ({node_types.get(oid)}) is not connected to anything.")

        for e in edges:
            if e["source"] not in node_ids:
                issues.append(f"Edge references missing source node '{e['source']}'.")
                continue
            if e["target"] not in node_ids:
                issues.append(f"Edge references missing target node '{e['target']}'.")
                continue

            src_handle = e.get("sourceHandle", "output")
            tgt_handle = e.get("targetHandle", "input")
            compatible = HANDLE_COMPATIBILITY.get(src_handle, [])
            if tgt_handle not in compatible:
                issues.append(
                    f"Edge {e['source']}->{e['target']}: handle '{src_handle}' "
                    f"cannot connect to '{tgt_handle}' (compatible: {compatible})"
                )

        return json.dumps({"valid": len(issues) == 0, "issues": issues}, indent=2)

    @tool
    def get_current_graph() -> str:
        """Get the current state of the workflow graph as JSON.

        Returns:
            JSON with {nodes: [...], edges: [...]}.
        """
        return json.dumps({
            "nodes": graph_state["nodes"],
            "edges": graph_state["edges"],
        }, indent=2)

    return [
        create_node,
        create_edge,
        update_node_config,
        delete_node,
        validate_graph,
        get_current_graph,
        validate_connection,
    ]


# ---------------------------------------------------------------------------
# Tool factories for each agent role
# ---------------------------------------------------------------------------

def create_planner_tools() -> list:
    """Return discovery-only tools for the Planner agent."""
    return list(DISCOVERY_TOOLS)


def create_reviewer_tools(
    graph_state: dict,
    ws_emitter: Optional[Callable] = None,
) -> list:
    """Return inspection + discovery tools for the Reviewer agent."""
    all_builder = create_builder_tools(graph_state, ws_emitter)
    inspection = [t for t in all_builder if t.name in ("get_current_graph", "validate_graph")]
    return inspection + [get_component_details, validate_connection]
