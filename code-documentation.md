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
│       ├── components/
│       │   ├── __init__.py              (auto-registers all components)
│       │   ├── base.py                  (BaseComponent ABC)
│       │   ├── http_entry.py            (HTTP Entry component)
│       │   ├── processor.py             (Echo Processor component)
│       │   └── response_builder.py      (Response Builder component)
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
    ├── proxy.ts                          (Clerk auth — replaces middleware.ts in Next.js 16)
    ├── postcss.config.mjs
    ├── eslint.config.mjs
    ├── app/
    │   ├── layout.tsx                    (ClerkProvider + TooltipProvider + Toaster)
    │   ├── page.tsx                      (Landing page with Spline 3D hero)
    │   ├── globals.css                   (Tailwind + marquee + Spline watermark hide)
    │   ├── dashboard/
    │   │   └── page.tsx
    │   ├── projects/
    │   │   └── [projectId]/
    │   │       └── page.tsx              (Project detail + OpenAPI modal)
    │   ├── files/
    │   │   └── [fileId]/
    │   │       └── page.tsx              (Flow Editor — full rewrite)
    │   ├── builder/
    │   │   └── page.tsx
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
    │   ├── SplineHero.tsx                ← NEW (scroll-animated 3D hero)
    │   ├── ScrollReveal.tsx              ← NEW (Intersection Observer fade-up)
    │   ├── OpenApiModal.tsx              ← NEW (project OpenAPI JSON viewer)
    │   ├── nodes/
    │   │   ├── nodeTypes.ts
    │   │   ├── NodeWrapper.tsx             (delete button + editable name overlay)
    │   │   ├── HttpEntryNode.tsx           (request & response schema builder)
    │   │   ├── ProcessorNode.tsx           (echo merge, NodeWrapper-wrapped)
    │   │   └── ResponseNode.tsx            (field mappings with input/static toggle)
    │   ├── edges/
    │   │   └── DeletableEdge.tsx           (custom edge with delete button on select)
    │   └── ui/
    │       ├── avatar.tsx
    │       ├── badge.tsx
    │       ├── button.tsx
    │       ├── card.tsx
    │       ├── dialog.tsx
    │       ├── dropdown-menu.tsx
    │       ├── input.tsx
    │       ├── label.tsx
    │       ├── scroll-area.tsx
    │       ├── select.tsx
    │       ├── separator.tsx
    │       ├── sheet.tsx
    │       ├── sonner.tsx                 (toast notifications)
    │       ├── tabs.tsx
    │       └── tooltip.tsx
    ├── lib/
    │   └── utils.ts
    └── public/
        ├── file.svg
        ├── globe.svg
        ├── next.svg
        ├── vercel.svg
        └── window.svg
```

---

## Architecture Overview

SynthTeam is a **visual API builder** — users design API pipelines by connecting nodes in a ReactFlow graph editor, then deploy them as live endpoints.

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│  HTTP Entry  │────▶│  Processor   │────▶│  Response Builder│
│  (blue)      │     │  (amber)     │     │  (green)         │
│              │     │              │     │                  │
│ Method: POST │     │ Merges       │     │ Shapes output to │
│ Path: /api/… │     │ upstream     │     │ declared schema  │
│ Schema: {…}  │     │ data         │     │                  │
└─────────────┘     └──────────────┘     └─────────────────┘
```

**Frontend ↔ Backend Node Mapping:**

| Frontend Node Type  | Frontend Component   | Backend Component Class      | Backend Registry Name  |
|--------------------|--------------------- |------------------------------|------------------------|
| `http_entry`       | `HttpEntryNode.tsx`  | `HttpEntryComponent`         | `http_entry`           |
| `processor`        | `ProcessorNode.tsx`  | `EchoProcessorComponent`     | `processor`, `echo_processor` |
| `response_builder` | `ResponseNode.tsx`   | `ResponseBuilderComponent`   | `response_builder`     |

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

Entry point. Sets up CORS, registers routers, creates DB tables on startup with retry logic, and auto-registers all pipeline components.

```python
import asyncio
import logging

from fastapi import FastAPI
from app.api.routes import router
from fastapi.middleware.cors import CORSMiddleware
from app.api.projects import router as project_router
from app.api.files import router as file_router
from app.models.models import Base
from app.db.session import engine

logger = logging.getLogger("uvicorn.error")

app = FastAPI(title="SynthTeam API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def create_tables():
    for attempt in range(1, 11):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created successfully.")
            break
        except Exception as e:
            logger.warning(f"DB connection attempt {attempt}/10 failed: {e}")
            await asyncio.sleep(2)
    else:
        raise RuntimeError("Could not connect to the database after 10 attempts")

    # ── Register all built-in pipeline components ───
    import app.components  # noqa: F401 — triggers auto-registration
    from app.runtime.registry import list_components
    logger.info(f"Registered components: {list_components()}")

app.include_router(project_router)
app.include_router(file_router)
app.include_router(router)
```

**Key points:**

- On startup: retry DB 10 times → create tables → register components.
- `import app.components` triggers `__init__.py` which calls `register_component()` for each built-in node type.

---

### `backend/app/components/` — Pipeline Node Implementations

This directory mirrors the frontend's `components/nodes/` folder. Each class implements `BaseComponent.execute()`.

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

**All components follow this contract:**
- `request_data` — the raw HTTP body that entered the pipeline.
- `inputs` — a dict of all upstream node outputs keyed by node ID (built from the edge map).
- `config` — the node's own configuration from the graph JSON.
- Returns data that becomes available to downstream nodes.

#### `http_entry.py` — HTTP Entry Component

```python
class HttpEntryComponent(BaseComponent):
    async def execute(self, request_data, inputs, config) -> dict:
        schema = config.get("request_schema", {})
        if not schema:
            return dict(request_data)  # Pass entire body
        # Extract only declared fields
        return {k: request_data[k] for k in schema if k in request_data}
```

- Entry point node — no upstream inputs.
- Extracts fields from request body per the `request_schema`.
- If no schema: passes the entire body through.

#### `processor.py` — Echo Processor Component

```python
class EchoProcessorComponent(BaseComponent):
    async def execute(self, request_data, inputs, config) -> dict:
        merged = {}
        for node_id, output in inputs.items():
            if isinstance(output, dict):
                merged.update(output)
            else:
                merged[node_id] = output
        return merged
```

- Merges all upstream inputs into one dict.
- Pass-through / echo behavior (template for future LLM/transform processors).

#### `response_builder.py` — Response Builder Component

```python
class ResponseBuilderComponent(BaseComponent):
    async def execute(self, request_data, inputs, config) -> dict:
        merged = {}
        for node_id, output in inputs.items():
            if isinstance(output, dict):
                merged.update(output)
            else:
                merged[node_id] = output
        schema = config.get("response_schema", {})
        if not schema:
            return merged
        # Build response using only declared fields (with typed defaults)
        response = {}
        for field_name, field_type in schema.items():
            if field_name in merged:
                response[field_name] = merged[field_name]
            else:
                defaults = {"string": "", "int": 0, "float": 0.0, "bool": False}
                response[field_name] = defaults.get(field_type, None)
        return response
```

- Terminal node — shapes the final API response.
- Only includes fields declared in `response_schema`.
- Provides typed defaults for missing fields.

#### `__init__.py` — Auto-Registration

```python
from app.components.http_entry import HttpEntryComponent
from app.components.processor import EchoProcessorComponent
from app.components.response_builder import ResponseBuilderComponent
from app.runtime.registry import register_component

register_component("http_entry", HttpEntryComponent)
register_component("echo_processor", EchoProcessorComponent)
register_component("processor", EchoProcessorComponent)          # alias
register_component("response_builder", ResponseBuilderComponent)
```

---

### `backend/app/runtime/compiler.py` — Graph Compiler

Turns a ReactFlow graph into an execution plan **with an edge map** for proper data flow.

**Compilation pipeline:**

1. `_build_adjacency()` — Adjacency list + in-degree map from edges.
2. `_build_edge_map()` — Reverse adjacency: `{ target: [source1, source2, ...] }`.
3. `_topological_sort()` — Kahn's algorithm; raises on cycles.
4. `_build_execution_plan()` — Maps sorted IDs to `{ id, component, config }`.
5. `_create_schema_model()` — Dynamic Pydantic models from `{ field: type_string }`.
6. `compile()` — Orchestrates all above. Returns:

```python
{
    "method": "POST",
    "path": "/api/custom/...",
    "request_model": <DynamicPydanticModel> | None,
    "response_model": <DynamicPydanticModel> | None,
    "ordered_nodes": [{ "id", "component", "config" }, ...],
    "edge_map": { "target_id": ["source_id_1", ...], ... }
}
```

**Key details:**
- The `edge_map` is included in the plan, enabling the executor to track data flow between nodes based on edges.
- **Response schema fallback:** The compiler first looks for `response_schema` on the entry node (since the HTTP Entry node now owns both request *and* response schemas). If the entry node has no response schema, it falls back to the response builder node's `response_schema`.

---

### `backend/app/runtime/executor.py` — Graph Executor

Runs nodes in topological order with **proper data flow**.

```python
class GraphExecutor:
    def __init__(self, execution_plan: dict):
        self.ordered_nodes = execution_plan["ordered_nodes"]
        self.edge_map = execution_plan.get("edge_map", {})

    async def execute(self, request_data: dict) -> Any:
        context = {}  # node_id → output
        last_output = None

        for node in self.ordered_nodes:
            node_id = node["id"]
            comp_name = node["component"]
            config = node.get("config", {})

            parent_ids = self.edge_map.get(node_id, [])
            inputs = {pid: context[pid] for pid in parent_ids if pid in context}

            try:
                component = get_component(comp_name)
                result = await component.execute(request_data, inputs, config)
            except Exception as exc:
                logger.error(f"Node {node_id} ({comp_name}) failed: {exc}")
                result = {"error": str(exc)}

            context[node_id] = result
            last_output = result

        return last_output
```

**Key improvements over earlier version:**
- Error handling: failing nodes return `{"error": "..."}` instead of crashing the whole pipeline.
- `last_output` tracked explicitly so the return value is always the final node's output.

**Data flow logic:**

```
HTTP Entry (id: "1") → output stored in context["1"]
    ↓ edge: 1→2
Processor (id: "2")  → inputs = { "1": context["1"] } → output stored in context["2"]
    ↓ edge: 2→3
Response (id: "3")   → inputs = { "2": context["2"] } → output = final API response
```

---

### `backend/app/runtime/registry.py` — Component & Route Registry

```python
# Component registry
register_component(name, cls)   # Register a component class by name
get_component(name)             # Instantiate and return (raises if missing)
list_components()               # List registered names

# Route registry
register_route(app, plan, executor, tag="deployed")  # Dynamically add FastAPI route with tag
unregister_route(app, path)                           # Remove a deployed route
list_routes()                                         # List active deployed routes
```

**Key details:**
- `register_route()` accepts a `tag` kwarg used as the OpenAPI tag for the route. At deploy time the tag is set to `{projectName}_{projectId}` so routes are namespaced per-project.
- Handles nullable `RequestModel` (for GET endpoints).
- Re-deploying the same path removes the old route first.
- Invalidates `app.openapi_schema` on every register/unregister so `/docs` stays up-to-date.
- Uses `body.model_dump()` (Pydantic v2) instead of `body.dict()`.

---

### `backend/app/core/config.py`

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str
    CLERK_SECRET_KEY: str
    CLERK_PUBLISHABLE_KEY: str

    class Config:
        env_file = ".env"

settings = Settings()
```

---

### `backend/app/core/auth.py`

Verifies Clerk JWT tokens. JWKS keys cached with 1-hour TTL, auto-refreshes on key rotation.

---

### `backend/app/models/models.py`

```python
class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    clerk_id = Column(String, unique=True)
    email = Column(String)

class Project(Base):
    __tablename__ = "projects"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, index=True)  # Clerk user ID is a string
    name = Column(String)

class File(Base):
    __tablename__ = "files"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"))
    name = Column(String)
    graph_json = Column(JSONB)
    is_deployed = Column(Boolean, default=False, server_default="false")
    deployed_path = Column(String, nullable=True)
    deployed_method = Column(String, nullable=True)
```

---

### API Endpoints

| Method | Path                                  | Auth     | Description                                              |
|--------|---------------------------------------|----------|----------------------------------------------------------|
| GET    | `/`                                   | Public   | Health check                                             |
| GET    | `/protected`                          | Required | Returns JWT payload                                      |
| POST   | `/api/projects`                       | Required | Create project                                           |
| GET    | `/api/projects`                       | Required | List user's projects                                     |
| PUT    | `/api/projects/{id}`                  | Required | Rename project                                           |
| DELETE | `/api/projects/{id}`                  | Required | Delete project                                           |
| GET    | `/api/projects/{id}/openapi`          | Required | Filtered OpenAPI 3.1 spec for this project's deployed routes |
| POST   | `/api/files`                          | Required | Create file with empty graph                             |
| GET    | `/api/files/project/{project_id}`     | Required | List files in a project (includes deploy status)         |
| GET    | `/api/files/{file_id}/meta`           | Required | Get file metadata (deploy status, path, method)          |
| GET    | `/api/files/{file_id}`                | Required | Get file's graph JSON                                    |
| PUT    | `/api/files/{file_id}`                | Required | Update graph data                                        |
| DELETE | `/api/files/{file_id}`                | Required | Delete file                                              |
| POST   | `/api/files/deploy/{file_id}`         | Required | Compile graph & register live route (tag: `name_id`)     |
| POST   | `/api/files/undeploy/{file_id}`       | Required | Remove a deployed route                                  |

---

## Frontend (Next.js 16 + React 19 + Clerk + ReactFlow)

### Tech Stack

| Library          | Version   | Purpose                    |
|------------------|-----------|----------------------------|
| Next.js          | 16.1.6    | React framework            |
| React            | 19.2.3    | UI library                 |
| @clerk/nextjs    | ^6.37.4   | Authentication             |
| axios            | ^1.13.5   | HTTP client                |
| reactflow        | ^11.11.4  | Node/edge graph editor     |
| shadcn/ui        | (latest)  | UI components (Radix-based)|
| Tailwind CSS     | v4        | Styling                    |
| zustand          | ^5.0.11   | State management           |
| lucide-react     | ^0.566.0  | Icons                      |
| sonner           | (latest)  | Toast notifications        |

### shadcn UI Components

| Component    | File               | Usage                                |
|--------------|--------------------|--------------------------------------|
| badge        | `ui/badge.tsx`     | Status indicators, method labels     |
| button       | `ui/button.tsx`    | Actions throughout the app           |
| card         | `ui/card.tsx`      | Project/file cards, stats            |
| dialog       | `ui/dialog.tsx`    | Create project/flow modals           |
| input        | `ui/input.tsx`     | Form inputs in modals                |
| label        | `ui/label.tsx`     | Form labels                          |
| scroll-area  | `ui/scroll-area.tsx`| Sidebar scrolling in flow editor    |
| select       | `ui/select.tsx`    | Dropdown selectors                   |
| separator    | `ui/separator.tsx` | Visual dividers                      |
| sheet        | `ui/sheet.tsx`     | Side panels                          |
| sonner       | `ui/sonner.tsx`    | Toast notifications (replaces alert)|
| tabs         | `ui/tabs.tsx`      | Tabbed interfaces                    |
| tooltip      | `ui/tooltip.tsx`   | Button/action tooltips               |

---

### `frontend/proxy.ts` — Clerk Auth (replaces middleware.ts)

Next.js 16 uses `proxy.ts` instead of `middleware.ts`. Handles authentication and route protection.

```typescript
import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";
import { NextResponse } from "next/server";

const isPublicRoute = createRouteMatcher([
  "/", "/sign-in(.*)", "/sign-up(.*)", "/sso-callback(.*)", "/api/webhook(.*)",
]);

export default clerkMiddleware(async (auth, req) => {
  const { userId } = await auth();
  const pathname = req.nextUrl.pathname;

  if (pathname.includes("/sso-callback")) return NextResponse.next();
  if (userId && (pathname.startsWith("/sign-in") || pathname.startsWith("/sign-up")))
    return NextResponse.redirect(new URL("/dashboard", req.url));
  if (!userId && !isPublicRoute(req))
    return NextResponse.redirect(new URL("/sign-in", req.url));
});
```

**Key points:**
- Landing page (`/`) is public; authenticated users on sign-in/sign-up are redirected to `/dashboard`.
- Unauthenticated users on protected routes are redirected to `/sign-in`.
- SSO callbacks are always allowed through.

---

### `frontend/app/layout.tsx`

Root layout with `ClerkProvider`, `TooltipProvider`, and `Toaster`.

```typescript
import { ClerkProvider } from '@clerk/nextjs'
import { TooltipProvider } from "@/components/ui/tooltip";
import { Toaster } from "@/components/ui/sonner";

export default function RootLayout({ children }) {
  return (
    <ClerkProvider afterSignOutUrl="/" signInUrl="/sign-in" signUpUrl="/sign-up"
      appearance={{ elements: { rootBox: "mx-auto" } }}>
      <html lang="en">
        <body>
          <TooltipProvider delayDuration={200}>
            {children}
          </TooltipProvider>
          <Toaster richColors position="bottom-right" />
        </body>
      </html>
    </ClerkProvider>
  );
}
```

**Key change:** `afterSignOutUrl` is set to `"/"` (landing page) instead of `/sign-in`.

---

### `frontend/app/files/[fileId]/page.tsx` — Flow Editor

The heart of the app. Features:

- **Dark canvas** with dot grid background (`#0a0a0f`)
- **Left sidebar** with component palette + stats panel + usage tips
- **Top toolbar** with Save (⌘S) + Deploy + Stop buttons with loading states
- **Live status indicator** in toolbar — shows `Live` (green, pulsing) or `Stopped` badge with deployed method + path
- **Deploy/Redeploy** — button label changes to "Redeploy" when already live
- **Stop/Undeploy** — red stop button appears when flow is live; calls `POST /api/files/undeploy/{id}`
- **DeletableEdge** custom edge type — delete button appears on edge when selected
- **Toast notifications** via Sonner
- **Animated edges** with indigo color
- **Staggered node placement** (offset by `nodes.length * 30`)
- **MiniMap** with color-coded nodes (blue/amber/emerald)
- **ReactFlowProvider** wrapper for proper context
- **`deleteKeyCode={null}`** — disables default keyboard delete (nodes deleted via NodeWrapper's X button instead)

```typescript
// Key architecture:
export default function FileEditorPage({ params }) {
  const { fileId } = use(params);
  return (
    <ReactFlowProvider>
      <FlowEditor fileId={fileId} />
    </ReactFlowProvider>
  );
}
```

**Layout:**
```
┌──────────┬────────────────────────────────────────────┐
│          │  ← Back   [fileId]           [Save] [Deploy]│
│  SIDEBAR │─────────────────────────────────────────────│
│          │                                              │
│ Components│         ReactFlow Canvas                   │
│  ┌─────┐ │         (dark theme, dot grid)              │
│  │HTTP │ │                                              │
│  ├─────┤ │              ┌──────┐                       │
│  │Proc.│ │              │ Node │──────▶ ...            │
│  ├─────┤ │              └──────┘                       │
│  │Resp.│ │                                              │
│  └─────┘ │                                    [MiniMap] │
│          │                                   [Controls] │
│  Info    │                                              │
│  Nodes: 3│                                              │
│  Edges: 2│                                              │
└──────────┴──────────────────────────────────────────────┘
```

**Toolbar actions:**

| Button          | Shortcut | Action                                                 |
|-----------------|----------|--------------------------------------------------------|
| Save            | ⌘S       | PUT /api/files/{id} — saves graph to DB               |
| Deploy/Redeploy | —        | Save + POST /api/files/deploy/{id}                    |
| Stop            | —        | POST /api/files/undeploy/{id} (visible only when live)|

**On mount:** fetches both the graph JSON (`GET /api/files/{id}`) and file metadata (`GET /api/files/{id}/meta`) in parallel to restore deploy status.

---

### `frontend/components/nodes/HttpEntryNode.tsx`

Dark-themed node wrapped in `NodeWrapper` (delete button + double-click rename). Features:
- **Method selector** — clickable pill buttons (GET/POST/PUT/DELETE/PATCH) with color coding
- **Path input** — mono font, dark styled
- **Request schema builder** — add fields with name + type, remove on hover
- **Response schema builder** — same UX, defines the API's response contract (emerald accent)
- Immutable state updates via `setNodes()` — syncs config on every change

**Config produced:**
```json
{
  "is_entry": true,
  "method": "POST",
  "path": "/api/endpoint",
  "request_schema": { "name": "string", "age": "int" },
  "response_schema": { "message": "string", "status": "bool" }
}
```

**Visual design:**
- Blue accent (`border-blue-500/30`)
- Dark card background (`#1a1a2e`)
- Blue source handle at bottom
- Response schema section uses emerald accent to distinguish from request

---

### `frontend/components/nodes/ProcessorNode.tsx`

Dark-themed node wrapped in `NodeWrapper` (delete button + double-click rename). Features:
- **Editable label** — user can rename the processor
- **Behavior description** — explains what it does
- **I/O indicators** — shows input/output types (`any` → `merged`)
- **No render-wipe** — uses `if (!data.component)` guard with `queueMicrotask` to avoid updating state during render

**Visual design:**
- Amber accent (`border-amber-500/30`)
- Target handle (top) + Source handle (bottom)

---

### `frontend/components/nodes/ResponseNode.tsx`

Dark-themed node wrapped in `NodeWrapper`. Features **field mappings** instead of a simple schema list:
- **Add/remove fields** — each field has a name and type
- **Source toggle** per field — `Input` (pull value from upstream data by key) or `Static` (hardcode a literal value)
- **Value input** per field — the upstream key or static literal
- **Field count badge** in header
- **Backward compatible** — old `response_schema`-only configs are auto-converted to `field_mappings`

**`FieldMapping` interface:**
```typescript
{ name: string; type: string; source: "input" | "static"; value: string }
```

**Config produced:**
```json
{
  "is_response": true,
  "response_schema": { "message": "string", "success": "bool" },
  "field_mappings": [
    { "name": "message", "type": "string", "source": "input", "value": "message" },
    { "name": "success", "type": "bool", "source": "static", "value": "true" }
  ]
}
```

**Visual design:**
- Emerald accent (`border-emerald-500/30`)
- Target handle (top) only — terminal node
- Input source uses cyan accent; Static source uses violet accent

---

### `frontend/components/nodes/NodeWrapper.tsx` (Client Component)

Shared wrapper for all custom nodes. Provides two behaviors:

1. **Floating delete button** — red circle with `X`, visible on hover over any node. Removes the node and all connected edges.
2. **Editable name overlay** — double-click the node header text to enter edit mode. Press Enter to commit, Escape to cancel. Shows a pencil icon on hover.

```typescript
<NodeWrapper id={id} name={nodeName} onNameChange={handleNameChange} accentColor="blue">
  {/* node content */}
</NodeWrapper>
```

- `accentColor` — Tailwind color token (`blue`, `amber`, `emerald`) for consistent theming.
- All three node types (`HttpEntryNode`, `ProcessorNode`, `ResponseNode`) wrap their content in this component.

---

### `frontend/components/edges/DeletableEdge.tsx` (Client Component)

Custom edge type that renders a delete button at the midpoint of the edge.

- Uses `getBezierPath` for the curve and `EdgeLabelRenderer` for the button overlay.
- The red `X` button is only visible when the edge is **selected** (click to select, then click `X` to delete).
- Registered as `edgeTypes={{ deletable: DeletableEdge }}` in the Flow Editor.
- Set as the default edge type via `defaultEdgeOptions={{ type: "deletable" }}`.

---

### `frontend/app/page.tsx` — Landing Page

Public landing page with animated 3D hero, scroll-reveal sections, and polished UI.

**Key sections:**
- **NavBar** — Fixed top nav with glass blur, indigo glow line, sign-in/sign-up or dashboard link based on auth state.
- **SplineHero** — Scroll-animated 3D Spline asset that grows and centers as user scrolls (client component).
- **Trust Bar** — Marquee of partner/technology logos.
- **Features** — Grid of feature cards with icons and descriptions.
- **How It Works** — Step-by-step numbered flow with scroll-reveal animation.
- **CTA Section** — Call-to-action with gradient background.
- **Footer** — Links, branding, legal.

---

### `frontend/components/SplineHero.tsx` (Client Component)

Scroll-driven 3D hero animation using Spline web component.

**Behavior:**
- Starts at normal scale with hero text overlaid.
- As user scrolls, the 3D asset grows (scale `1.0 → 1.3`) and centers while text fades out.
- Page "locks" during animation (section is `min-h-[200vh]` with `sticky` positioning).
- Multi-layered approach to hide Spline "Built with Spline" watermark:
  - `overflow: hidden` on parent with viewer slightly oversized to clip watermark.
  - Gradient overlay divs at high z-index.
  - CSS `::part(logo)` and shadow-DOM fallback selectors in `globals.css`.

---

### `frontend/components/ScrollReveal.tsx` (Client Component)

Intersection Observer-based fade-up animation wrapper.

```typescript
<ScrollReveal delay={0.2}>
  <FeatureCard ... />
</ScrollReveal>
```

- Configurable `delay` for staggered child animations.
- Uses `IntersectionObserver` with `threshold: 0.15`.
- Applies `translateY(24px) → 0` with opacity transition.

---

### `frontend/components/OpenApiModal.tsx` (Client Component)

Modal dialog to view and export the project-specific OpenAPI JSON.

**Features:**
- Fetches `GET /api/projects/{projectId}/openapi` on open.
- Displays prettified JSON with syntax highlighting in `<pre>` block.
- Copy to clipboard button with success feedback.
- Download as `.json` file.
- Shows endpoint count in footer.
- Empty state when no deployed flows exist.

---

### `frontend/components/Navbar.tsx`

Dark-themed top navigation:
- Indigo logo square with `Layers` icon
- User email + Clerk `UserButton`
- Backdrop blur glass effect
- Sticky positioning

---

### `frontend/components/CreateProjectModal.tsx` / `CreateFlowModal.tsx`

Dark-themed modal dialogs:
- Dark background (`#13131f`)
- Indigo accent buttons
- Auto-focus + Enter-to-submit
- Controlled open state

---

### `frontend/app/dashboard/page.tsx`

Dark-themed dashboard:
- Stats cards with colored icons (Projects / Flows / Deployed)
- Project grid with folder icons + arrow indicators
- Empty state with icon placeholder
- Toast notifications for errors

---

### `frontend/app/projects/[projectId]/page.tsx`

Dark-themed project detail:
- Back navigation to dashboard
- Flow file grid with `FileJson` icons + deploy status badges (Live/Stopped)
- **Per-file deploy toggle** — power button on each card to deploy or undeploy a flow directly from the project view (with loading spinner)
- **Deployed path display** — shows `METHOD /path` on live file cards
- **OpenAPI button** — `OpenApiModal` in header, opens modal with project-specific OpenAPI spec
- Empty state with icon
- Toast notifications

---

## Data Flow — End to End

### 1. User Designs Pipeline (Frontend)

```
HttpEntryNode ─edge─▶ ProcessorNode ─edge─▶ ResponseNode
  config:                config:               config:
    method: POST           label: "Echo"         response_schema:
    path: /api/hello                               message: string
    request_schema:                                 status: bool
      name: string                              field_mappings:
      age: int                                    [{name:"message", source:"input", value:"message"},
    response_schema:                               {name:"status", source:"static", value:"true"}]
      message: string
      status: bool
```

### 2. User Saves (PUT /api/files/{id})

```json
{
  "graph": {
    "nodes": [
      { "id": "1", "type": "http_entry", "data": { "component": "http_entry", "config": { "is_entry": true, "method": "POST", "path": "/api/hello", "request_schema": { "name": "string", "age": "int" }, "response_schema": { "message": "string", "status": "bool" } } } },
      { "id": "2", "type": "processor", "data": { "component": "echo_processor", "config": { "label": "Echo" } } },
      { "id": "3", "type": "response_builder", "data": { "component": "response_builder", "config": { "is_response": true, "response_schema": { "message": "string", "status": "bool" }, "field_mappings": [{"name":"message","type":"string","source":"input","value":"message"},{"name":"status","type":"bool","source":"static","value":"true"}] } } }
    ],
    "edges": [
      { "source": "1", "target": "2" },
      { "source": "2", "target": "3" }
    ]
  }
}
```

### 3. User Deploys (POST /api/files/deploy/{id})

**Namespace tag:** `{projectName}_{projectId}` (e.g. `MyProject_a1b2c3d4-...`). This tag is attached to every deployed route so the per-project OpenAPI endpoint can filter by it.

**Compiler produces:**
```python
{
    "method": "POST",
    "path": "/api/hello",
    "request_model": DynReq(name: str, age: int),
    "response_model": DynResp(message: str, status: bool),
    "ordered_nodes": [node_1, node_2, node_3],
    "edge_map": { "2": ["1"], "3": ["2"] }
}
```

### 4. External Client Calls Deployed Endpoint

```bash
curl -X POST http://localhost:8000/api/hello \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice", "age": 30}'
```

**Execution flow:**
```
1. HttpEntryComponent.execute({"name":"Alice","age":30}, {}, config)
   → Extracts: {"name": "Alice", "age": 30}
   → Stored in context["1"]

2. EchoProcessorComponent.execute(request_data, {"1": {"name":"Alice","age":30}}, config)
   → Merges inputs: {"name": "Alice", "age": 30}
   → Stored in context["2"]

3. ResponseBuilderComponent.execute(request_data, {"2": {"name":"Alice","age":30}}, config)
   → Shapes to response_schema: {"message": "", "status": false}
   → (name/age not in response_schema, so defaults used)
   → Returns: {"message": "", "status": false}
```

### 5. User Views Project OpenAPI Spec

The frontend's `OpenApiModal` calls `GET /api/projects/{project_id}/openapi`. The backend:

1. Looks up the project by ID → builds the tag string `{name}_{id}`.
2. Reads the full FastAPI OpenAPI schema via `request.app.openapi()`.
3. Filters `paths` to keep only operations whose `tags` array includes the project's tag.
4. Transitively resolves `$ref` schemas used by those paths.
5. Returns a clean OpenAPI 3.1 document scoped to that project.

```json
{
  "openapi": "3.1.0",
  "info": { "title": "MyProject — API", "version": "1.0.0" },
  "paths": {
    "/api/hello": {
      "post": { "tags": ["MyProject_a1b2..."], "summary": "..." }
    }
  },
  "tags": [{ "name": "MyProject_a1b2..." }]
}
```

---

### `frontend/app/globals.css` — Global Styles

Beyond standard Tailwind/shadcn theme variables, includes:

- **Marquee animation** — `@keyframes marquee-scroll` for the landing page trust bar.
- **Smooth scrolling** — `html { scroll-behavior: smooth; }`.
- **Spline watermark hide** — CSS rules targeting `spline-viewer::part(logo)` and shadow-DOM `#logo` to hide the "Built with Spline" badge.

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
- **Postgres**: localhost:5432
- **Redis**: localhost:6379
