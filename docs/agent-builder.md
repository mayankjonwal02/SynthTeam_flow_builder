# AI Agent Builder

The Agent Builder turns a natural-language request ("build a chatbot API with memory and web search") into a working SynthTeam workflow. You watch the graph appear on a live canvas, answer follow-up questions, supply any secrets it needs, then save the result as a regular workflow file and deploy it.

Open it in the app at `/agent-builder`.

## How it works

`backend/app/multi_agent/orchestrator.py` runs a chain of LangChain ReAct agents:

```
prompt ─▶ Requirement ─▶ Planner ─▶ Builder ─▶ Reviewer ─┐
                                       ▲                  │ issues found (max 3 rounds)
                                       └──────────────────┘
```

| Agent | Role |
|-------|------|
| **Requirement** | Clarifies the request and extracts a structured spec (endpoints, data, providers) |
| **Planner** | Chooses node types from the component catalog and plans the edges between them |
| **Builder** | Creates nodes and edges on the canvas via tools; each change streams to the browser |
| **Reviewer** | Validates handle compatibility and required connections; sends issues back to the Builder, up to three times |
| **Feedback** | Summarises diagnostics from the run |

Helper tools in `multi_agent/tools.py` validate edges (`validate_plan_edges`, `validate_plan_required_connections`), fill config defaults (`fill_config_defaults`) and detect missing credentials (`scan_missing_secrets`). When secrets are missing the session emits `needs_input`, and the UI prompts for them.

There is also an **optimized pipeline** (`optimized_*.py`) with batch node/edge creation, caching, tighter prompts and performance monitoring. It is exposed under `/agent/optimized/*`; see [agent-builder-optimization.md](agent-builder-optimization.md).

## Choosing a model

Each session takes `llm_provider`, `llm_model` and an optional `api_key`. The default is local Ollama with `llama3.1:8b`, so the builder works without any cloud key once Ollama is running and `OLLAMA_BASE_URL` points at it. Larger hosted models (OpenAI, Anthropic, Groq, Gemini, Mistral) produce more reliable graphs for complex requests. Without an `api_key`, the provider's key from `backend/.env` is used (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, `MISTRAL_API_KEY`, `GROQ_API_KEY`).

You can switch provider or model mid-session by passing them with a follow-up message.

## Session lifecycle

All calls need a Clerk bearer token, and a session is only visible to the user who started it.

1. `POST /agent/session` with the prompt → returns `session_id`. The pipeline starts in the background.
2. Connect to `ws://localhost:8000/ws/agent/{session_id}?token=<clerk token>` for live events.
3. Answer questions or request changes with `POST /agent/session/{id}/message`. After the first message, messages are treated as follow-ups. Only one run per session at a time (`409` while busy).
4. Provide credentials with `POST /agent/session/{id}/secrets`. The values are written into the matching node configs and the review resumes.
5. Accept the result with `POST /agent/session/{id}/approve`, or keep iterating.
6. `POST /agent/session/{id}/save?project_id=…&name=…` stores the graph as a workflow file in one of your projects. The UI asks which project.
7. Open the file in the editor and **Deploy**.

In the editor, the **AI Copilot** panel uses the same API and merges the agents' nodes into your existing canvas instead of replacing it.

Full request/response shapes are in the [API reference](api-reference.md#ai-agent-builder--agent).

## Configuration

| Variable | Effect |
|----------|--------|
| `OLLAMA_BASE_URL` | Where to find Ollama models |
| `GROQ_API_KEY` | Default Groq key |
| `AGENT_BUILDER_CONTEXT_MESSAGES` | Number of past messages kept in agent context (default 60) |

## Testing

`backend/test_optimized_system.py` runs end-to-end scenarios (simple API, CRUD, AI chatbot, RAG…) against the optimized pipeline and checks the expected node types are produced:

```bash
cd backend
python test_optimized_system.py
```

It needs a reachable LLM provider.
