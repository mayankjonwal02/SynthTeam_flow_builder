# Configuration

SynthTeam reads its configuration from environment variables. Templates are provided in `backend/.env.example` and `frontend/.env.example`; copy them to `backend/.env` and `frontend/.env.local`. Both real files are git-ignored.

## Backend (`backend/.env`)

Loaded by `backend/app/core/config.py` (pydantic-settings) and, under Docker Compose, through `env_file`.

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | yes | — | SQLAlchemy async URL for the application database, e.g. `postgresql+asyncpg://synthuser:synthpass@postgres:5432/synthdb` |
| `REDIS_URL` | yes | — | Redis URL used for rate limiting, Celery and Redis-backed memory, e.g. `redis://redis:6379/0` |
| `CLERK_SECRET_KEY` | yes | — | Clerk secret key |
| `CLERK_PUBLISHABLE_KEY` | yes | — | Clerk publishable key |
| `CLERK_JWKS_URL` | yes in practice | the original developer's Clerk instance | JWKS endpoint used to verify Clerk session tokens: `https://<your-instance>.clerk.accounts.dev/.well-known/jwks.json` |
| `ENCRYPTION_KEY` | yes in practice | placeholder | Fernet key that encrypts saved database credentials. **Set a real key before storing any connection**; changing it later makes existing credentials unreadable. |
| `GROQ_API_KEY` | no | empty | Default Groq key, used when a node or Agent Builder session doesn't supply one |
| `OLLAMA_BASE_URL` | no | `http://localhost:11434` | Ollama server for local LLMs, embeddings and vision. In Docker use `http://host.docker.internal:11434`. |
| `AI_MEMORY_DEFAULT_MAX_MESSAGES` | no | `200` | Default history cap for conversation memory |
| `AGENT_BUILDER_CONTEXT_MESSAGES` | no | `60` | How many past messages the Agent Builder keeps in context |

Generate an encryption key:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### Provider API keys

Most AI nodes take their API key in the node config (an **LLM Model** node, for example). You can also set the standard environment variables, which the underlying LangChain/SDK clients pick up when no key is supplied:

`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, `GROQ_API_KEY`, `MISTRAL_API_KEY`, `TAVILY_API_KEY`, `DEEPGRAM_API_KEY`, `ELEVENLABS_API_KEY`, `PINECONE_API_KEY`.

## Frontend (`frontend/.env.local`)

| Variable | Required | Description |
|----------|----------|-------------|
| `NEXT_PUBLIC_API_URL` | yes | Backend base URL **as seen from the browser**, e.g. `http://localhost:8000` |
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | yes | Clerk publishable key |
| `CLERK_SECRET_KEY` | yes | Clerk secret key, used by the Next.js server-side middleware (`proxy.ts`) |

Docker Compose sets `NEXT_PUBLIC_API_URL=http://localhost:8000` and `WATCHPACK_POLLING=true` for the frontend container.

## Clerk authentication

1. Create an application at https://dashboard.clerk.com.
2. Copy the publishable and secret keys into both env files.
3. Point the backend at your instance's JWKS endpoint in `backend/.env`:

   ```env
   CLERK_JWKS_URL=https://<your-instance>.clerk.accounts.dev/.well-known/jwks.json
   ```

   The URL is shown under **API keys → Show JWT public key / JWKS URL** in the Clerk dashboard.

   The backend validates every protected request's `Authorization: Bearer <token>` against these keys (RS256, expiry checked, keys cached for one hour).

Public frontend routes are `/`, `/sign-in`, `/sign-up` and `/sso-callback`; everything else redirects to sign-in when logged out.

## Ollama (local models)

1. Install Ollama and pull a model: `ollama pull llama3.1:8b` (the Agent Builder's default model).
2. Set `OLLAMA_BASE_URL` so the backend can reach it. From the Compose backend container, that's `http://host.docker.internal:11434`.
3. `GET /agent/ollama/models` lists the models the backend can see.

## Docker Compose defaults

The bundled `docker-compose.yml` is meant for **local development**: the database password is hard-coded, ports are published on all interfaces and the backend runs with `--reload`. For any shared deployment, change the credentials, drop `--reload`, and run the frontend with `npm run build && npm start`.

## CORS

`backend/app/main.py` allows only `http://localhost:3000`. Add your frontend's origin to `allow_origins` when hosting it elsewhere.
