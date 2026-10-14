# SynthTeam Frontend

Next.js 16 (App Router) app for SynthTeam: the visual workflow editor, project dashboard, execution logs and the AI Agent Builder.

Stack: React 19, ReactFlow 11, Zustand, Tailwind CSS 4, shadcn/ui, Clerk.

## Development

```bash
cp .env.example .env.local   # set NEXT_PUBLIC_API_URL and Clerk keys
npm ci
npm run dev                  # http://localhost:3000
```

The backend must be running at `NEXT_PUBLIC_API_URL` (default `http://localhost:8000`).

| Script | Purpose |
|--------|---------|
| `npm run dev` | Development server with hot reload |
| `npm run build` | Production build |
| `npm start` | Serve the production build |
| `npm run lint` | ESLint |

## Layout

| Path | Contents |
|------|----------|
| `app/` | Routes: dashboard, projects, file editor and logs, agent builder, auth |
| `components/nodes/` | One component per workflow node (`db/`, `ai/` subfolders); `nodeTypes.ts` registry |
| `components/agent/` | Agent Builder canvas, chat and status panels |
| `components/ui/` | shadcn/ui primitives |
| `hooks/` | `useAgentWebSocket` for Agent Builder streaming |
| `proxy.ts` | Clerk route protection |

See the [project documentation](../docs/README.md) for architecture, configuration and the node reference.
