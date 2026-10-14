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

def _f(key, label, type_="text", **kw):
    """Shorthand for config_schema field descriptors."""
    d: dict[str, Any] = {"key": key, "type": type_, "label": label}
    d.update(kw)
    return d


def _fields_from_schema(schema: list[dict]) -> list[str]:
    """Extract flat field-key list from config_schema for backward compatibility."""
    return [f["key"] for f in schema]


COMPONENT_CATALOG: dict[str, dict] = {
    # ── TRIGGERS ──────────────────────────────────────────────────────
    "http_entry": {
        "description": "API endpoint entry point — defines method, path, and request/response schema",
        "category": "trigger",
        "config_schema": [
            _f("method", "HTTP Method", "select", options=["GET", "POST", "PUT", "DELETE", "PATCH"], default="POST", required=True),
            _f("path", "API Path", default="/api/endpoint", required=True, description="URL path for this endpoint, e.g. /api/users"),
            _f("request_schema", "Request Body Schema", "schema_builder", default={}, description="Define request body fields as {name: type} pairs. Types: string, int, float, bool, list, dict, json, date, datetime, uuid, email, url, any"),
            _f("response_schema", "Response Body Schema", "schema_builder", default={}, description="Define response body fields as {name: type} pairs"),
        ],
        "source_handles": ["output"],
        "target_handles": [],
    },
    "webhook_trigger": {
        "description": "Receive external webhook payloads",
        "category": "trigger",
        "config_schema": [
            _f("method", "HTTP Method", "select", options=["POST", "PUT"], default="POST"),
            _f("path", "Webhook Path", default="/webhook/endpoint"),
        ],
        "source_handles": ["output"],
        "target_handles": [],
    },
    "cron_trigger": {
        "description": "Time-based trigger using cron expressions",
        "category": "trigger",
        "config_schema": [
            _f("cron_expression", "Cron Expression", default="* * * * *", required=True, description="Standard cron syntax: minute hour day month weekday"),
        ],
        "source_handles": ["output"],
        "target_handles": [],
    },
    "manual_trigger": {
        "description": "Manual test entry point — no configuration needed",
        "category": "trigger",
        "config_schema": [],
        "source_handles": ["output"],
        "target_handles": [],
    },
    # ── LOGIC ─────────────────────────────────────────────────────────
    "processor": {
        "description": "Transform and relay data with field mappings. Without mappings acts as pass-through",
        "category": "logic",
        "config_schema": [
            _f("field_mappings", "Field Mappings", "field_mappings", default=[], description="List of {name, source, value} objects. source is 'static', 'input', or 'expression'. value is the literal, field key, or dot-path expression"),
        ],
        "source_handles": ["output"],
        "target_handles": ["input"],
    },
    "if_condition": {
        "description": "Branch execution into true/false paths based on a condition",
        "category": "logic",
        "config_schema": [
            _f("field", "Field to Evaluate", mode="field_mode", default_mode="expression", description="The data field to test, e.g. 'age' or 'input.user.role'"),
            _f("operator", "Operator", "select", options=["==", "!=", ">", "<", ">=", "<="], default="=="),
            _f("value", "Compare Value", mode="value_mode", default_mode="static", description="Value to compare the field against"),
        ],
        "source_handles": ["output"],
        "target_handles": ["input"],
    },
    "switch_case": {
        "description": "Multi-way branching based on a field's value",
        "category": "logic",
        "config_schema": [
            _f("field", "Switch Field", mode="field_mode", default_mode="expression", description="The field whose value determines the branch"),
            _f("cases", "Cases", "textarea", default="[]", description='JSON array of case values, e.g. ["admin","user","guest"]'),
        ],
        "source_handles": ["output"],
        "target_handles": ["input"],
    },
    "python_function": {
        "description": "Execute custom Python code. Receives merged upstream data as 'data' dict",
        "category": "logic",
        "config_schema": [
            _f("code", "Python Code", "code", default='# data = merged upstream inputs (dict)\n# return a dict\nreturn {"result": data}', required=True, description="Python code that receives 'data' dict and must return a dict"),
        ],
        "source_handles": ["output"],
        "target_handles": ["input"],
    },
    # ── OUTPUT ─────────────────────────────────────────────────────────
    "response_builder": {
        "description": "Build the API response (terminal node). Maps upstream data to response fields",
        "category": "output",
        "config_schema": [
            _f("response_schema", "Response Schema", "schema_builder", default={}, description="Define response fields as {name: type} pairs"),
            _f("field_mappings", "Field Mappings", "field_mappings", default=[], description="List of {name, type, source, value} to map upstream data into response fields. source: 'static', 'input', or 'expression'"),
        ],
        "source_handles": [],
        "target_handles": ["input"],
    },
    # ── FLOW CONTROL ──────────────────────────────────────────────────
    "loop_foreach": {
        "description": "Iterate over an array, executing body nodes for each element",
        "category": "flow",
        "config_schema": [
            _f("array_field", "Array Field", default="items", mode="array_field_mode", default_mode="expression", description="Dot-path to the array to iterate over"),
        ],
        "source_handles": ["loop_out", "done"],
        "target_handles": ["in", "loop_back"],
    },
    "parallel_split": {
        "description": "Run downstream children concurrently — no configuration needed",
        "category": "flow",
        "config_schema": [],
        "source_handles": ["output"],
        "target_handles": ["input"],
    },
    "merge_join": {
        "description": "Merge outputs from parallel branches — no configuration needed",
        "category": "flow",
        "config_schema": [],
        "source_handles": ["output"],
        "target_handles": ["input"],
    },
    "delay": {
        "description": "Pause execution for N seconds",
        "category": "flow",
        "config_schema": [
            _f("seconds", "Seconds", "number", default="1", mode="seconds_mode", default_mode="static", description="Number of seconds to pause"),
        ],
        "source_handles": ["output"],
        "target_handles": ["input"],
    },
    # ── MIDDLEWARE ─────────────────────────────────────────────────────
    "header_extractor": {
        "description": "Extract specific HTTP headers from the request and pass them downstream",
        "category": "middleware",
        "config_schema": [
            _f("headers", "Headers to Extract", "textarea", default="[]", description='JSON array of header names, e.g. ["authorization","x-request-id"]'),
        ],
        "source_handles": ["output"],
        "target_handles": ["input"],
    },
    "auth_node": {
        "description": "Validate API keys or auth tokens from request headers",
        "category": "middleware",
        "config_schema": [
            _f("type", "Auth Type", "select", options=["api_key", "bearer", "basic"], default="api_key"),
            _f("header_name", "Header Name", default="x-api-key", mode="header_name_mode", default_mode="static", description="Name of the header containing the auth credential"),
        ],
        "source_handles": ["output"],
        "target_handles": ["input"],
    },
    # ── AI CONFIG ─────────────────────────────────────────────────────
    "llm_model": {
        "description": "Configure LLM provider and model (config node). Connects to AI exec nodes via ai_model handle",
        "category": "ai_config",
        "config_schema": [
            _f("provider", "Provider", "select", options=["openai", "anthropic", "gemini", "ollama", "groq", "mistral"], default="openai", required=True),
            _f("model", "Model", default="gpt-4o-mini", required=True, description="Model name, e.g. gpt-4o-mini, claude-3-haiku, gemini-pro"),
            _f("api_key", "API Key", "password", secret=True, required=True, description="LLM provider API key — ASK THE USER"),
            _f("temperature", "Temperature", "number", default="0.7", description="Sampling temperature 0.0-2.0"),
            _f("base_url", "Base URL", description="Custom API endpoint URL (optional, for self-hosted models)"),
        ],
        "source_handles": ["ai_model"],
        "target_handles": ["input"],
    },
    "embedding_model": {
        "description": "Configure embedding provider (config node). Connects via ai_embedding handle",
        "category": "ai_config",
        "config_schema": [
            _f("provider", "Provider", "select", options=["openai", "ollama", "huggingface"], default="openai", required=True),
            _f("model", "Model", description="Embedding model name (leave blank for provider default)"),
            _f("api_key", "API Key", "password", secret=True, required=True, description="Embedding provider API key — ASK THE USER"),
        ],
        "source_handles": ["ai_embedding"],
        "target_handles": ["input"],
    },
    "vectorstore_config": {
        "description": "Configure vector DB connection (config node). Connects via ai_vectorstore handle",
        "category": "ai_config",
        "config_schema": [
            _f("provider", "Provider", "select", options=["qdrant", "chroma", "pinecone", "weaviate"], default="qdrant", required=True),
            _f("collection", "Collection", default="default", required=True, description="Collection/index name in the vector DB"),
            _f("url", "URL", description="Vector DB endpoint URL"),
            _f("api_key", "API Key", "password", secret=True, description="Vector DB API key — ASK THE USER if required"),
        ],
        "source_handles": ["ai_vectorstore"],
        "target_handles": ["input"],
    },
    "memory_config": {
        "description": "Configure agent memory backend (config node). Connects via ai_memory handle",
        "category": "ai_config",
        "config_schema": [
            _f("backend", "Backend", "select", options=["in_memory", "redis"], default="in_memory", required=True),
            _f("session_id", "Session ID", default="default", description="Key to isolate memory per conversation"),
            _f("max_messages", "Max Messages", "number", default="200", description="Maximum messages to retain"),
            _f("redis_url", "Redis URL", description="Redis connection URL (only for redis backend)"),
        ],
        "source_handles": ["ai_memory"],
        "target_handles": ["input"],
    },
    "output_structure": {
        "description": "JSON schema for structured LLM output (config node). Connects via ai_structure handle",
        "category": "ai_config",
        "config_schema": [
            _f("schema", "JSON Schema", "textarea", default="", description='JSON schema defining the structured output format, e.g. {"name": "string", "age": "int"}'),
        ],
        "source_handles": ["ai_structure"],
        "target_handles": ["input"],
    },
    # ── AI EXECUTION ──────────────────────────────────────────────────
    "llm_call": {
        "description": "Invoke an LLM with system prompt and user prompt. Requires llm_model connected via ai_model handle",
        "category": "ai_exec",
        "config_schema": [
            _f("system_prompt", "System Prompt", "textarea", mode="system_prompt_source", default_mode="static", description="System instructions for the LLM"),
            _f("prompt_template", "User Prompt", "textarea", default="{{input}}", mode="prompt_template_source", default_mode="static", description="User message template. Use {{input}} to inject upstream data"),
        ],
        "source_handles": ["output"],
        "target_handles": ["input", "ai_model", "ai_structure"],
    },
    "agent_run": {
        "description": "ReAct agent that reasons and uses tools iteratively. Connect llm_model, tools, and optionally memory",
        "category": "ai_exec",
        "config_schema": [
            _f("system_prompt", "System Prompt", "textarea", mode="system_prompt_source", default_mode="static", description="System instructions for the agent"),
            _f("prompt_template", "Prompt / Goal", "textarea", default="{{input}}", mode="prompt_template_source", default_mode="static", description="User message or goal. Use {{input}} for upstream data"),
            _f("max_iterations", "Max Iterations", "number", default="10", description="Maximum reasoning/tool-call loops"),
        ],
        "source_handles": ["output"],
        "target_handles": ["input", "ai_model", "ai_tool", "ai_memory", "ai_structure", "ai_embedding", "ai_vectorstore", "ai_subagent"],
    },
    "autonomous_agent": {
        "description": "Autonomous planning agent that creates and executes a step-by-step plan",
        "category": "ai_exec",
        "config_schema": [
            _f("system_prompt", "System Prompt", "textarea", mode="system_prompt_source", default_mode="static", description="System instructions for the autonomous agent"),
            _f("goal", "Goal", "textarea", default="{{input}}", mode="goal_source", default_mode="static", description="The goal for the agent to achieve. Use {{input}} for upstream data"),
            _f("max_iterations", "Max Iterations", "number", default="10", description="Maximum planning/execution steps"),
        ],
        "source_handles": ["output"],
        "target_handles": ["input", "ai_model", "ai_tool", "ai_memory", "ai_embedding", "ai_vectorstore", "ai_subagent"],
    },
    "vision_analyze": {
        "description": "Analyze images with AI vision models. Requires llm_model connected via ai_model handle",
        "category": "ai_exec",
        "config_schema": [
            _f("image_url", "Image URL", description="URL of the image to analyze"),
            _f("prompt", "Analysis Prompt", "textarea", default="Describe this image.", description="Instructions for the vision model"),
        ],
        "source_handles": ["output"],
        "target_handles": ["input", "ai_model"],
    },
    "speech_to_text": {
        "description": "Transcribe audio to text",
        "category": "ai_exec",
        "config_schema": [
            _f("provider", "Provider", "select", options=["openai_whisper"], default="openai_whisper"),
            _f("audio_path", "Audio Path", description="Path or URL to the audio file"),
        ],
        "source_handles": ["output"],
        "target_handles": ["input", "ai_model"],
    },
    "text_to_speech": {
        "description": "Convert text to audio",
        "category": "ai_exec",
        "config_schema": [
            _f("provider", "Provider", "select", options=["openai"], default="openai"),
            _f("voice", "Voice", "select", options=["alloy", "echo", "fable", "onyx", "nova", "shimmer"], default="alloy"),
            _f("text_template", "Text Template", default="{{input}}", description="Text to convert. Use {{input}} for upstream data"),
        ],
        "source_handles": ["output"],
        "target_handles": ["input", "ai_model"],
    },
    # ── RAG PIPELINE ──────────────────────────────────────────────────
    "doc_loader": {
        "description": "Load text from URL, file, or raw text input",
        "category": "rag",
        "config_schema": [
            _f("source_type", "Source Type", "select", options=["text", "url", "file"], default="text", required=True),
            _f("text", "Raw Text", "textarea", description="Raw text content (when source_type is 'text')"),
            _f("url", "URL", description="Document URL (when source_type is 'url')"),
            _f("file_path", "File Path", description="File path (when source_type is 'file')"),
        ],
        "source_handles": ["default"],
        "target_handles": ["input"],
    },
    "text_splitter": {
        "description": "Chunk documents into smaller pieces for embedding",
        "category": "rag",
        "config_schema": [
            _f("strategy", "Strategy", "select", options=["character", "recursive"], default="character"),
            _f("chunk_size", "Chunk Size", "number", default="1000", description="Maximum characters per chunk"),
            _f("overlap", "Overlap", "number", default="200", description="Character overlap between chunks"),
            _f("separator", "Separator", default="\\n\\n", description="Text separator for splitting"),
        ],
        "source_handles": ["default"],
        "target_handles": ["input"],
    },
    "embedding_generate": {
        "description": "Generate text embeddings from chunks or text. Requires embedding_model via ai_embedding handle",
        "category": "rag",
        "config_schema": [
            _f("text_template", "Text Template", default="{{input}}", description="Template for text to embed. Use {{input}} for upstream data"),
        ],
        "source_handles": ["output"],
        "target_handles": ["input", "ai_embedding"],
    },
    "vector_upsert": {
        "description": "Insert embeddings into a vector database. Requires vectorstore_config via ai_vectorstore handle",
        "category": "rag",
        "config_schema": [],
        "source_handles": ["output"],
        "target_handles": ["input", "ai_vectorstore"],
    },
    "vector_search": {
        "description": "Similarity search in a vector database. Requires vectorstore_config via ai_vectorstore handle",
        "category": "rag",
        "config_schema": [
            _f("top_k", "Top K Results", "number", default="5", description="Number of similar results to return"),
        ],
        "source_handles": ["output"],
        "target_handles": ["input", "ai_vectorstore"],
    },
    "retrieval": {
        "description": "RAG retrieval — embed query, search vector DB, return context. Requires embedding_model + vectorstore_config",
        "category": "rag",
        "config_schema": [
            _f("top_k", "Top K Results", "number", default="5", description="Number of context chunks to retrieve"),
        ],
        "source_handles": ["output"],
        "target_handles": ["input", "ai_embedding", "ai_vectorstore"],
    },
    # ── AI TOOLS ──────────────────────────────────────────────────────
    "tool_web_search": {
        "description": "Web search tool for agents (Tavily). Connect to agent_run via ai_tool handle",
        "category": "ai_tool",
        "config_schema": [
            _f("api_key", "Tavily API Key", "password", secret=True, required=True, description="Tavily API key — ASK THE USER"),
            _f("max_results", "Max Results", "number", default="5"),
        ],
        "source_handles": ["ai_tool"],
        "target_handles": ["input"],
    },
    "tool_http_request": {
        "description": "HTTP request tool for agents. Connect to agent_run via ai_tool handle",
        "category": "ai_tool",
        "config_schema": [
            _f("allowed_methods", "Allowed Methods", default="GET,POST", description="Comma-separated HTTP methods the agent can use"),
            _f("timeout", "Timeout (seconds)", "number", default="30"),
        ],
        "source_handles": ["ai_tool"],
        "target_handles": ["input"],
    },
    "tool_calculator": {
        "description": "Math calculator tool for agents — no configuration needed",
        "category": "ai_tool",
        "config_schema": [],
        "source_handles": ["ai_tool"],
        "target_handles": ["input"],
    },
    "tool_knowledge_base": {
        "description": "RAG knowledge base retrieval tool for agents",
        "category": "ai_tool",
        "config_schema": [
            _f("data_description", "Data Description", "textarea", description="Describe what data the knowledge base contains (helps the agent decide when to use it)"),
            _f("collection", "Collection", default="default"),
            _f("top_k", "Top K", "number", default="5"),
            _f("embedding_provider", "Embedding Provider", "select", options=["openai", "ollama", "huggingface"], default="openai"),
            _f("vectorstore_provider", "VectorStore Provider", "select", options=["qdrant", "chroma", "pinecone"], default="qdrant"),
        ],
        "source_handles": ["ai_tool"],
        "target_handles": ["input"],
    },
    "tool_gmail": {
        "description": "Gmail sending tool for agents. Connect to agent_run via ai_tool handle",
        "category": "ai_tool",
        "config_schema": [
            _f("email", "Gmail Address", required=True, description="The Gmail address to send from"),
            _f("app_password", "App Password", "password", secret=True, required=True, description="Gmail app password — ASK THE USER"),
        ],
        "source_handles": ["ai_tool"],
        "target_handles": ["input"],
    },
    "tool_code_executor": {
        "description": "Sandboxed Python code executor tool for agents",
        "category": "ai_tool",
        "config_schema": [
            _f("timeout", "Timeout (seconds)", "number", default="10"),
        ],
        "source_handles": ["ai_tool"],
        "target_handles": ["input"],
    },
    "tool_db_query": {
        "description": "Database query tool for agents",
        "category": "ai_tool",
        "config_schema": [
            _f("db_type", "Database Type", "select", options=["postgres", "mysql", "sqlite", "mongo"], default="postgres"),
            _f("connection_id", "Connection ID", required=True, description="ID of a saved database connection"),
        ],
        "source_handles": ["ai_tool"],
        "target_handles": ["input"],
    },
    "tool_slack": {
        "description": "Slack webhook notifier tool for agents",
        "category": "ai_tool",
        "config_schema": [
            _f("webhook_url", "Webhook URL", secret=True, required=True, description="Slack incoming webhook URL — ASK THE USER"),
        ],
        "source_handles": ["ai_tool"],
        "target_handles": ["input"],
    },
    "tool_email": {
        "description": "SMTP email sender tool for agents",
        "category": "ai_tool",
        "config_schema": [
            _f("smtp_host", "SMTP Host", required=True, description="SMTP server hostname"),
            _f("smtp_port", "SMTP Port", "number", default="587"),
            _f("username", "Username", required=True),
            _f("password", "Password", "password", secret=True, required=True, description="SMTP password — ASK THE USER"),
            _f("from_email", "From Email", required=True, description="Sender email address"),
        ],
        "source_handles": ["ai_tool"],
        "target_handles": ["input"],
    },
    "tool_file_ops": {
        "description": "File read/write tool for agents",
        "category": "ai_tool",
        "config_schema": [
            _f("mode", "Mode", "select", options=["read", "write"], default="read"),
            _f("base_path", "Base Path", default="/tmp", description="Root directory for file operations"),
        ],
        "source_handles": ["ai_tool"],
        "target_handles": ["input"],
    },
    "tool_workflow": {
        "description": "Invoke other deployed workflows as a tool",
        "category": "ai_tool",
        "config_schema": [
            _f("workflow_url", "Workflow URL", required=True, description="URL of the deployed workflow to call"),
            _f("method", "Method", "select", options=["POST", "GET"], default="POST"),
        ],
        "source_handles": ["ai_tool"],
        "target_handles": ["input"],
    },
    "tool_composio": {
        "description": "Composio actions integration tool for agents",
        "category": "ai_tool",
        "config_schema": [
            _f("api_key", "Composio API Key", "password", secret=True, required=True, description="Composio API key — ASK THE USER"),
            _f("action", "Action", required=True, description="Composio action name to execute"),
        ],
        "source_handles": ["ai_tool"],
        "target_handles": ["input"],
    },
    # ── DATABASE ──────────────────────────────────────────────────────
    "pg_find": {
        "description": "Query PostgreSQL rows",
        "category": "database",
        "config_schema": [
            _f("connection_id", "Connection ID", required=True, description="Saved PostgreSQL connection ID"),
            _f("table", "Table", required=True),
            _f("filter_mappings", "Filters", "field_mappings", default=[], description="Filter conditions as {name, source, value} mappings"),
        ],
        "source_handles": ["output"],
        "target_handles": ["input"],
    },
    "pg_insert": {
        "description": "Insert into PostgreSQL",
        "category": "database",
        "config_schema": [
            _f("connection_id", "Connection ID", required=True),
            _f("table", "Table", required=True),
        ],
        "source_handles": ["output"],
        "target_handles": ["input"],
    },
    "pg_update": {
        "description": "Update PostgreSQL rows",
        "category": "database",
        "config_schema": [
            _f("connection_id", "Connection ID", required=True),
            _f("table", "Table", required=True),
            _f("filter_mappings", "Filters", "field_mappings", default=[], description="Filter conditions to match rows"),
        ],
        "source_handles": ["output"],
        "target_handles": ["input"],
    },
    "pg_delete": {
        "description": "Delete PostgreSQL rows",
        "category": "database",
        "config_schema": [
            _f("connection_id", "Connection ID", required=True),
            _f("table", "Table", required=True),
            _f("filter_mappings", "Filters", "field_mappings", default=[], description="Filter conditions to match rows for deletion"),
        ],
        "source_handles": ["output"],
        "target_handles": ["input"],
    },
    "pg_raw_query": {
        "description": "Run raw SQL on PostgreSQL",
        "category": "database",
        "config_schema": [
            _f("connection_id", "Connection ID", required=True),
            _f("query", "SQL Query", "textarea", required=True, description="Raw SQL query to execute"),
        ],
        "source_handles": ["output"],
        "target_handles": ["input"],
    },
    "mongo_find": {
        "description": "Find MongoDB documents",
        "category": "database",
        "config_schema": [
            _f("connection_id", "Connection ID", required=True, description="Saved MongoDB connection ID"),
            _f("database", "Database", required=True),
            _f("collection", "Collection", required=True),
            _f("filter_mappings", "Filters", "field_mappings", default=[], description="Query filter conditions"),
        ],
        "source_handles": ["output"],
        "target_handles": ["input"],
    },
    "mongo_insert": {
        "description": "Insert MongoDB document",
        "category": "database",
        "config_schema": [
            _f("connection_id", "Connection ID", required=True),
            _f("database", "Database", required=True),
            _f("collection", "Collection", required=True),
        ],
        "source_handles": ["output"],
        "target_handles": ["input"],
    },
    "mongo_update": {
        "description": "Update MongoDB documents",
        "category": "database",
        "config_schema": [
            _f("connection_id", "Connection ID", required=True),
            _f("database", "Database", required=True),
            _f("collection", "Collection", required=True),
            _f("filter_mappings", "Filters", "field_mappings", default=[], description="Query filter conditions"),
        ],
        "source_handles": ["output"],
        "target_handles": ["input"],
    },
    "mongo_delete": {
        "description": "Delete MongoDB documents",
        "category": "database",
        "config_schema": [
            _f("connection_id", "Connection ID", required=True),
            _f("database", "Database", required=True),
            _f("collection", "Collection", required=True),
            _f("filter_mappings", "Filters", "field_mappings", default=[], description="Query filter conditions"),
        ],
        "source_handles": ["output"],
        "target_handles": ["input"],
    },
}

# Compute backward-compatible "fields" list from config_schema
for _comp_info in COMPONENT_CATALOG.values():
    _comp_info["fields"] = _fields_from_schema(_comp_info.get("config_schema", []))


def fill_config_defaults(node_type: str, config: dict) -> dict:
    """Fill missing config fields with defaults from config_schema, including mode keys.

    Ensures every field that has a default gets populated, and every field with
    a mode key (static/input/expression) gets its mode set to the default_mode.
    Mutates and returns the config dict.
    """
    comp = COMPONENT_CATALOG.get(node_type)
    if not comp:
        return config
    for field_def in comp.get("config_schema", []):
        key = field_def["key"]
        if key not in config and "default" in field_def:
            config[key] = field_def["default"]
        mode_key = field_def.get("mode")
        if mode_key and mode_key not in config:
            config[mode_key] = field_def.get("default_mode", "static")
    return config


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
# Required connections — which target_handles must have an edge from a config node
# ---------------------------------------------------------------------------

# Config handle -> component types that have that source_handle (satisfiers)
_CONFIG_HANDLE_SATISFIERS: dict[str, list[str]] = {}
for _comp_name, _comp_info in COMPONENT_CATALOG.items():
    for _sh in _comp_info.get("source_handles", []):
        if _sh in ("ai_model", "ai_embedding", "ai_vectorstore", "ai_tool", "ai_memory", "ai_structure", "ai_subagent"):
            _CONFIG_HANDLE_SATISFIERS.setdefault(_sh, []).append(_comp_name)

# Per component type: which config target_handles are required (True) or optional (False)
REQUIRED_CONNECTIONS: dict[str, list[dict]] = {}
for _comp_name, _comp_info in COMPONENT_CATALOG.items():
    target_handles = _comp_info.get("target_handles", [])
    entries = []
    for _th in target_handles:
        if _th in ("input", "in", "loop_back"):
            continue
        if _th not in _CONFIG_HANDLE_SATISFIERS:
            continue
        satisfied_by = _CONFIG_HANDLE_SATISFIERS[_th]
        required = True
        if _comp_name in ("llm_call", "vision_analyze", "speech_to_text", "text_to_speech"):
            required = _th == "ai_model"
        elif _comp_name in ("agent_run", "autonomous_agent"):
            required = _th == "ai_model"
        elif _comp_name in ("embedding_generate",):
            required = _th == "ai_embedding"
        elif _comp_name in ("vector_upsert", "vector_search"):
            required = _th == "ai_vectorstore"
        elif _comp_name == "retrieval":
            required = _th in ("ai_embedding", "ai_vectorstore")
        elif _th == "ai_structure":
            required = False
        elif _th in ("ai_tool", "ai_memory", "ai_subagent"):
            required = False
        entries.append({
            "target_handle": _th,
            "required": required,
            "satisfied_by_component_types": satisfied_by,
        })
    if entries:
        REQUIRED_CONNECTIONS[_comp_name] = entries

# ---------------------------------------------------------------------------
# Workflow pattern templates — common starting points the Planner can adapt
# ---------------------------------------------------------------------------

WORKFLOW_PATTERNS: dict[str, dict] = {
    "basic_api": {
        "description": "Simple REST API: receive request, process, respond",
        "nodes": [
            {"id": "n1", "type": "http_entry", "label": "API Entry", "config": {"method": "POST", "path": "/api/endpoint", "request_schema": {}, "response_schema": {}}, "position": {"x": 100, "y": 200}},
            {"id": "n2", "type": "processor", "label": "Process Data", "config": {"field_mappings": []}, "position": {"x": 380, "y": 200}},
            {"id": "n3", "type": "response_builder", "label": "Response", "config": {"response_schema": {}, "field_mappings": []}, "position": {"x": 660, "y": 200}},
        ],
        "edges": [
            {"source": "n1", "target": "n2", "sourceHandle": "output", "targetHandle": "input"},
            {"source": "n2", "target": "n3", "sourceHandle": "output", "targetHandle": "input"},
        ],
    },
    "authenticated_api": {
        "description": "API with header extraction and auth validation before processing",
        "nodes": [
            {"id": "n1", "type": "http_entry", "label": "API Entry", "config": {"method": "POST", "path": "/api/secure", "request_schema": {}, "response_schema": {}}, "position": {"x": 100, "y": 200}},
            {"id": "n2", "type": "header_extractor", "label": "Extract Headers", "config": {"headers": '["authorization"]'}, "position": {"x": 380, "y": 200}},
            {"id": "n3", "type": "auth_node", "label": "Validate Auth", "config": {"type": "api_key", "header_name": "x-api-key", "header_name_mode": "static"}, "position": {"x": 660, "y": 200}},
            {"id": "n4", "type": "processor", "label": "Process Data", "config": {"field_mappings": []}, "position": {"x": 940, "y": 200}},
            {"id": "n5", "type": "response_builder", "label": "Response", "config": {"response_schema": {}, "field_mappings": []}, "position": {"x": 1220, "y": 200}},
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
            {"id": "n1", "type": "http_entry", "label": "Chat Entry", "config": {"method": "POST", "path": "/api/chat", "request_schema": {"message": "string"}, "response_schema": {"reply": "string"}}, "position": {"x": 100, "y": 200}},
            {"id": "n2", "type": "llm_model", "label": "LLM Config", "config": {"provider": "openai", "model": "gpt-4o-mini", "api_key": "__ASK_USER__", "temperature": "0.7"}, "position": {"x": 380, "y": 400}},
            {"id": "n3", "type": "memory_config", "label": "Memory", "config": {"backend": "in_memory", "session_id": "default", "max_messages": "200"}, "position": {"x": 660, "y": 400}},
            {"id": "n4", "type": "agent_run", "label": "Chat Agent", "config": {"system_prompt": "You are a helpful assistant.", "system_prompt_source": "static", "prompt_template": "{{input}}", "prompt_template_source": "static", "max_iterations": "10"}, "position": {"x": 660, "y": 200}},
            {"id": "n5", "type": "response_builder", "label": "Response", "config": {"response_schema": {}, "field_mappings": []}, "position": {"x": 940, "y": 200}},
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
            {"id": "n1", "type": "http_entry", "label": "Ingest Entry", "config": {"method": "POST", "path": "/api/ingest", "request_schema": {"text": "string"}, "response_schema": {"status": "string"}}, "position": {"x": 100, "y": 200}},
            {"id": "n2", "type": "doc_loader", "label": "Load Document", "config": {"source_type": "text"}, "position": {"x": 380, "y": 200}},
            {"id": "n3", "type": "text_splitter", "label": "Chunk Text", "config": {"strategy": "character", "chunk_size": "500", "overlap": "50"}, "position": {"x": 660, "y": 200}},
            {"id": "n4", "type": "embedding_model", "label": "Embedding Config", "config": {"provider": "openai", "api_key": "__ASK_USER__"}, "position": {"x": 940, "y": 400}},
            {"id": "n5", "type": "embedding_generate", "label": "Generate Embeddings", "config": {"text_template": "{{input}}"}, "position": {"x": 940, "y": 200}},
            {"id": "n6", "type": "vectorstore_config", "label": "VectorDB Config", "config": {"provider": "chroma", "collection": "default"}, "position": {"x": 1220, "y": 400}},
            {"id": "n7", "type": "vector_upsert", "label": "Store Embeddings", "config": {}, "position": {"x": 1220, "y": 200}},
            {"id": "n8", "type": "response_builder", "label": "Response", "config": {"response_schema": {}, "field_mappings": []}, "position": {"x": 1500, "y": 200}},
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
            {"id": "n1", "type": "http_entry", "label": "API Entry", "config": {"method": "POST", "path": "/api/query", "request_schema": {"table": "string"}, "response_schema": {"rows": "list"}}, "position": {"x": 100, "y": 200}},
            {"id": "n2", "type": "pg_find", "label": "Query Database", "config": {"connection_id": "", "table": ""}, "position": {"x": 380, "y": 200}},
            {"id": "n3", "type": "response_builder", "label": "Response", "config": {"response_schema": {}, "field_mappings": []}, "position": {"x": 660, "y": 200}},
        ],
        "edges": [
            {"source": "n1", "target": "n2", "sourceHandle": "output", "targetHandle": "input"},
            {"source": "n2", "target": "n3", "sourceHandle": "output", "targetHandle": "input"},
        ],
    },
}

# ---------------------------------------------------------------------------
# Helpers for connection points and config schema
# ---------------------------------------------------------------------------

HANDLE_DESCRIPTIONS = {
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


def _build_connection_points(component_type: str) -> dict:
    """Build connection_points (outputs + inputs) with required/satisfied_by for a component."""
    info = COMPONENT_CATALOG.get(component_type)
    if not info:
        return {"outputs": [], "inputs": []}
    outputs = []
    for h in info.get("source_handles", []):
        compatible = HANDLE_COMPATIBILITY.get(h, [])
        outputs.append({
            "handle": h,
            "description": HANDLE_DESCRIPTIONS.get(h, "Data output"),
            "connects_to_handles": compatible,
        })
    inputs = []
    req_list = REQUIRED_CONNECTIONS.get(component_type, [])
    req_by_handle = {e["target_handle"]: e for e in req_list}
    for h in info.get("target_handles", []):
        receives_from = [sh for sh, targets in HANDLE_COMPATIBILITY.items() if h in targets]
        entry = {
            "handle": h,
            "description": HANDLE_DESCRIPTIONS.get(h, "Data input"),
            "receives_from_handles": receives_from,
        }
        if h in req_by_handle:
            entry["required"] = req_by_handle[h]["required"]
            entry["satisfied_by_component_types"] = req_by_handle[h]["satisfied_by_component_types"]
        else:
            entry["required"] = False
            entry["satisfied_by_component_types"] = []
        inputs.append(entry)
    return {"outputs": outputs, "inputs": inputs}


def _normalize_config_schema(config_schema: list) -> list:
    """Ensure every field has a 'description' key (default '')."""
    out = []
    for f in config_schema:
        d = dict(f)
        if "description" not in d:
            d["description"] = ""
        out.append(d)
    return out


# ---------------------------------------------------------------------------
# Stateless discovery tools — no graph_state dependency
# ---------------------------------------------------------------------------


@tool
def list_categories() -> str:
    """List all available component categories with descriptions and roles.

    Returns:
        JSON with each category name, description, role, component count, and a hint
        to call get_components_by_category(category) next to list components and connection points.
    """
    result = {}
    for cat, info in CATEGORY_INFO.items():
        count = sum(1 for c in COMPONENT_CATALOG.values() if c["category"] == cat)
        result[cat] = {
            **info,
            "component_count": count,
            "hint": f"Call get_components_by_category('{cat}') to list components and their connection points.",
        }
    return json.dumps(result, indent=2)


@tool
def get_components_by_category(category: str) -> str:
    """Get all components belonging to a specific category with full details.

    Includes connection_points (outputs and inputs with descriptions, required,
    satisfied_by_component_types) and config_schema with description for every field.

    Args:
        category: Category name (e.g. 'trigger', 'ai_exec', 'database').

    Returns:
        JSON with category, description, role, and components. Each component has
        type, description, config_schema (with description), fields, connection_points,
        and required_connections (if any).
    """
    if category not in CATEGORY_INFO:
        available = ", ".join(sorted(CATEGORY_INFO.keys()))
        return f"Error: Unknown category '{category}'. Available: {available}"

    components = []
    for name, info in COMPONENT_CATALOG.items():
        if info["category"] == category:
            config_schema = _normalize_config_schema(info.get("config_schema", []))
            connection_points = _build_connection_points(name)
            required_connections = REQUIRED_CONNECTIONS.get(name, [])
            components.append({
                "type": name,
                "description": info["description"],
                "config_schema": config_schema,
                "fields": info["fields"],
                "source_handles": info["source_handles"],
                "target_handles": info["target_handles"],
                "connection_points": connection_points,
                "required_connections": required_connections,
            })
    return json.dumps({"category": category, **CATEGORY_INFO[category], "components": components}, indent=2)


@tool
def get_component_details(component_type: str) -> str:
    """Get full details for a specific component including connection points and required connections.

    Args:
        component_type: The component type name (e.g. 'llm_call', 'agent_run').

    Returns:
        JSON with type, category, description, config_schema (with description),
        connection_points (outputs/inputs with required/satisfied_by), required_connections.
    """
    info = COMPONENT_CATALOG.get(component_type)
    if not info:
        return f"Error: Unknown component '{component_type}'."
    out = {"type": component_type, **dict(info)}
    out["config_schema"] = _normalize_config_schema(out.get("config_schema", []))
    out["connection_points"] = _build_connection_points(component_type)
    out["required_connections"] = REQUIRED_CONNECTIONS.get(component_type, [])
    return json.dumps(out, indent=2)


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

    source_details = []
    for h in info["source_handles"]:
        compatible = HANDLE_COMPATIBILITY.get(h, [])
        source_details.append({
            "handle": h,
            "description": HANDLE_DESCRIPTIONS.get(h, "Data output"),
            "connects_to_target_handles": compatible,
        })

    target_details = []
    for h in info["target_handles"]:
        receives_from = [sh for sh, targets in HANDLE_COMPATIBILITY.items() if h in targets]
        target_details.append({
            "handle": h,
            "description": HANDLE_DESCRIPTIONS.get(h, "Data input"),
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


@tool
def get_connection_points(component_type: str) -> str:
    """Get a unified view of all connection points (in and out) for a component.

    Returns outputs and inputs with handle id, direction, description, required/optional,
    and for config inputs: which component types can satisfy them.

    Args:
        component_type: The component type name.

    Returns:
        JSON with connection_points.outputs and connection_points.inputs (each with
        handle, description, required, satisfied_by_component_types where applicable).
    """
    info = COMPONENT_CATALOG.get(component_type)
    if not info:
        return f"Error: Unknown component '{component_type}'."
    cp = _build_connection_points(component_type)
    return json.dumps({"component": component_type, "connection_points": cp}, indent=2)


@tool
def get_required_connections(component_type: str) -> str:
    """Get required and optional config connections for a component.

    For components that need config nodes (e.g. llm_call needs llm_model on ai_model),
    returns each target_handle that expects a connection: whether it is required,
    which component types must be added to satisfy it, and the handle pair for the edge.

    Args:
        component_type: The component type name (e.g. 'llm_call', 'agent_run', 'embedding_generate').

    Returns:
        JSON with required_connections list. Each entry has target_handle, required,
        satisfied_by_component_types, and example edge (sourceHandle/targetHandle).
        If the component has no config connections, returns empty list.
    """
    info = COMPONENT_CATALOG.get(component_type)
    if not info:
        return f"Error: Unknown component '{component_type}'."
    entries = REQUIRED_CONNECTIONS.get(component_type, [])
    result = []
    for e in entries:
        th = e["target_handle"]
        satisfied = e["satisfied_by_component_types"]
        result.append({
            "target_handle": th,
            "required": e["required"],
            "satisfied_by_component_types": satisfied,
            "example_edge": {
                "sourceHandle": th,
                "targetHandle": th,
            },
            "note": f"Add one of {satisfied} and connect its '{th}' output to this node's '{th}' input.",
        })
    return json.dumps({
        "component": component_type,
        "required_connections": result,
    }, indent=2)


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


def validate_plan_required_connections(plan: dict) -> list[str]:
    """Validate that every node with required config target_handles has an edge filling each.

    Returns a list of issue strings (e.g. "Node n3 (llm_call) requires an edge on
    target_handle 'ai_model' from a llm_model node"). Empty if all required connections are present.
    """
    issues: list[str] = []
    node_map = {n["id"]: n["type"] for n in plan.get("nodes", [])}
    edges_in = defaultdict(list)
    for e in plan.get("edges", []):
        tgt_id = e.get("target")
        tgt_handle = e.get("targetHandle", "input")
        if tgt_id:
            edges_in[tgt_id].append(tgt_handle)

    for node in plan.get("nodes", []):
        nid = node.get("id", "")
        ntype = node.get("type", "")
        req_list = REQUIRED_CONNECTIONS.get(ntype, [])
        for req in req_list:
            if not req.get("required"):
                continue
            th = req["target_handle"]
            if th not in edges_in.get(nid, []):
                satisfied = req.get("satisfied_by_component_types", [])
                names = ", ".join(satisfied) if satisfied else "a config node"
                issues.append(
                    f"Node {nid} ({ntype}) requires an edge on target_handle '{th}' from {names}."
                )
    return issues


def scan_missing_secrets(graph_state: dict) -> list[dict]:
    """Scan built graph for config fields marked secret that are empty.

    Returns a list of {node_id, node_label, field_key, field_label} dicts.
    """
    missing: list[dict] = []
    for node in graph_state.get("nodes", []):
        node_type = node.get("type", "")
        comp = COMPONENT_CATALOG.get(node_type)
        if not comp:
            continue
        cfg = node.get("data", {}).get("config", {})
        for field_def in comp.get("config_schema", []):
            if not field_def.get("secret"):
                continue
            val = cfg.get(field_def["key"], "")
            if not val or val == "__ASK_USER__":
                missing.append({
                    "node_id": node["id"],
                    "node_label": node.get("data", {}).get("label", node_type),
                    "field_key": field_def["key"],
                    "field_label": field_def["label"],
                })
    return missing


# All standalone discovery tools in one list for easy assembly
DISCOVERY_TOOLS = [
    list_categories,
    get_components_by_category,
    get_component_details,
    get_compatible_targets,
    validate_connection,
    get_handle_info,
    get_connection_points,
    get_required_connections,
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

        fill_config_defaults(node_type, cfg)
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
