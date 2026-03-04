# SynthTeam QA + Security Review (Browser Automation) — 2026-03-04

## Scope
- **Target**: `http://localhost:3000` (frontend) talking to `http://localhost:8000` (backend)
- **Goal**: Smoke-test key pages/flows via browser automation and identify security vulnerabilities + product improvements.
- **Notes**:
  - Findings include **observed runtime behavior** + a **light code review** of the relevant backend routers.
  - This is **not** a full pentest (no credential stuffing, fuzzing of every endpoint, or SAST/DAST suite).

## Pages/flows exercised
- **Marketing/home**: `/`
- **Auth’d app**:
  - Dashboard: `/dashboard`
  - Project flows: `/projects/{projectId}`
  - Flow editor: `/files/{fileId}` (including AI Copilot + Logs modal)
  - Agent builder: `/agent-builder` (start page)

## Key functional observations
- **Dashboard → New Project**: project creation works; project appears immediately in list.
- **Project → New Flow**: flow creation works; flow appears in list and opens editor.
- **Flow editor**:
  - AI Copilot successfully produced nodes after the request completed.
  - Logs modal loads and shows “No executions yet” until a deploy/execution happens.
- **Agent Builder**:
  - UI attempts to start a session and then route to `/agent-builder/{sessionId}`; when the backend isn’t reachable/ready, the UI resets to the start state without a strong inline error state.

## Security findings (highest signal)

### 1) IDOR / missing authorization checks on project + file routes (High)
**Impact**: Any authenticated user could potentially read/update/delete another user’s projects/files by guessing IDs.

**Evidence (code)**:
- `backend/app/api/projects.py`
  - `update_project`, `delete_project`, `get_project_openapi` fetch by `Project.id == project_id` **without** verifying `Project.user_id == user["sub"]`.
- `backend/app/api/files.py`
  - `get_file_meta`, `get_file`, `update_file`, `delete_file`, `deploy_file`, `undeploy_file` fetch by `File.id == file_id` **without** verifying the file’s project belongs to the current user.
  - `create_file` accepts `project_id` and never verifies the project belongs to the current user.

**Recommended fix**:
- For **every** project/file read/write endpoint:
  - Join `Project` and enforce `Project.user_id == user["sub"]`
  - Or fetch the resource and explicitly check ownership before returning/mutating.
- Add integration tests for cross-user access.

### 2) Multi-agent endpoints appear unauthenticated (Medium → High depending on deployment)
**Impact**: If deployed beyond localhost or if CORS/origin restrictions are weakened, attackers could start agent sessions and potentially abuse tool execution (web requests, code execution, etc.) through your agent toolchain.

**Evidence (code)**:
- `backend/app/multi_agent/api.py` endpoints (`/agent/session/start`, `/agent/session/{id}/message`, etc.) do **not** require `verify_token`.

**Recommended fix**:
- Require auth for agent endpoints, at least in production.
- Add per-user session ownership and rate limiting.
- If you want “anonymous mode”, gate it behind explicit config (`ALLOW_ANON_AGENT_SESSIONS=false` by default).

### 3) Input validation: project/flow names allow “HTML-looking” values (Low, but watch for later rendering)
**Observed**:
- Creating a project with name `<img src=x onerror=alert(1)>` displays as literal text (no JS executed in the UI observed).

**Risk**:
- Safe today because React escapes by default; becomes risky if any future view uses `dangerouslySetInnerHTML`, markdown rendering, email templates, or logs rendering.

**Recommended fix**:
- Apply a **conservative validation** (length limits; restrict control chars; optionally restrict `< >`).
- Normalize whitespace; enforce a max length (e.g., 80 chars).

### 4) “Flow name” accepts path-like strings (Low)
**Observed**:
- Flow name accepted `../../etc/passwd` and was displayed as `../../etc/passwd.json`.

**Risk**:
- Looks scary but current backend stores `File.name` in DB (not filesystem paths). Still, it’s confusing UX and can become an issue if you later add exports or filesystem-backed storage.

**Recommended fix**:
- Same validation as above + forbid path separators (`/`, `\`) and `..`.

## Product improvements (non-security)
- **Centralize API base URL**: Several frontend files historically hardcoded `http://localhost:8000`. Prefer `process.env.NEXT_PUBLIC_API_URL` everywhere so Docker/local/prod behave the same.
- **Agent builder error UX**: when session start fails, show inline error (not just an alert or silent reset), and keep the “Start” button state consistent.
- **Copilot config UX**:
  - Show a clear “Ollama unreachable / models endpoint failed” message (with a retry button).
  - Default to first installed model when available.

## Ollama migration notes (for this repo)
- Backend now supports an Ollama base URL via `OLLAMA_BASE_URL` and exposes `GET /agent/ollama/models` (reads Ollama’s `/api/tags`).
- In Docker, set `OLLAMA_BASE_URL=http://host.docker.internal:11434` (and ensure `extra_hosts: ["host.docker.internal:host-gateway"]` for Linux).
- Frontend Copilot + Agent Builder can show a dropdown of installed models when that endpoint returns models.

## Suggested next steps
- Fix IDOR in `/api/projects` and `/api/files` first (highest risk).
- Add auth + ownership checks for `/agent/*` routes (or explicitly gate anonymous access).
- Add validation constraints for names + test coverage.
- Add a small E2E test suite for:
  - create project → create flow → copilot creates nodes → deploy → hit endpoint → see execution logs.

