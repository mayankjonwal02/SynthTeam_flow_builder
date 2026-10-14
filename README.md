<div align="center">

# SynthTeam Flow Builder

**Visually design backend APIs, AI agents and RAG pipelines — then deploy them as live endpoints with one click.**

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
![Backend](https://img.shields.io/badge/backend-FastAPI-009688)
![Frontend](https://img.shields.io/badge/frontend-Next.js%2016-black)
![Python](https://img.shields.io/badge/python-3.11-3776AB)

</div>

---

SynthTeam is a low-code workflow builder. You drag nodes onto a canvas, wire them together, and press **Deploy** — the backend compiles the graph and registers it as a real HTTP route on the running FastAPI server. Workflows can query databases, branch and loop, call LLMs, run tool-using agents, and search vector stores.

An **AI Agent Builder** can also generate a workflow for you from a plain-English prompt, using a Requirement → Planner → Builder → Reviewer chain of agents.

## Features

- **Visual editor** — ReactFlow canvas with typed connection handles, per-field modes (static value / variable / expression) and live execution logs.
- **One-click deploy** — each workflow becomes a live `GET`/`POST`/`PUT`/`DELETE` endpoint, listed in the backend's OpenAPI docs and grouped by project.
- **Flow control** — if/else, switch/case, for-each loops, parallel split/merge, delays, and sandboxed Python function nodes.
- **Triggers** — HTTP entry, webhook, cron schedule (APScheduler) and manual.
- **Databases** — find / insert / update / delete / raw query nodes (plus transactions where supported) for **PostgreSQL, MySQL, MongoDB, SQLite and Supabase**, with saved, encrypted connection credentials.
- **AI layer**
  - LLM providers: OpenAI, Anthropic, Google Gemini, Groq, Mistral, Ollama
  - Embeddings: OpenAI, Ollama, HuggingFace
  - Vector stores: Qdrant, Pinecone, Weaviate, ChromaDB, Supabase pgvector
  - ReAct and autonomous agents with tools (web search, HTTP, DB query, code execution, email/Gmail, Slack, Composio, knowledge base, sub-workflows)
  - Conversation memory (in-memory, Redis, vector), structured output, vision, speech-to-text and text-to-speech
- **AI Agent Builder** — describe the API you want; agents plan, build and review the graph while streaming progress over WebSocket.
- **Auth & safety** — Clerk authentication, Fernet-encrypted credentials, Redis-backed rate limiting on deployed routes.

## Architecture

```
┌──────────────────────────┐   REST / WebSocket   ┌───────────────────────────────┐
│  Frontend (Next.js 16)   │ ───────────────────▶ │  Backend (FastAPI)            │
│  ReactFlow editor        │                      │  ├─ Project / file / DB APIs  │
│  Clerk auth · Zustand    │                      │  ├─ GraphCompiler → Executor  │
└──────────────────────────┘                      │  ├─ Dynamic route registry    │
                                                  │  ├─ AI layer (LangChain)      │
                                                  │  └─ Multi-agent builder       │
                                                  └──────┬───────────┬────────────┘
                                                         │           │
                                                  ┌──────▼─────┐ ┌───▼────┐ ┌────────┐
                                                  │ PostgreSQL │ │ Redis  │ │ Celery │
                                                  │ (app data) │ │        │ │ worker │
                                                  └────────────┘ └────────┘ └────────┘
```

Saving a workflow stores its graph JSON. Deploying runs the **GraphCompiler** (validates the graph and computes the execution order) and registers a route whose handler runs the **GraphExecutor**, which passes each node's output along its edges. See [docs/architecture.md](docs/architecture.md) for details.

## Quick start

### Prerequisites

- Docker and Docker Compose
- A [Clerk](https://clerk.com) application (free tier works) for sign-in
- At least one LLM provider API key, or a local [Ollama](https://ollama.com) install, if you plan to use AI nodes or the Agent Builder

### 1. Clone

```bash
git clone https://github.com/mayankjonwal02/SynthTeam_flow_builder.git
cd SynthTeam_flow_builder
```

### 2. Configure environment

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
```

Fill in the Clerk keys and generate an encryption key:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

> **Note:** set `CLERK_JWKS_URL` in `backend/.env` to your own Clerk instance's JWKS endpoint, otherwise the backend rejects your sign-in tokens. See [docs/configuration.md](docs/configuration.md#clerk-authentication).

### 3. Run

```bash
docker compose up --build
```

| Service      | URL                          |
|--------------|------------------------------|
| Frontend     | http://localhost:3000        |
| Backend API  | http://localhost:8000        |
| API docs     | http://localhost:8000/docs   |
| PostgreSQL   | localhost:5432               |
| Redis        | localhost:6379               |

To run the services without Docker, see [docs/getting-started.md](docs/getting-started.md#running-without-docker).

### 4. Build your first API

1. Sign in and create a **project** on the dashboard.
2. Create a **file** (workflow) inside it and open the editor.
3. Drag in **HTTP Entry** → **Processor** → **Response** and connect them.
4. Set the entry path (for example `/hello`) and method, then click **Deploy**.
5. Call it: `curl -X POST http://localhost:8000/hello -H 'Content-Type: application/json' -d '{"name":"world"}'`

## Documentation

| Document | What it covers |
|----------|----------------|
| [Getting started](docs/getting-started.md) | Installation, local development, first workflow |
| [Configuration](docs/configuration.md) | Every environment variable, Clerk and Ollama setup |
| [Architecture](docs/architecture.md) | Components, compile/deploy/execute lifecycle, data model |
| [API reference](docs/api-reference.md) | REST and WebSocket endpoints |
| [Node reference](docs/node-reference.md) | Every node, its handles and example workflows |
| [Data flow](docs/data-flow.md) | How nodes and edges become a running API |
| [AI Agent Builder](docs/agent-builder.md) | Generating workflows from prompts |
| [Code documentation](docs/code-documentation.md) | File-by-file walkthrough of the codebase |
| [Roadmap](docs/roadmap.md) | Planned features |

The full index is at [docs/README.md](docs/README.md).

## Project structure

```
.
├── backend/                 FastAPI application
│   └── app/
│       ├── api/             REST routers (projects, files, db-connections)
│       ├── components/      Workflow node implementations (incl. ai/)
│       ├── db_connectors/   PostgreSQL, MySQL, MongoDB, SQLite, Supabase
│       ├── runtime/         Graph compiler, executor, dynamic route registry
│       ├── ai/              LLMs, embeddings, vector stores, tools, agents, memory
│       ├── multi_agent/     AI Agent Builder (REST + WebSocket)
│       ├── core/            Settings and Clerk auth
│       ├── models/          SQLAlchemy models
│       └── main.py          App entrypoint
├── frontend/                Next.js app (editor, dashboard, agent builder)
├── docs/                    Project documentation
├── test_dbs/                Docker Compose for local MySQL/Postgres test databases
├── reports/                 Generated QA / security reports
└── docker-compose.yml       Full stack: postgres, redis, backend, celery, frontend
```

## Contributing

Contributions are welcome. Read [CONTRIBUTING.md](CONTRIBUTING.md) for the development workflow and how to add a new node type.

## Security

Management APIs and the Agent Builder require a signed-in user, and every project, workflow, log, connection and agent session is scoped to its owner. Workflow nodes bind SQL values as parameters and run Python in an isolated process. Workflows can still run user-supplied Python and SQL, though, and node configs can hold API keys, so only let trusted users author workflows. See the [security model](docs/architecture.md#security-model), and report vulnerabilities privately to the maintainer rather than in a public issue.

## License

Licensed under the [Apache License, Version 2.0](LICENSE). See [NOTICE](NOTICE) for attribution.
