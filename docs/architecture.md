# Architecture

SynthTeam has two applications — a Next.js frontend and a FastAPI backend — backed by PostgreSQL and Redis, plus an optional Celery worker.

```
Browser ──▶ Next.js frontend ──REST/WS──▶ FastAPI backend ──▶ PostgreSQL (app data)
                                              │          ├──▶ Redis (rate limits, memory, Celery broker)
                                              │          └──▶ User databases / LLM providers / vector stores
                                              └── dynamically registered workflow routes
```

## Frontend

`frontend/` — Next.js 16 (App Router), React 19, ReactFlow 11, Zustand, Tailwind CSS 4, shadcn/ui, Clerk.

| Route | Purpose |
|-------|---------|
| `/` | Landing page |
| `/sign-in`, `/sign-up` | Clerk auth |
| `/dashboard` | Projects overview |
| `/projects/[projectId]` | Files (workflows) in a project |
| `/files/[fileId]` | Visual workflow editor |
| `/files/[fileId]/logs` | Execution logs of a workflow |
| `/builder` | Standalone builder canvas |
| `/agent-builder`, `/agent-builder/[sessionId]` | AI Agent Builder chat + live canvas |

Key code:

- `components/nodes/` — one React component per node type; `nodeTypes.ts` maps type names to components. `db/` and `ai/` hold database and AI nodes, many built from factories (`DBNodeFactory`, `AINodeFactory`, `ConfigNodeFactory`).
- `components/nodes/FieldModeInput.tsx` — lets a config field be a static value, a reference to upstream data, or an expression.
- `components/agent/` — Agent Builder canvas, chat panel, copilot panel and status bar.
- `hooks/useAgentWebSocket.ts` — streaming connection to `/ws/agent/{session_id}`.
- `proxy.ts` — Clerk middleware (Next.js 16 replacement for `middleware.ts`).

## Backend

`backend/app/` — FastAPI, SQLAlchemy 2 (async), LangChain/LangGraph, APScheduler, Celery.

| Package | Responsibility |
|---------|----------------|
| `main.py` | App factory, CORS, startup (create tables, register components/connectors/AI providers, Redis, scheduler), router wiring |
| `api/` | REST routers: projects, files (save/deploy/logs), database connections |
| `core/` | Settings (`config.py`) and Clerk JWT verification (`auth.py`) |
| `models/` | SQLAlchemy models |
| `runtime/` | `compiler.py` (graph → plan), `executor.py` (runs a plan), `registry.py` (mounts/unmounts routes, cron jobs, rate limiting) |
| `components/` | One class per node type, registered with `@register_component("<type>")` |
| `db_connectors/` | Async connectors and pool manager for PostgreSQL, MySQL, MongoDB, SQLite, Supabase; `interpolation.py` resolves field modes |
| `ai/` | Registries for LLMs, embeddings, vector stores, vision and tools; ReAct/autonomous agents; memory; speech; A2A protocol; observability |
| `multi_agent/` | AI Agent Builder: orchestrator, agents, tools, session store, REST and WebSocket APIs |
| `scheduler.py` | APScheduler instance used by cron triggers |
| `celery_worker.py` | Celery app (Redis broker) |
| `utils/` | Fernet encryption for credentials, Redis rate limiter |

### Plugin registries

Node components, DB connectors, LLM providers, embedding providers, vector stores and tools all use the same pattern: a module-level dictionary filled by a decorator when the module is imported. `main.py` imports each package at startup, which registers everything. Adding a capability means adding a module and importing it from its package's `__init__.py` — see [CONTRIBUTING.md](../CONTRIBUTING.md#adding-a-new-node-type).

## Workflow lifecycle

### 1. Save

The editor serialises the ReactFlow graph (nodes with `data.component` and `data.config`, plus edges with source/target handles) and `PUT`s it to `/api/files/{id}`. It is stored as JSONB in `files.graph_json`.

### 2. Compile

`POST /api/files/deploy/{id}` runs `GraphCompiler`, which:

- finds the entry node (`is_entry: true`) and the response node;
- reads `method`, `path`, optional `version` prefix, request/response/query schemas, path params and `rate_limit` from the entry config;
- builds dynamic Pydantic models for request validation and OpenAPI docs;
- topologically sorts the nodes and builds the edge map (including branch conditions from `if`/`switch` handles);
- detects cron triggers.

The result is an execution plan:

```python
{
  "method": "POST", "path": "/hello",
  "request_model": DynReq, "response_model": DynResp, "query_model": None,
  "path_params": None,
  "ordered_nodes": [{"id", "component", "config"}, ...],
  "edge_map": {target_id: [{"parent", "condition"}, ...]},
  "forward_adj": {source_id: [target_id, ...]},
  "rate_limit": {"requests": 100, "window_seconds": 60} | None,
  "has_cron": False, "cron_expression": None,
}
```

### 3. Register

`runtime/deployment.deploy_file` stores the project owner on the plan and calls `runtime/registry.register_route`, which:

- rejects reserved paths (`/`, `/protected`, and anything under `/api`, `/agent`, `/ws`, `/docs`, `/redoc`, `/openapi.json`) with **422**;
- rejects a method + path already served by another workflow with **409**;
- replaces this workflow's previous route, if any (even if the path changed);
- tags the route with the project for the OpenAPI docs and schedules an APScheduler job if the graph has a cron trigger.

The file is marked `is_deployed` with its path and method.

Routes live in the backend process's memory, so on startup `restore_deployed_routes` re-registers every file marked as deployed (and its cron job). A file whose graph no longer compiles, or whose path is now invalid or taken, is marked undeployed and the reason is logged. With several backend worker processes each one restores the routes itself.

### 4. Execute

On each request the handler enforces the rate limit (keyed by client IP), then `GraphExecutor`:

1. walks nodes in topological order;
2. collects each node's inputs from its parents' outputs, skipping branches whose condition did not match;
3. **skips** a node when all of its data parents were skipped or failed, so a skipped branch never runs downstream nodes with empty input;
4. resolves field modes and `{{variable}}` interpolation in the node config;
5. calls `component.execute(request_data, inputs, config)`;
6. records each node's input, output, timing and errors into a trace.

Outcomes:

| What happened | HTTP response | Log status |
|---------------|---------------|------------|
| Every node succeeded or was skipped | `200` with the response node's output | `success` |
| A node raised an HTTP error (e.g. **Auth Gate** → 401) | That status and `{"detail": ...}`; nothing after it runs | `rejected` |
| A node failed | `500` with `{"error", "execution_id", "failed_nodes"}`; its descendants are skipped | `failed` |

The trace is stored in `workflow_execution_logs` with `Authorization`, `Cookie` and `X-API-Key` header values redacted. [data-flow.md](data-flow.md) walks through a concrete example.

## Data model

| Table | Purpose |
|-------|---------|
| `users` | Clerk user mirror (`clerk_id`, `email`) |
| `projects` | Workflow groups owned by a user |
| `files` | A workflow: `graph_json`, `is_deployed`, `deployed_path`, `deployed_method` |
| `api_keys` | API keys for calling deployed routes |
| `database_connections` | Saved DB connections with Fernet-encrypted credentials |
| `workflow_execution_logs` | Per-execution status and node trace |
| `agent_sessions` | AI Agent Builder sessions |

Tables are created with `Base.metadata.create_all` on startup; there are no migrations yet.

## Security model

- **Authentication** — every management API (projects, files, logs, DB connections, deploy), the Agent Builder (`/agent/*`), A2A (`/api/agents/*`) and the Agent Builder WebSocket require a Clerk token. Deployed workflow routes are public unless the workflow includes an **Auth Gate** node.
- **Ownership** — projects, files, logs, DB connections and Agent Builder sessions are only visible to their owner; anyone else gets `404`. A deployed workflow can only use DB connections owned by the workflow's owner, and can't point a raw connection URI at the platform's own database.
- **Credentials** — saved database credentials are encrypted with `ENCRYPTION_KEY`. API keys typed into node configs are stored in the graph JSON in plain text, so treat workflow files as secrets. The Agent Builder never returns stored API keys from `GET /agent/session/{id}`.
- **Code execution** — the **Python Function** node rejects imports and private/dunder attribute access before running, then runs the handler in a separate isolated Python process with no server environment variables, killed at the timeout (default 10s). The agent **Code Executor** tool also runs in an isolated process without secrets, and the **File** tools are confined to their base directory. These are guard rails, not a hardened sandbox: only let trusted users author workflows.
- **SQL** — table and column names are validated as plain identifiers, values are always bound parameters, and update/delete without filters are refused. Raw query nodes bind `{{input.x}}` and `:x` placeholders as parameters (quotes directly around a placeholder are dropped). Write `LIKE` patterns as `'%' || {{input.q}} || '%'`, not `'%{{input.q}}%'`.
- **SQLite** — database files must live inside `SQLITE_BASE_DIR`.
- **Rate limiting** — per-route limits from the entry node config, keyed by client IP and enforced in Redis. Skipped if Redis is unavailable.

Security QA reports from earlier audits are in [`reports/`](../reports).
