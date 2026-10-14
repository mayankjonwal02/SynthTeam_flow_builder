# Contributing to SynthTeam

Thanks for your interest in improving SynthTeam! This guide covers the development setup, conventions and the most common change: adding a new node type.

## Development setup

Follow [docs/getting-started.md](docs/getting-started.md). The Docker Compose stack mounts `./backend` and `./frontend` into their containers, so code changes reload automatically.

## Workflow

1. Open an issue describing the bug or feature (skip this for small fixes).
2. Create a branch from `main`: `git checkout -b feature/short-description`.
3. Make focused commits with clear messages.
4. Run the checks below.
5. Open a pull request explaining **what** changed and **why**, with screenshots for UI changes.

## Checks

```bash
# Frontend
cd frontend
npm run lint
npm run build

# Backend: confirm the app imports and registers its components
cd backend
python -c "import app.main"
```

Run the backend and click through the affected workflow in the editor before opening a PR.

## Code style

- **Python** — follow PEP 8, use type hints and `async` I/O, and keep each node component in its own module.
- **TypeScript/React** — functional components and hooks; Tailwind and the shadcn/ui primitives in `frontend/components/ui`.
- Match the surrounding code's naming, comment density and structure.
- Never commit secrets. `.env` files are git-ignored; update the `.env.example` files when you add a variable, and document it in [docs/configuration.md](docs/configuration.md).

## Adding a new node type

A node exists in up to four places that must agree on its type name (here `my_node`).

### 1. Backend component

Create `backend/app/components/my_node.py` (or `components/ai/` for AI nodes):

```python
from typing import Any, Dict

from app.components.base import BaseComponent
from app.components.component_registry import register_component
from app.db_connectors.interpolation import resolve_field_mapping


@register_component("my_node")
class MyNodeComponent(BaseComponent):
    """One-line description of what the node does."""

    async def execute(self, request_data: dict, inputs: Dict[str, Any], config: dict) -> Any:
        # request_data: the original HTTP request body
        # inputs:       {parent_node_id: parent_output}
        # config:       this node's config from the graph JSON
        ...
        return {"result": ...}
```

Import it from `backend/app/components/__init__.py` (or `components/ai/__init__.py`) so it registers at startup.

### 2. Frontend node

- Add `frontend/components/nodes/MyNode.tsx`, wrapping it in `NodeWrapper` and using `FieldModeInput` for configurable fields. For DB and AI nodes, prefer the existing factories.
- Register it in `frontend/components/nodes/nodeTypes.ts`.
- Add a palette entry, a minimap colour and its default config in `getInitialConfig` in `frontend/app/files/[fileId]/page.tsx`.

### 3. Agent Builder catalog *(optional)*

To let the AI Agent Builder use the node, add it to `COMPONENT_CATALOG` (and `HANDLE_COMPATIBILITY` for typed handles) in `backend/app/multi_agent/tools.py`.

### 4. Documentation

Describe the node, its config and handles in [docs/node-reference.md](docs/node-reference.md).

## Adding providers

LLM providers, embeddings, vector stores, vision providers, tools and DB connectors each have a `registry.py` in their package under `backend/app/ai/` or `backend/app/db_connectors/`. Follow an existing implementation in the same folder and import the new module from the package's `__init__.py`.

## Reporting security issues

Please don't open public issues for vulnerabilities. Contact the maintainer privately through GitHub.

## License

By contributing, you agree that your contributions will be licensed under the [Apache License 2.0](LICENSE).
