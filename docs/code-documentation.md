# SynthTeam — Code Documentation

## Directory Structure

```
SynthTeam/
├── docker-compose.yml
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py
│       ├── celery_worker.py
│       ├── core/
│       │   ├── config.py
│       │   └── auth.py
│       ├── db/
│       │   └── session.py
│       ├── models/
│       │   └── models.py
│       ├── api/
│       │   ├── routes.py
│       │   ├── projects.py              (CRUD + per-project OpenAPI endpoint)
│       │   └── files.py                 (CRUD + deploy/undeploy)
│       ├── utils/
│       │   ├── encryption.py            (API key encryption utilities)
│       │   └── rate_limiter.py          (Rate limiting for AI tools)
│       ├── db_connectors/               ← NEW: Multi-database abstraction
│       │   ├── __init__.py
│       │   ├── base.py                  (BaseConnector ABC)
│       │   ├── connector_registry.py    (CONNECTOR_REGISTRY)
│       │   ├── pool_manager.py          (Connection pooling)
│       │   ├── interpolation.py         (Variable interpolation engine)
│       │   ├── postgres_connector.py
│       │   ├── mysql_connector.py
│       │   ├── mongo_connector.py
│       │   ├── sqlite_connector.py
│       │   └── supabase_connector.py
│       ├── components/
│       │   ├── __init__.py              (auto-registers all components)
│       │   ├── base.py                  (BaseComponent ABC)
│       │   ├── component_registry.py    (COMPONENT_REGISTRY)
│       │   ├── db_base_mixin.py         (Shared DB node utilities)
│       │   │
│       │   ├── # Core nodes
│       │   ├── http_entry.py
│       │   ├── processor.py
│       │   ├── response_builder.py
│       │   │
│       │   ├── # Flow control nodes
│       │   ├── if_condition.py
│       │   ├── switch_case.py
│       │   ├── loop_foreach.py
│       │   ├── parallel_split.py
│       │   ├── merge_join.py
│       │   ├── delay.py
│       │   │
│       │   ├── # Trigger nodes
│       │   ├── cron_trigger.py
│       │   ├── webhook_trigger.py
│       │   ├── manual_trigger.py
│       │   │
│       │   ├── # Utility nodes
│       │   ├── header_extractor.py
│       │   ├── auth_node.py
│       │   ├── python_function.py
│       │   │
│       │   ├── # PostgreSQL nodes
│       │   ├── pg_find.py
│       │   ├── pg_insert.py
│       │   ├── pg_update.py
│       │   ├── pg_delete.py
│       │   ├── pg_raw_query.py
│       │   ├── pg_txn_start.py
│       │   ├── pg_txn_commit.py
│       │   ├── pg_txn_rollback.py
│       │   │
│       │   ├── # MySQL nodes
│       │   ├── mysql_find.py
│       │   ├── mysql_insert.py
│       │   ├── mysql_update.py
│       │   ├── mysql_delete.py
│       │   ├── mysql_raw_query.py
│       │   ├── mysql_txn_start.py
│       │   ├── mysql_txn_commit.py
│       │   ├── mysql_txn_rollback.py
│       │   │
│       │   ├── # MongoDB nodes
│       │   ├── mongo_find.py
│       │   ├── mongo_insert.py
│       │   ├── mongo_update.py
│       │   ├── mongo_delete.py
│       │   ├── mongo_aggregate.py
│       │   │
│       │   ├── # SQLite nodes
│       │   ├── sqlite_find.py
│       │   ├── sqlite_insert.py
│       │   ├── sqlite_update.py
│       │   ├── sqlite_delete.py
│       │   ├── sqlite_raw_query.py
│       │   │
│       │   ├── # Supabase nodes
│       │   ├── supa_find.py
│       │   ├── supa_insert.py
│       │   ├── supa_update.py
│       │   ├── supa_delete.py
│       │   ├── supa_raw_query.py
│       │   │
│       │   └── ai/                       ← NEW: AI/Agent components
│       │       ├── __init__.py
│       │       ├── llm_call.py
│       │       ├── embedding_generate.py
│       │       ├── vector_upsert.py
│       │       ├── vector_search.py
│       │       ├── vector_delete.py
│       │       ├── retrieval.py
│       │       ├── agent_run.py
│       │       ├── multi_agent.py
│       │       ├── autonomous_agent.py
│       │       ├── vision_analyze.py
│       │       ├── speech_to_text.py
│       │       └── text_to_speech.py
│       │
│       ├── ai/                           ← NEW: AI layer abstractions
│       │   ├── __init__.py
│       │   ├── llm/
│       │   │   ├── registry.py           (LLM_PROVIDER_REGISTRY)
│       │   │   ├── openai_provider.py
│       │   │   ├── anthropic_provider.py
│       │   │   ├── gemini_provider.py
│       │   │   ├── ollama_provider.py
│       │   │   ├── groq_provider.py
│       │   │   └── mistral_provider.py
│       │   ├── embeddings/
│       │   │   ├── registry.py           (EMBEDDING_REGISTRY)
│       │   │   ├── openai_embeddings.py
│       │   │   ├── ollama_embeddings.py
│       │   │   └── huggingface_embeddings.py
│       │   ├── vectorstores/
│       │   │   ├── registry.py           (VECTORSTORE_REGISTRY)
│       │   │   ├── qdrant_store.py
│       │   │   ├── pinecone_store.py
│       │   │   ├── weaviate_store.py
│       │   │   ├── chroma_store.py
│       │   │   └── supabase_vector.py
│       │   ├── tools/
│       │   │   ├── registry.py           (TOOL_REGISTRY)
│       │   │   ├── base.py               (SynthTool base class)
│       │   │   ├── web_search.py
│       │   │   ├── http_request.py
│       │   │   ├── calculator.py
│       │   │   ├── db_query.py
│       │   │   ├── code_executor.py
│       │   │   ├── file_ops.py
│       │   │   ├── email_sender.py
│       │   │   ├── slack_notifier.py
│       │   │   ├── workflow_invoker.py
│       │   │   └── composio_tools.py
│       │   ├── prompts/
│       │   │   └── template.py           (Jinja-style prompt rendering)
│       │   ├── output/
│       │   │   └── validator.py          (JSON schema validation)
│       │   ├── agents/
│       │   │   ├── react_agent.py        (ReAct agent with LangGraph)
│       │   │   └── autonomous_agent.py   (Planning & dynamic execution)
│       │   ├── memory/
│       │   │   ├── manager.py            (MemoryManager factory)
│       │   │   ├── in_memory.py
│       │   │   ├── redis_memory.py
│       │   │   └── vector_memory.py
│       │   ├── orchestration/
│       │   │   ├── multi_agent.py        (Sequential/collaborative)
│       │   │   └── hierarchical.py       (Supervisor delegation)
│       │   ├── vision/
│       │   │   ├── registry.py           (VISION_REGISTRY)
│       │   │   ├── openai_vision.py
│       │   │   ├── gemini_vision.py
│       │   │   └── ollama_vision.py
│       │   ├── speech/
│       │   │   ├── stt.py                (Speech-to-Text: Whisper, Deepgram)
│       │   │   └── tts.py                (Text-to-Speech: OpenAI, ElevenLabs)
│       │   ├── a2a/
│       │   │   ├── protocol.py           (A2AMessage, AgentCapability)
│       │   │   └── router.py             (Agent-to-Agent API endpoints)
│       │   └── observability/
│       │       └── tracker.py            (AITracker for metrics)
│       │
│       ├── runtime/
│       │   ├── compiler.py              (graph → execution plan + edge map)
│       │   ├── executor.py              (runs nodes with data flow)
│       │   └── registry.py              (component & route registries)
│       └── schemas/
│           └── user.py
│
└── frontend/
    ├── package.json
    ├── next.config.ts
    ├── tsconfig.json
    ├── components.json
    ├── proxy.ts                          (Clerk auth)
    ├── postcss.config.mjs
    ├── eslint.config.mjs
    ├── app/
    │   ├── layout.tsx
    │   ├── page.tsx
    │   ├── globals.css
    │   ├── dashboard/
    │   │   └── page.tsx
    │   ├── projects/
    │   │   └── [projectId]/
    │   │       └── page.tsx
    │   ├── files/
    │   │   └── [fileId]/
    │   │       └── page.tsx              (Flow Editor)
    │   ├── sign-in/
    │   │   └── [[...sign-in]]/
    │   │       └── page.tsx
    │   └── sign-up/
    │       └── [[...sign-up]]/
    │           └── page.tsx
    ├── components/
    │   ├── Navbar.tsx
    │   ├── CreateProjectModal.tsx
    │   ├── CreateFlowModal.tsx
    │   ├── SplineHero.tsx
    │   ├── ScrollReveal.tsx
    │   ├── OpenApiModal.tsx
    │   ├── nodes/
    │   │   ├── nodeTypes.ts              (Node type registry)
    │   │   ├── NodeWrapper.tsx
    │   │   ├── FieldModeInput.tsx        ← NEW: Static/Input/Expression toggle
    │   │   │
    │   │   ├── # Core nodes
    │   │   ├── HttpEntryNode.tsx
    │   │   ├── ProcessorNode.tsx
    │   │   ├── ResponseNode.tsx
    │   │   │
    │   │   ├── # Flow control nodes
    │   │   ├── IfConditionNode.tsx
    │   │   ├── SwitchCaseNode.tsx
    │   │   ├── LoopForEachNode.tsx
    │   │   ├── ParallelSplitNode.tsx
    │   │   ├── MergeJoinNode.tsx
    │   │   ├── DelayNode.tsx
    │   │   │
    │   │   ├── # Trigger nodes
    │   │   ├── WebhookTriggerNode.tsx
    │   │   ├── CronTriggerNode.tsx
    │   │   ├── ManualTriggerNode.tsx
    │   │   │
    │   │   ├── # Utility nodes
    │   │   ├── HeaderExtractorNode.tsx
    │   │   ├── AuthNodeNode.tsx
    │   │   ├── PythonFunctionNode.tsx
    │   │   │
    │   │   ├── db/                        ← Database node components
    │   │   │   ├── DBNodeFactory.tsx      (Factory for DB node UI)
    │   │   │   ├── PGFindNode.tsx
    │   │   │   ├── PGInsertNode.tsx
    │   │   │   ├── PGUpdateNode.tsx
    │   │   │   ├── PGDeleteNode.tsx
    │   │   │   ├── PGQueryNode.tsx
    │   │   │   ├── PGTxnStartNode.tsx
    │   │   │   ├── PGTxnCommitNode.tsx
    │   │   │   ├── PGTxnRollbackNode.tsx
    │   │   │   ├── MySQLFindNode.tsx
    │   │   │   ├── MySQLInsertNode.tsx
    │   │   │   ├── MySQLUpdateNode.tsx
    │   │   │   ├── MySQLDeleteNode.tsx
    │   │   │   ├── MySQLQueryNode.tsx
    │   │   │   ├── MySQLTxnStartNode.tsx
    │   │   │   ├── MySQLTxnCommitNode.tsx
    │   │   │   ├── MySQLTxnRollbackNode.tsx
    │   │   │   ├── MongoFindNode.tsx
    │   │   │   ├── MongoInsertNode.tsx
    │   │   │   ├── MongoUpdateNode.tsx
    │   │   │   ├── MongoDeleteNode.tsx
    │   │   │   ├── MongoAggregateNode.tsx
    │   │   │   ├── SQLiteFindNode.tsx
    │   │   │   ├── SQLiteInsertNode.tsx
    │   │   │   ├── SQLiteUpdateNode.tsx
    │   │   │   ├── SQLiteDeleteNode.tsx
    │   │   │   ├── SQLiteQueryNode.tsx
    │   │   │   ├── SupaFindNode.tsx
    │   │   │   ├── SupaInsertNode.tsx
    │   │   │   ├── SupaUpdateNode.tsx
    │   │   │   ├── SupaDeleteNode.tsx
    │   │   │   └── SupaQueryNode.tsx
    │   │   │
    │   │   └── ai/                        ← AI/Agent node components
    │   │       ├── AINodeFactory.tsx      (Factory for AI node UI)
    │   │       ├── LLMCallNode.tsx
    │   │       ├── EmbeddingNode.tsx
    │   │       ├── VectorUpsertNode.tsx
    │   │       ├── VectorSearchNode.tsx
    │   │       ├── VectorDeleteNode.tsx
    │   │       ├── RetrievalNode.tsx
    │   │       ├── AgentRunNode.tsx
    │   │       ├── MultiAgentNode.tsx
    │   │       ├── AutonomousAgentNode.tsx
    │   │       ├── VisionNode.tsx
    │   │       ├── STTNode.tsx
    │   │       └── TTSNode.tsx
    │   │
    │   ├── edges/
    │   │   └── DeletableEdge.tsx
    │   └── ui/
    │       └── (shadcn components)
    ├── lib/
    │   └── utils.ts
    └── public/
        └── (static assets)
```

---

## Architecture Overview

SynthTeam is a **visual API & workflow builder** — users design pipelines by connecting nodes in a ReactFlow graph editor, then deploy them as live endpoints. The platform now supports:

- **Multi-database operations** (PostgreSQL, MySQL, MongoDB, SQLite, Supabase)
- **AI/Agent workflows** (LLMs, embeddings, vector stores, RAG, autonomous agents)
- **Flow control** (conditionals, loops, parallel execution)
- **Observability** (execution logs, AI metrics tracking)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          WORKFLOW PIPELINE                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐             │
│  │  HTTP Entry  │────▶│  DB Node     │────▶│  LLM Call    │             │
│  │  (trigger)   │     │  (postgres)  │     │  (openai)    │             │
│  └──────────────┘     └──────────────┘     └──────────────┘             │
│                              │                    │                      │
│                              ▼                    ▼                      │
│                       ┌──────────────┐     ┌──────────────┐             │
│                       │  If Condition│     │  Agent Run   │             │
│                       │  (branch)    │     │  (ReAct)     │             │
│                       └──────────────┘     └──────────────┘             │
│                              │                    │                      │
│                              ▼                    ▼                      │
│                       ┌──────────────────────────────────┐              │
│                       │        Response Builder           │              │
│                       │        (final output)             │              │
│                       └──────────────────────────────────┘              │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Component Categories

### Node Type Registry

| Category | Frontend Node Types | Backend Components |
|----------|--------------------|--------------------|
| **Core** | `http_entry`, `processor`, `response_builder` | HttpEntryComponent, EchoProcessorComponent, ResponseBuilderComponent |
| **Flow Control** | `if_condition`, `switch_case`, `loop_foreach`, `parallel_split`, `merge_join`, `delay` | IfConditionComponent, SwitchCaseComponent, LoopForEachComponent, ParallelSplitComponent, MergeJoinComponent, DelayComponent |
| **Triggers** | `cron_trigger`, `webhook_trigger`, `manual_trigger` | CronTriggerComponent, WebhookTriggerComponent, ManualTriggerComponent |
| **Utilities** | `header_extractor`, `auth_node`, `python_function` | HeaderExtractorComponent, AuthNodeComponent, PythonFunctionComponent |
| **PostgreSQL** | `pg_find`, `pg_insert`, `pg_update`, `pg_delete`, `pg_raw_query`, `pg_txn_*` | PGFindComponent, PGInsertComponent, etc. |
| **MySQL** | `mysql_find`, `mysql_insert`, `mysql_update`, `mysql_delete`, `mysql_raw_query`, `mysql_txn_*` | MySQLFindComponent, MySQLInsertComponent, etc. |
| **MongoDB** | `mongo_find`, `mongo_insert`, `mongo_update`, `mongo_delete`, `mongo_aggregate` | MongoFindComponent, MongoInsertComponent, etc. |
| **SQLite** | `sqlite_find`, `sqlite_insert`, `sqlite_update`, `sqlite_delete`, `sqlite_raw_query` | SQLiteFindComponent, SQLiteInsertComponent, etc. |
| **Supabase** | `supa_find`, `supa_insert`, `supa_update`, `supa_delete`, `supa_raw_query` | SupaFindComponent, SupaInsertComponent, etc. |
| **AI/LLM** | `llm_call`, `embedding_generate` | LLMCallComponent, EmbeddingGenerateComponent |
| **Vector DB** | `vector_upsert`, `vector_search`, `vector_delete`, `retrieval` | VectorUpsertComponent, VectorSearchComponent, VectorDeleteComponent, RetrievalComponent |
| **Agents** | `agent_run`, `multi_agent_orchestrator`, `autonomous_agent` | AgentRunComponent, MultiAgentComponent, AutonomousAgentComponent |
| **Vision & Speech** | `vision_analyze`, `speech_to_text`, `text_to_speech` | VisionAnalyzeComponent, SpeechToTextComponent, TextToSpeechComponent |

---

## Docker Compose

### `docker-compose.yml`

Orchestrates four services: **Postgres**, **Redis**, **Backend (FastAPI)**, and **Celery worker**.

```yaml
version: "3.9"

services:
  postgres:
    image: postgres:15
    container_name: synthteam_postgres
    restart: always
    environment:
      POSTGRES_USER: synthuser
      POSTGRES_PASSWORD: synthpass
      POSTGRES_DB: synthdb
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U synthuser -d synthdb"]
      interval: 3s
      timeout: 3s
      retries: 10

  redis:
    image: redis:7
    container_name: synthteam_redis
    restart: always
    ports:
      - "6379:6379"

  backend:
    build: ./backend
    container_name: synthteam_backend
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    volumes:
      - ./backend:/app
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started
    env_file:
      - ./backend/.env

  celery:
    build: ./backend
    container_name: synthteam_celery
    command: celery -A app.celery_worker worker --loglevel=info
    volumes:
      - ./backend:/app
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started
    env_file:
      - ./backend/.env

volumes:
  postgres_data:
```

---

## Backend (FastAPI + SQLAlchemy + Celery)

### `backend/app/main.py`

Entry point. Sets up CORS, registers routers, creates DB tables on startup, and auto-registers all pipeline components and AI providers.

**Startup sequence:**

1. Retry DB connection 10 times → create tables
2. Import `app.components` → triggers component auto-registration
3. Import `app.db_connectors` → registers all DB connectors
4. Import `app.ai` → registers LLM providers, embedding models, vector stores, and tools
5. Include A2A router for agent-to-agent communication

---

### Variable Interpolation System

The `backend/app/db_connectors/interpolation.py` module provides a unified system for resolving dynamic values across all components.

**Three input modes:**

| Mode | Description | Example Value | Resolution |
|------|-------------|---------------|------------|
| `static` | Literal value, used as-is | `"hello"` | Returns `"hello"` |
| `input` | Flat key lookup from upstream context | `"user_id"` | Returns `context.get("user_id")` |
| `expression` | Dot-path/bracket traversal | `"data.users[0].name"` | Returns `context["data"]["users"][0]["name"]` |

**Special handling:**
- If the value is just `"input"` in either `input` or `expression` mode, the entire upstream context is returned
- Supports Jinja-style `{{variable}}` syntax in templates

```python
def resolve_field_mapping(mapping: dict, context: dict) -> Any:
    mode = mapping.get("mode", "expression")
    value = mapping.get("value", "")

    if mode == "static":
        return value
    elif mode == "input":
        key = value.strip()
        if not key or key == "input":
            return context  # Return entire context
        return context.get(key)
    elif mode == "expression":
        return evaluate_expression(value, context)
```

---

### `backend/app/components/` — Pipeline Node Implementations

#### `base.py` — Abstract Base Class

```python
from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseComponent(ABC):
    @abstractmethod
    async def execute(
        self,
        request_data: dict,   # Original HTTP request body
        inputs: Dict[str, Any],  # { parent_node_id: parent_output, ... }
        config: dict,           # This node's config from graph JSON
    ) -> Any:
        ...
```

#### `db_base_mixin.py` — Database Node Utilities

All database nodes inherit from `DBNodeMixin` which provides:

- `_get_connector()` — Creates a connector from UUID or URI
- `_resolve_filters()` — Processes filter mappings with mode support
- `_uri_to_credentials()` — Parses connection URIs

```python
class DBNodeMixin:
    CONNECTOR_TYPE: str = ""  # Override in subclass

    async def _get_connector(self, config: dict, context: dict):
        conn_id = config.get("connection_id", "")
        uri = config.get("uri", "")
        
        if uri:
            creds = self._uri_to_credentials(uri, config.get("database"))
            return await get_or_create_connector(self.CONNECTOR_TYPE, **creds)
        else:
            return await get_connector_by_id(conn_id)
```

---

### Database Connectors

#### `backend/app/db_connectors/base.py`

```python
from abc import ABC, abstractmethod

class BaseConnector(ABC):
    @abstractmethod
    async def connect(self): ...
    
    @abstractmethod
    async def disconnect(self): ...
    
    @abstractmethod
    async def execute(self, query: str, params: dict = None): ...
    
    @abstractmethod
    async def find(self, table: str, filters: dict, options: dict = None): ...
    
    @abstractmethod
    async def insert(self, table: str, data: dict): ...
    
    @abstractmethod
    async def update(self, table: str, filters: dict, data: dict): ...
    
    @abstractmethod
    async def delete(self, table: str, filters: dict): ...
```

#### Supported Databases

| Connector | Driver | Features |
|-----------|--------|----------|
| PostgreSQL | `asyncpg` | Transactions, raw queries, CRUD |
| MySQL | `aiomysql` | Transactions, raw queries, CRUD |
| MongoDB | `motor` | Aggregation pipeline, CRUD |
| SQLite | `aiosqlite` | Raw queries, CRUD |
| Supabase | `asyncpg` | Raw queries, CRUD (PostgreSQL-based) |

---

### Flow Control Components

#### `if_condition.py`

```python
class IfConditionComponent(BaseComponent):
    async def execute(self, request_data, inputs, config) -> dict:
        field_value = resolve_field_mapping(config.get("field", {}), context)
        compare_value = resolve_field_mapping(config.get("value", {}), context)
        operator = config.get("operator", "==")
        
        result = self._compare(field_value, compare_value, operator)
        return {
            "condition_met": result,
            "branch": "true" if result else "false",
            **context
        }
```

Supported operators: `==`, `!=`, `>`, `<`, `>=`, `<=`, `contains`, `not_contains`, `starts_with`, `ends_with`, `is_empty`, `is_not_empty`

#### `loop_foreach.py`

Iterates over an array field and executes downstream nodes for each item:

```python
class LoopForEachComponent(BaseComponent):
    async def execute(self, request_data, inputs, config) -> dict:
        array = resolve_field_mapping(config.get("array_field", {}), context)
        return {
            "loop_items": array,
            "loop_index": 0,
            "loop_current": array[0] if array else None,
            "loop_length": len(array)
        }
```

#### `parallel_split.py` / `merge_join.py`

- **Parallel Split**: Duplicates data to multiple branches
- **Merge Join**: Collects outputs from parallel branches, supports `all`, `any`, `first` strategies

---

## AI Layer

### LLM Provider Registry

```
backend/app/ai/llm/
├── registry.py          # LLM_PROVIDER_REGISTRY, get_llm()
├── openai_provider.py   # ChatOpenAI
├── anthropic_provider.py # ChatAnthropic
├── gemini_provider.py   # ChatGoogleGenerativeAI
├── ollama_provider.py   # ChatOllama
├── groq_provider.py     # ChatGroq
└── mistral_provider.py  # ChatMistralAI
```

**Usage:**

```python
from app.ai.llm.registry import get_llm

llm = get_llm(
    provider="openai",
    model="gpt-4",
    temperature=0.7,
    api_key="sk-..."
)
response = await llm.ainvoke([HumanMessage(content="Hello")])
```

### Embedding Registry

```
backend/app/ai/embeddings/
├── registry.py              # EMBEDDING_REGISTRY, get_embeddings()
├── openai_embeddings.py     # OpenAIEmbeddings
├── ollama_embeddings.py     # OllamaEmbeddings
└── huggingface_embeddings.py # HuggingFaceEmbeddings
```

### Vector Store Registry

```
backend/app/ai/vectorstores/
├── registry.py          # VECTORSTORE_REGISTRY
├── qdrant_store.py      # QdrantClient
├── pinecone_store.py    # Pinecone
├── weaviate_store.py    # weaviate.connect_to_local
├── chroma_store.py      # chromadb.HttpClient
└── supabase_vector.py   # SupabaseVectorStore
```

### Tool Registry

```
backend/app/ai/tools/
├── registry.py          # TOOL_REGISTRY, @register_tool
├── base.py              # SynthTool(BaseTool)
├── web_search.py        # Tavily web search
├── http_request.py      # HTTP GET/POST/PUT/DELETE
├── calculator.py        # Safe math evaluation
├── db_query.py          # DB-specific query tools
├── code_executor.py     # Sandboxed Python execution
├── file_ops.py          # File read/write
├── email_sender.py      # SMTP email
├── slack_notifier.py    # Slack webhooks
├── workflow_invoker.py  # Call other workflows
└── composio_tools.py    # Composio integration
```

**Registering a custom tool:**

```python
from app.ai.tools.registry import register_tool
from app.ai.tools.base import SynthTool

@register_tool("my_tool")
class MyTool(SynthTool):
    name = "my_tool"
    description = "Does something useful"
    
    def _run(self, input: str) -> str:
        return f"Processed: {input}"
```

### Agent Execution

#### ReAct Agent (`backend/app/ai/agents/react_agent.py`)

Uses LangGraph's `create_react_agent` for reasoning and tool use:

```python
async def run_react_agent(
    llm,
    tools: list,
    messages: list,
    max_iterations: int = 10
) -> dict:
    agent = create_react_agent(llm, tools)
    result = await agent.ainvoke({"messages": messages})
    return {
        "output": result["messages"][-1].content,
        "reasoning_trace": [m.dict() for m in result["messages"]]
    }
```

#### Multi-Agent Orchestration

**Sequential strategy**: Agents run one after another, each receiving the previous output.

**Collaborative strategy**: All agents receive the same input, outputs are merged.

```python
async def run_multi_agent(
    agents: list[dict],
    input_data: dict,
    strategy: str = "sequential"
) -> dict:
    if strategy == "sequential":
        return await _run_sequential(agents, input_data)
    else:
        return await _run_collaborative(agents, input_data)
```

### Memory System

```
backend/app/ai/memory/
├── manager.py       # MemoryManager factory
├── in_memory.py     # Dict-based memory
├── redis_memory.py  # Redis-backed memory
└── vector_memory.py # Semantic vector memory
```

```python
from app.ai.memory.manager import MemoryManager

memory = MemoryManager.create(
    backend="redis",
    session_id="user-123",
    redis_url="redis://localhost:6379"
)

await memory.add("user", "Hello")
await memory.add("assistant", "Hi there!")
history = await memory.get_history()
```

### Vision & Speech

#### Vision Providers

| Provider | Model | Input |
|----------|-------|-------|
| OpenAI | `gpt-4-vision-preview` | image_url or base64 |
| Gemini | `gemini-pro-vision` | image_url or base64 |
| Ollama | `llava` | image_url or base64 |

#### Speech-to-Text

| Provider | Implementation |
|----------|----------------|
| OpenAI Whisper | `openai.audio.transcriptions.create()` |
| Deepgram | `deepgram-sdk` |

#### Text-to-Speech

| Provider | Implementation |
|----------|----------------|
| OpenAI TTS | `openai.audio.speech.create()` |
| ElevenLabs | `elevenlabs` package |

### Agent-to-Agent Protocol

REST API for inter-agent communication:

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/agents/` | List all registered agents |
| GET | `/api/agents/{id}/capabilities` | Get agent's available tools |
| POST | `/api/agents/{id}/message` | Send message to agent |

**Message schema:**

```python
class A2AMessage(BaseModel):
    sender_id: str
    content: str
    context: dict = {}
    require_response: bool = True
```

### AI Observability

The `AITracker` class logs metrics for every AI node execution:

```python
tracker = AITracker()
tracker.start()

# ... AI operation ...

tracker.record(
    model="gpt-4",
    tokens_used={"prompt": 100, "completion": 50},
    tools_called=["web_search", "calculator"]
)

metrics = tracker.finish()
# Returns: { model, tokens_used, latency_ms, tools_called, errors }
```

---

## AI Components (Workflow Nodes)

### `llm_call` — LLM Invocation

```python
class LLMCallComponent(BaseComponent):
    async def execute(self, request_data, inputs, config) -> dict:
        llm = get_llm(
            provider=config["provider"],
            model=config["model"],
            temperature=config.get("temperature", 0.7),
            api_key=config["api_key"]
        )
        
        prompt = render_prompt(config["prompt_template"], context)
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        
        return {
            "response": response.content,
            "model": config["model"],
            "tokens_used": response.usage_metadata
        }
```

### `embedding_generate` — Generate Embeddings

```python
class EmbeddingGenerateComponent(BaseComponent):
    async def execute(self, request_data, inputs, config) -> dict:
        embedder = get_embeddings(config["provider"], config["api_key"])
        text = resolve_field_mapping(config["text"], context)
        vector = await embedder.aembed_query(text)
        
        return {"embedding": vector, "dimensions": len(vector)}
```

### `retrieval` — RAG Pipeline

```python
class RetrievalComponent(BaseComponent):
    async def execute(self, request_data, inputs, config) -> dict:
        # 1. Generate query embedding
        embedder = get_embeddings(config["embedding_provider"], config["api_key"])
        query_vector = await embedder.aembed_query(query)
        
        # 2. Search vector store
        store = get_vectorstore(config["vectorstore_type"], config["vectorstore_config"])
        results = await store.search(query_vector, top_k=config.get("top_k", 5))
        
        return {
            "documents": results,
            "query": query,
            "source_count": len(results)
        }
```

### `agent_run` — ReAct Agent

```python
class AgentRunComponent(BaseComponent):
    async def execute(self, request_data, inputs, config) -> dict:
        llm = get_llm(config["provider"], config["model"], config["api_key"])
        tools = get_tools(config.get("tools", []))
        
        result = await run_react_agent(
            llm=llm,
            tools=tools,
            messages=[HumanMessage(content=config["goal"])],
            max_iterations=config.get("max_iterations", 10)
        )
        
        return result
```

---

## Frontend

### Tech Stack

| Library | Version | Purpose |
|---------|---------|---------|
| Next.js | 16.x | React framework |
| React | 19.x | UI library |
| @clerk/nextjs | ^6.x | Authentication |
| reactflow | ^11.x | Node/edge graph editor |
| shadcn/ui | latest | UI components |
| Tailwind CSS | v4 | Styling |
| zustand | ^5.x | State management |
| lucide-react | latest | Icons |

### Component Palette (Flow Editor)

The left sidebar in the flow editor organizes nodes into categories:

| Section | Color | Nodes |
|---------|-------|-------|
| Triggers | Blue | HTTP Entry, Webhook, Cron, Manual |
| Logic | Amber | Processor, If Condition, Switch Case, Loop ForEach |
| Flow Control | Orange | Parallel Split, Merge Join, Delay |
| Utilities | Cyan | Header Extractor, Auth, Python Function |
| PostgreSQL | Emerald | Find, Insert, Update, Delete, Query, Txn Start/Commit/Rollback |
| MySQL | Yellow | Find, Insert, Update, Delete, Query, Txn Start/Commit/Rollback |
| MongoDB | Green | Find, Insert, Update, Delete, Aggregate |
| SQLite | Slate | Find, Insert, Update, Delete, Query |
| Supabase | Violet | Find, Insert, Update, Delete, Query |
| AI/LLM | Purple | LLM Call, Embedding Generate |
| Embeddings & RAG | Indigo | Vector Upsert, Vector Search, Vector Delete, Retrieval |
| Agents | Rose | Agent Run, Multi-Agent, Autonomous Agent |
| Vision & Speech | Teal | Vision Analyze, Speech-to-Text, Text-to-Speech |
| Output | Emerald | Response Builder |

### `FieldModeInput` Component

Reusable component for toggling between Static, Input, and Expression modes:

```typescript
interface FieldModeInputProps {
  mode: "static" | "input" | "expression";
  value: string;
  onModeChange: (mode: FieldMode) => void;
  onValueChange: (value: string) => void;
  placeholder?: string;
}

export default function FieldModeInput({
  mode, value, onModeChange, onValueChange, placeholder
}: FieldModeInputProps) {
  return (
    <div className="flex gap-1">
      {/* Mode toggle buttons */}
      <button onClick={() => onModeChange("static")}>S</button>
      <button onClick={() => onModeChange("input")}>I</button>
      <button onClick={() => onModeChange("expression")}>E</button>
      
      {/* Value input */}
      <input
        value={value}
        onChange={(e) => onValueChange(e.target.value)}
        placeholder={mode === "static" ? "literal value" : 
                     mode === "input" ? "field_name" : 
                     "data.users[0].name"}
      />
    </div>
  );
}
```

### Node Configuration Examples

#### LLM Call Node Config

```json
{
  "provider": "openai",
  "model": "gpt-4",
  "api_key": "sk-...",
  "temperature": 0.7,
  "prompt_template": "Summarize: {{input.text}}",
  "system_prompt": "You are a helpful assistant.",
  "output_schema": {
    "summary": "string",
    "key_points": "array"
  }
}
```

#### Agent Run Node Config

```json
{
  "provider": "openai",
  "model": "gpt-4",
  "api_key": "sk-...",
  "goal": "Research and summarize {{input.topic}}",
  "tools": ["web_search", "calculator"],
  "max_iterations": 10,
  "memory_backend": "redis",
  "memory_session_id": "{{input.session_id}}"
}
```

#### MongoDB Find Node Config

```json
{
  "uri": "mongodb+srv://user:pass@cluster.mongodb.net/mydb",
  "database": "mydb",
  "collection": "users",
  "filter_mappings": [
    { "field": "email", "mode": "input", "value": "user_email" },
    { "field": "status", "mode": "static", "value": "active" }
  ],
  "limit": 10
}
```

---

## Runtime System

### Graph Compiler (`backend/app/runtime/compiler.py`)

Transforms ReactFlow graph into execution plan:

1. `_build_adjacency()` — Adjacency list + in-degree map
2. `_build_edge_map()` — Reverse adjacency: `{ target: [sources] }`
3. `_topological_sort()` — Kahn's algorithm (raises on cycles)
4. `_build_execution_plan()` — Maps sorted IDs to node configs
5. `_create_schema_model()` — Dynamic Pydantic models

**Output:**

```python
{
    "method": "POST",
    "path": "/api/custom/...",
    "request_model": <DynamicPydanticModel>,
    "response_model": <DynamicPydanticModel>,
    "ordered_nodes": [{ "id", "component", "config" }, ...],
    "edge_map": { "target_id": ["source_id_1", ...] }
}
```

### Graph Executor (`backend/app/runtime/executor.py`)

Runs nodes in topological order with data flow:

```python
class GraphExecutor:
    async def execute(self, request_data: dict) -> Any:
        context = {}  # node_id → output
        
        for node in self.ordered_nodes:
            # Gather inputs from parent nodes
            parent_ids = self.edge_map.get(node["id"], [])
            inputs = {pid: context[pid] for pid in parent_ids}
            
            # Execute component
            component = get_component(node["component"])
            result = await component.execute(request_data, inputs, node["config"])
            
            # JSON sanitization
            result = _to_json_safe(result)
            
            context[node["id"]] = result
        
        return context[self.ordered_nodes[-1]["id"]]
```

**JSON Sanitization:**

The executor applies `_to_json_safe()` to all node outputs, converting:
- `datetime` → ISO string
- `UUID` → string
- `ObjectId` → string
- `bytes` → UTF-8 string
- `Decimal` → float

---

## API Endpoints

### Core Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/` | Public | Health check |
| GET | `/protected` | Required | Returns JWT payload |

### Project Management

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/projects` | Required | Create project |
| GET | `/api/projects` | Required | List user's projects |
| PUT | `/api/projects/{id}` | Required | Rename project |
| DELETE | `/api/projects/{id}` | Required | Delete project |
| GET | `/api/projects/{id}/openapi` | Required | Project-specific OpenAPI spec |

### File/Workflow Management

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/files` | Required | Create file |
| GET | `/api/files/project/{project_id}` | Required | List files in project |
| GET | `/api/files/{file_id}/meta` | Required | Get file metadata |
| GET | `/api/files/{file_id}` | Required | Get file's graph JSON |
| PUT | `/api/files/{file_id}` | Required | Update graph data |
| DELETE | `/api/files/{file_id}` | Required | Delete file |
| POST | `/api/files/deploy/{file_id}` | Required | Deploy workflow |
| POST | `/api/files/undeploy/{file_id}` | Required | Undeploy workflow |

### Agent-to-Agent (A2A)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/agents/` | Optional | List registered agents |
| GET | `/api/agents/{id}/capabilities` | Optional | Agent's tool capabilities |
| POST | `/api/agents/{id}/message` | Optional | Send message to agent |

---

## Data Flow Example

### End-to-End: HTTP → MongoDB → LLM → Response

```
1. HTTP Entry receives POST /api/analyze
   Input: { "user_id": "123", "question": "What are my orders?" }
   Output: { user_id: "123", question: "What are my orders?" }

2. MongoDB Find queries orders collection
   Config: { collection: "orders", filter: { user_id: "{{input.user_id}}" } }
   Output: { orders: [{ id: 1, item: "Widget", qty: 5 }, ...] }

3. LLM Call summarizes the orders
   Config: { 
     provider: "openai", 
     model: "gpt-4",
     prompt: "Summarize these orders for the user: {{input.orders}}"
   }
   Output: { response: "You have 3 orders totaling $150...", tokens_used: 120 }

4. Response Builder shapes final output
   Config: { 
     field_mappings: [
       { name: "summary", source: "input", value: "response" },
       { name: "order_count", source: "expression", value: "orders.length" }
     ]
   }
   Output: { summary: "You have 3 orders...", order_count: 3 }
```

---

## Running the Project

```bash
# 1. Start backend services (Postgres, Redis, FastAPI, Celery)
docker compose up --build

# 2. Start frontend (in a separate terminal)
cd frontend
npm install
npm run dev
```

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Postgres**: localhost:5432
- **Redis**: localhost:6379

---

## Environment Variables

### Backend (`backend/.env`)

```env
DATABASE_URL=postgresql+asyncpg://synthuser:synthpass@postgres:5432/synthdb
REDIS_URL=redis://redis:6379/0

# Clerk Authentication
CLERK_SECRET_KEY=sk_test_...
CLERK_PUBLISHABLE_KEY=pk_test_...

# Optional: Default AI API keys (can be overridden per-node)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

### Frontend (`frontend/.env.local`)

```env
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Security Considerations

1. **API Keys**: Passed directly in node configs, masked in UI with `type="password"`
2. **SQL Injection**: Parameterized queries used in all DB connectors
3. **Code Execution**: Python function node runs in subprocess with timeout
4. **Rate Limiting**: AI tools support rate limiting via `rate_limiter.py`
5. **Authentication**: All non-public routes require Clerk JWT validation
