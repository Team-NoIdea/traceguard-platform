# TraceGuard — Frontend (Phase 1)

AI-assisted application security analysis — frontend UI.

This is **Phase 1**: a complete, working UI built entirely against realistic
mock data. No real backend, no real Semgrep/CodeQL/runtime analysis, and no
LangGraph — just the product surface, architected so Phase 2 can swap in
the real FastAPI backend without restructuring anything.

## Tech stack

- **React 19** + **TypeScript** — functional components only
- **Vite** — dev server / build
- **Tailwind CSS v4** — design tokens defined once in `src/index.css` via `@theme`
- **React Router** — client-side routing (`createBrowserRouter`)
- **TanStack Query** — data-fetching/caching layer (currently backed by mock resolvers)
- **Lucide React** — icons

No Redux, no CSS-in-JS, no component library — state lives in TanStack Query
(server-shaped data) and local `useState` (form/filter state).

## Folder structure

```
src/
├── app/                 App shell: routes, providers, root component
├── pages/                One folder per route, thin — compose components + hooks
├── components/
│   ├── layout/           Sidebar, Header, PageContainer, AppLayout
│   ├── ui/                Design-system primitives (Button, Badge, Card, ...)
│   └── findings/          Finding-specific display components
├── features/
│   ├── scans/              types, mock data, api (mock), hooks (TanStack Query)
│   ├── findings/            same shape
│   └── analysis/            pipeline/agent-activity types + derivation (no api.ts —
│                            analysis is derived from a Scan, not fetched separately)
├── lib/                  api.ts (fetch client, unused until Phase 2), utils.ts
├── hooks/                usePolling.ts — generic interval-driven re-render hook
└── types/                Domain types mirroring the backend's Pydantic schema
```

**Data flow, strictly one direction:** `UI (pages/components) → feature hooks
→ feature api.ts → mock data (today) / apiClient (Phase 2)`. Pages never
import mock data or call `fetch` directly.

## Local setup

```bash
npm install
cp .env.example .env   # optional in Phase 1 — nothing reads it yet
npm run dev
```

Then open the printed local URL (typically http://localhost:5173).

## Available scripts

| Command | Does |
|---|---|
| `npm run dev` | Start the Vite dev server |
| `npm run build` | Type-check (`tsc -b`) then production build |
| `npm run preview` | Serve the production build locally |
| `npm run lint` | Run oxlint |

## Environment variables

| Variable | Purpose |
|---|---|
| `VITE_API_BASE_URL` | Base URL of the FastAPI backend. Defined and typed today (`src/lib/api.ts`), but **not called anywhere yet** — every `features/*/api.ts` resolves mock data instead. Phase 2 points these at real endpoints. |

## About the mock data

Everything under `src/features/*/mockData.ts` is realistic, hand-authored
demo data — no `Math.random()`, no fixtures library:

- **6 findings** (`features/findings/mockData.ts`) covering SQL Injection,
  Command Injection, Unsafe eval, Path Traversal, Reflected XSS, and a
  Hardcoded Secret — spanning all four severities, a spread of confidence
  scores, both static-only and static+runtime evidence, multiple tools
  (Semgrep, CodeQL, Gitleaks), and varied statuses (OPEN/CONFIRMED/DISMISSED)
  so every filter on the Findings page actually does something.
- **4 scans** (`features/scans/mockData.ts`), one per status
  (Completed/Running/Failed/Queued), with finding counts derived live from
  the findings above rather than hardcoded separately.
- **One live scan**: submitting New Scan creates `mock-scan-001` with a
  `started_at` timestamp; the Scan Progress page derives pipeline/activity
  state as a pure function of elapsed time, so it genuinely animates
  through all 6 stages over ~14 seconds and then completes — no
  `setInterval` state machine to keep in sync, just time math.

All mock resolvers (`features/*/api.ts`) are `async` and return the same
shapes real backend calls will, with an artificial ~300ms delay, so loading
states are exercised honestly rather than resolving instantly.

## Phase 2

Phase 2 wires this UI to the real backend:

1. FastAPI endpoints for scans/findings/correlation/confidence (already
   underway server-side — see the repository root)
2. LangGraph-driven AI analysis, replacing the "Mock analysis" placeholder
   on the Finding Details page
3. Real remediation generation + PR creation (the "Apply Fix" / "Create
   Pull Request" buttons are wired up but disabled — "Coming in Phase 2" —
   until then)

None of this should require restructuring the frontend: swap the bodies of
`features/*/api.ts` to call `apiClient` (`src/lib/api.ts`) instead of the
mock resolvers, and every page/component/hook above stays the same.
