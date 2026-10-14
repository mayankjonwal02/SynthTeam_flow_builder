# Getting Started

This guide gets SynthTeam running locally and walks through deploying a first workflow.

## Prerequisites

| Tool | Version | Needed for |
|------|---------|------------|
| Docker + Docker Compose | recent | The recommended way to run everything |
| Python | 3.11 | Running the backend without Docker |
| Node.js | 20 | Running the frontend without Docker |
| PostgreSQL | 15 | Application database (provided by Compose) |
| Redis | 7 | Rate limiting, Celery broker, Redis memory (provided by Compose) |
| Clerk account | — | User sign-in |
| Ollama *(optional)* | — | Local LLMs for AI nodes and the Agent Builder |

## Running with Docker (recommended)

```bash
git clone https://github.com/mayankjonwal02/SynthTeam_flow_builder.git
cd SynthTeam_flow_builder

cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
# edit both files — see configuration.md

docker compose up --build
```

Compose starts five services:

| Service | Container | Port | Notes |
|---------|-----------|------|-------|
| `postgres` | `synthteam_postgres` | 5432 | User `synthuser`, password `synthpass`, database `synthdb` |
| `redis` | `synthteam_redis` | 6379 | |
| `backend` | `synthteam_backend` | 8000 | Uvicorn with `--reload`; `./backend` is mounted for live edits |
| `celery` | `synthteam_celery` | — | Background worker |
| `frontend` | `synthteam_frontend` | 3000 | `next dev` with polling file watcher |

Open http://localhost:3000 for the app and http://localhost:8000/docs for the interactive API docs. Tables are created automatically on backend startup.

The backend container can reach services on your host machine (such as Ollama) at `host.docker.internal`.

## Running without Docker

Start PostgreSQL and Redis yourself (or run only those two: `docker compose up postgres redis`).

### Backend

```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Use localhost instead of the compose service names in backend/.env:
#   DATABASE_URL=postgresql+asyncpg://synthuser:synthpass@localhost:5432/synthdb
#   REDIS_URL=redis://localhost:6379/0

uvicorn app.main:app --reload --port 8000
```

Optional worker, in a second terminal:

```bash
celery -A app.celery_worker worker --loglevel=info
```

### Frontend

```bash
cd frontend
npm ci
npm run dev
```

## Your first workflow

1. **Sign in** at http://localhost:3000 and open the **Dashboard**.
2. **Create a project.** Projects group workflows, and each project gets its own section in the OpenAPI docs.
3. **Create a file.** A file is one workflow graph. Opening it launches the visual editor.
4. **Add nodes** from the palette:
   - **HTTP Entry** — set `method` to `POST` and `path` to `/hello`. Optionally define a request schema such as `name: str`.
   - **Processor** — passes data through (or transforms it).
   - **Response** — the value returned to the caller.
5. **Connect** the nodes left to right. Edges carry each node's output into the next node's inputs.
6. **Save**, then click **Deploy**. The backend compiles the graph and registers `POST /hello`.
7. **Call it:**

   ```bash
   curl -X POST http://localhost:8000/hello \
     -H 'Content-Type: application/json' \
     -d '{"name": "world"}'
   ```

8. Open the file's **Logs** page to see the per-node execution trace.

Next steps:

- Browse the [node reference](node-reference.md) for the full list of nodes and fourteen example workflows (CRUD APIs, chatbots, RAG, agents, scheduled jobs).
- Try the [AI Agent Builder](agent-builder.md) to generate a workflow from a prompt.

## Local test databases

`test_dbs/docker-compose.yaml` starts throwaway MySQL (port `13306`) and PostgreSQL (port `15432`) instances for trying out database nodes:

```bash
docker compose -f test_dbs/docker-compose.yaml up -d
```

Both use user `appuser`, password `apppass`, database `dummytat`. From inside the backend container, reach them via `host.docker.internal`.

## Troubleshooting

| Symptom | Likely cause |
|---------|--------------|
| Backend exits with `Could not connect to the database after 10 attempts` | PostgreSQL isn't running or `DATABASE_URL` is wrong. Inside Compose the host is `postgres`; outside, `localhost`. |
| Every API call returns `401 Invalid auth token` | The backend's Clerk JWKS URL doesn't match the Clerk app your frontend uses. See [configuration.md](configuration.md#clerk-authentication). |
| `AI layer not fully available` warning on startup | An AI dependency failed to import. Reinstall `requirements.txt`. Non-AI nodes still work. |
| A deployed endpoint returns 404 after a restart | Deployed routes live in the backend process's memory. Re-deploy the workflow after restarting the backend. |
| Ollama models don't appear in the Agent Builder | `OLLAMA_BASE_URL` must be reachable from the backend; inside Docker use `http://host.docker.internal:11434`. |
| Frontend calls fail with CORS errors | The backend only allows `http://localhost:3000`. Edit `allow_origins` in `backend/app/main.py` if you serve the frontend elsewhere. |
