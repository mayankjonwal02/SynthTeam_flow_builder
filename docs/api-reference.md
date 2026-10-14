# API Reference

Base URL: `http://localhost:8000`. Interactive docs with request/response schemas are served at `/docs` (Swagger UI) and `/redoc`.

**Auth** column: 🔒 requires `Authorization: Bearer <Clerk session token>`; 🌐 public.

## Health

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/` | 🌐 | Returns `{"message": "SynthTeam Backend Running"}` |
| GET | `/protected` | 🔒 | Returns the decoded token payload; useful for checking auth setup |

## Projects — `/api/projects`

| Method | Path | Auth | Body | Description |
|--------|------|------|------|-------------|
| POST | `/api/projects` | 🔒 | `{"name": str}` | Create a project |
| GET | `/api/projects` | 🔒 | — | List the caller's projects |
| PUT | `/api/projects/{project_id}` | 🔒 | `{"name": str}` | Rename a project |
| DELETE | `/api/projects/{project_id}` | 🔒 | — | Delete a project |
| GET | `/api/projects/{project_id}/openapi` | 🔒 | — | OpenAPI spec containing only this project's deployed routes |

## Files (workflows) — `/api/files`

| Method | Path | Auth | Body | Description |
|--------|------|------|------|-------------|
| POST | `/api/files` | 🔒 | `{"project_id": uuid, "name": str}` | Create an empty workflow |
| GET | `/api/files/project/{project_id}` | 🔒 | — | List workflows in a project |
| GET | `/api/files/{file_id}` | 🔒 | — | Get a workflow including its graph |
| GET | `/api/files/{file_id}/meta` | 🔒 | — | Name, project and deploy status |
| PUT | `/api/files/{file_id}` | 🔒 | graph JSON | Save the workflow graph |
| DELETE | `/api/files/{file_id}` | 🔒 | — | Delete a workflow |
| GET | `/api/files/{file_id}/logs?limit=50` | 🔒 | — | Recent execution logs with node traces |
| POST | `/api/files/deploy/{file_id}` | 🔒 | — | Compile and mount the workflow as a live route |
| POST | `/api/files/undeploy/{file_id}` | 🔒 | — | Remove the live route (and its cron job) |

Deploy response:

```json
{ "success": true, "endpoint": "/hello", "method": "POST", "tag": "MyProject_<project-id>" }
```

Compilation errors (for example, no entry node) return `422` with a `detail` message.

## Database connections — `/api/db-connections`

| Method | Path | Auth | Body | Description |
|--------|------|------|------|-------------|
| POST | `/api/db-connections` | 🔒 | `{"name": str, "db_type": str, "credentials": {...}}` | Save a connection; credentials are encrypted |
| GET | `/api/db-connections` | 🔒 | — | List saved connections (no secrets) |
| GET | `/api/db-connections/{conn_id}` | 🔒 | — | Get one connection |
| DELETE | `/api/db-connections/{conn_id}` | 🔒 | — | Delete a connection |
| POST | `/api/db-connections/{conn_id}/test` | 🔒 | — | Open a connection and report success or the error |

`db_type` is one of `postgres`, `mysql`, `mongodb`, `sqlite`, `supabase`.

## Deployed workflow routes

Each deployed workflow is mounted at the `method` and `path` from its HTTP Entry node (prefixed with `/{version}` if the entry sets a version). These routes:

- validate the body, query and path parameters against the schemas defined on the entry node;
- appear in `/docs` under the project's tag;
- are public unless the workflow contains an **Auth Gate** node;
- are rate-limited when the entry node sets `rate_limit`; the limit key is the `x-api-key` header, falling back to client IP. Exceeding it returns `429`.

## AI Agent Builder — `/agent`

These endpoints currently do not require authentication. See [agent-builder.md](agent-builder.md) for the flow.

| Method | Path | Body | Description |
|--------|------|------|-------------|
| GET | `/agent/ollama/models` | — | Models available on `OLLAMA_BASE_URL` |
| POST | `/agent/session` | `SessionStartRequest` | Start a build session (alias: `/agent/session/start`). Returns the session id; work continues in the background. |
| POST | `/agent/session/{session_id}/message` | `SessionMessageRequest` | Send a follow-up or change request |
| POST | `/agent/session/{session_id}/secrets` | `{"secrets": {node_id: {field: value}}}` | Supply API keys/credentials the agents asked for |
| GET | `/agent/session/{session_id}` | — | Session state, messages and current graph |
| POST | `/agent/session/{session_id}/save?project_id=` | — | Save the generated graph as a workflow file |
| POST | `/agent/optimized/build` | `SessionStartRequest` | Build using the optimized multi-agent pipeline |
| GET | `/agent/optimized/performance` | — | Performance metrics for the optimized pipeline |
| GET | `/agent/optimized/status/{session_id}` | — | Status of an optimized build |
| POST | `/agent/optimized/cancel/{session_id}` | — | Cancel an optimized build |

```jsonc
// SessionStartRequest
{
  "prompt": "Build a CRUD API for a users table in PostgreSQL",
  "project_id": null,          // optional
  "user_id": "anonymous",
  "llm_provider": "ollama",    // ollama | openai | anthropic | groq | gemini | mistral
  "llm_model": "llama3.1:8b",
  "api_key": null              // provider key, if needed
}

// SessionMessageRequest
{ "message": "Add rate limiting", "llm_provider": null, "llm_model": null, "api_key": null }
```

### WebSocket — `/ws/agent/{session_id}`

Connect after starting a session to receive live events. Each message is JSON:

```json
{ "type": "node_added", "data": { ... }, "timestamp": "2026-01-01T12:00:00" }
```

| `type` | Meaning |
|--------|---------|
| `status_change` | Session moved to a new phase (requirement, planning, building, reviewing, done…) |
| `agent_thinking` | An agent started working |
| `agent_message` | An agent produced a message for the user |
| `agent_done` | An agent finished its step |
| `node_added` / `node_updated` / `node_deleted` | Canvas change |
| `edge_added` | Canvas change |
| `needs_input` | Agents need secrets or clarification from the user |
| `error` | Build failed |

## Agent-to-Agent (A2A) — `/api/agents`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/agents/` | List registered agents |
| GET | `/api/agents/{agent_id}/capabilities` | Describe an agent's capabilities |
| POST | `/api/agents/{agent_id}/message` | Send an `A2AMessage`; returns an `A2AResponse` |
