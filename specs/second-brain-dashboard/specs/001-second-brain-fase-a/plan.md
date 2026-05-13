# Implementation Plan: Second Brain Dashboard — Fase A

**Branch**: `001-second-brain-fase-a` (subproject not a git root; staying on parent `main`) | **Date**: 2026-05-13 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-second-brain-fase-a/spec.md`

## Summary

Fase A delivers a strictly read-only web dashboard at `https://tablero.nosvers.com` that surfaces Angel's and África's daily notes from the existing vault as a single merged timeline, with author/tag/date filters, full-text search, and a markdown detail view. The dashboard runs as a Vite + React + TypeScript single-page app, served by nginx as static files, calling a thin FastAPI/Starlette REST extension that is mounted **inside the existing `nosvers-mcp` uvicorn process** (port 8765) alongside `voz.rest`. The REST extension is a thin orchestration layer: it imports and reuses `voz.auth.validar_token`, `voz.buscar.dia_buscar_impl`, and `voz.vault_io.{leer_dia, listar_dias}` directly (Constitution IV). No new database, no new auth scheme, no new MCP tool — the dashboard composes existing primitives. The single architectural decision worth recording is *how* the backend reaches `dia_buscar`: in-process Python import vs. round-tripping through the MCP transport. We pick **in-process import**, justified in `research.md`.

## Technical Context

**Language/Version**: Python 3.11 (backend, matching the existing `nosvers-mcp` runtime); TypeScript 5.x with React 18 (frontend).

**Primary Dependencies**:
- Backend (reused, already installed): FastMCP 3.x, Starlette (transitive from FastMCP), uvicorn, PyJWT, PyYAML. Imports from `voz/*`: `auth`, `buscar`, `vault_io`.
- Backend (new): none. The dashboard REST extension uses only the same Starlette primitives already present in `voz/rest.py`. Markdown serving stays plaintext at the API layer; rendering is the frontend's job.
- Frontend (new): Vite 5, React 18, TypeScript 5, Tailwind CSS 3, shadcn/ui components (Radix UI + Tailwind), `react-markdown` + `remark-gfm` + `rehype-highlight` for the detail renderer, `idb-keyval` for the 30-note IndexedDB cache, `clsx` + `lucide-react` for UI plumbing. No router (single-page app with internal state) or a featherweight one (`wouter`) if needed — decision deferred to implementation.

**Storage**: None of our own. The vault at `/home/nosvers/public_html/knowledge_base/dia/*.md` is the only persistence layer (Constitution III). Frontend IndexedDB stores up to 30 recent notes for the offline fallback (FR-016) and is treated as derived cache, not source of truth.

**Testing**:
- Backend: pytest with `httpx.AsyncClient` against the mounted Starlette routes; reuse the test harness pattern already present for `voz/`. Smoke tests for: JWT 401 path, timeline shape, search proxy, detail-view path validation.
- Frontend: Vitest + React Testing Library for component logic; Playwright (manual run, not required for first commit) for one happy-path end-to-end.
- Performance: Lighthouse CLI in CI-equivalent (manual on Angel's reference profile) for SC-001; locust-style script of `httpx.AsyncClient` for SC-003.
- Tests are scoped to smoke level for Fase A — the constitution does not mandate TDD; spec.md does not request tests. Just enough to catch regressions on the contract endpoints and the auth gate.

**Target Platform**: Linux server (existing VPS Hostinger, srv1313138.hstgr.cloud, running as `nosvers-mcp.service` under systemd, behind nginx 1.24+). Frontend targets the last two versions of Chrome (mobile + desktop), Safari iOS 16+, Firefox 120+, on viewports 360–2560 px wide.

**Project Type**: Web application — backend extension + new frontend SPA. Constitution VIII forbids SSR / heavy meta-frameworks, so this is a pure SPA + REST split, not a Next/Remix monolith.

**Performance Goals** (anchored to spec SCs):
- Cold-cache page load on Slow-4G Lighthouse profile: TTI ≤ 2 s (SC-001).
- Filter toggle re-render: ≤ 200 ms (SC-002).
- Full-text search p95: ≤ 500 ms (SC-003).
- Note detail open: ≤ 300 ms (SC-004).
- Unauthenticated request rejection: ≤ 50 ms (SC-006).

**Constraints**:
- Mounted **inside** the running `nosvers-mcp` uvicorn process — no new systemd unit, no new port (Constitution V — no regression).
- Tablero CORS allowed-origin is exclusively `https://tablero.nosvers.com` (Constitution X). The existing `voz.rest` CORS for `https://voz.nosvers.com` is **unchanged** to preserve VOZ PWA behavior.
- No file write paths: the tablero REST module does not import `escribir_nota`, `guardar_audio_opus`, or any other write primitive from `voz.vault_io` (Constitution VI; FR-014).
- Frontend bundle size: target ≤ 200 KB gzipped initial JS payload, to satisfy SC-001 on 4G.

**Scale/Scope**:
- Users: 2 (Angel, África). Concurrency is effectively 1–2 simultaneous sessions.
- Vault size today: O(100) notes across O(60) day files; full-text search over the whole vault completes in tens of ms (verified empirically; `voz.buscar` reads files sequentially).
- The performance budget assumes today's vault size and one note/day growth; if the vault grows to thousands of notes, `dia_buscar` will need indexing, but that is **explicitly out of scope for Fase A** (mentioned only as a future option in the constitution's Additional Constraints).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

Each principle is graded compliant / partial / violation, with a one-line justification.

| # | Principle | Status | Justification |
|---|-----------|--------|---------------|
| I | Soberanía | compliant | All compute on the existing VPS; no new cloud service introduced. Reuses Hostinger + Let's Encrypt + nginx stack already in place. |
| II | MCP-first | compliant | Every dashboard read composes existing `voz.*` primitives that already back MCP tools (`dia_buscar`, indirectly `dia_contexto`). Timeline = `listar_dias` + `leer_dia`; search = `dia_buscar_impl`; note detail = `leer_dia` on a specific date. No new business logic is born in the dashboard layer. |
| III | Vault as Source of Truth | compliant | No new DB. IndexedDB is derived cache, invalidated by server `Last-Modified`. SQLite at `voz/data/tokens.sqlite` predates this project and is the auth store (allowed; not vault-content state). |
| IV | Reuse 001, do not duplicate | compliant | Backend imports `voz.auth`, `voz.buscar`, `voz.vault_io` directly. `agt07_diario` is untouched. The dashboard's `tablero/rest.py` mirrors the shape of `voz/rest.py` so a future maintainer reads them as parallels. |
| V | No regression on existing infra | compliant | Mounted on the same uvicorn process via the same `app.router.routes.append(...)` pattern used by `voz/rest.py` (verified at `mcp_server.py:534-536`). Adds new routes under `/tablero/api/*`, never modifying `/voz/api/*`, `/mcp`, or other tools. nginx config adds a new `server` block for `tablero.nosvers.com`, never editing the existing vhost. Rollback = remove the import + the nginx file. |
| VI | Read-only Fase A | compliant | All new HTTP routes are `GET` (plus `OPTIONS` for CORS preflight). No `POST`/`PUT`/`PATCH`/`DELETE`. Verifiable by `grep -E '\"(POST\|PUT\|PATCH\|DELETE)\"' tablero/rest.py` returning zero matches. |
| VII | Real multi-user | compliant | Every endpoint validates JWT via `voz.auth.validar_token`; `sub in {angel, africa}` enforced. The timeline endpoint serves both authors interleaved (no per-user filtering server-side); the frontend "filter by author" is a UI affordance. |
| VIII | Light stack | compliant | Vite + React 18 + TypeScript + Tailwind + shadcn/ui — no Next, no Remix. Backend is FastAPI/Starlette only, mounted inside the existing uvicorn — no new web server. |
| IX | Observability | compliant | Backend logs to the same `logging` channel as `voz.rest` (request id, sub, route, latency, status). Critical 5xx → existing Telegram alert path via the running MCP server's `notify()` helper, with in-process dedup to avoid spam. |
| X | Security baseline | partial — see Complexity Tracking | HTTPS + Let's Encrypt + HSTS + strict CORS + rate-limit are all in plan. The remaining gap is token TTL: `voz.auth` issues access tokens with a 365-day TTL and has no refresh-token scheme; constitution X targets ≤ 15 min access + ≤ 30 day refresh. Justified deviation recorded below. |

**Gate decision**: PASS for Phase 0. The single partial on Principle X is recorded in Complexity Tracking with a concrete follow-up; it does **not** block Fase A because (a) the long-lived token comes from the inherited 001 auth scheme, (b) revocation is available (`voz.auth.revocar_token`), (c) the dashboard makes the situation no *worse* than it already is for the voz PWA.

## Project Structure

### Documentation (this feature)

```text
specs/001-second-brain-fase-a/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output — local dev + deploy
├── contracts/
│   ├── timeline.openapi.yaml
│   ├── buscar.openapi.yaml
│   ├── nota.openapi.yaml
│   └── whoami.openapi.yaml
├── checklists/
│   └── requirements.md
└── tasks.md             # Phase 2 output (created by /speckit-tasks)
```

### Source Code (repository root)

Runtime code lives in **two new directories** under `/home/nosvers/`, parallel to the existing `voz/`:

```text
/home/nosvers/
├── voz/                                 # untouched — Constitution V
├── tablero/                             # NEW — backend REST extension (Python)
│   ├── __init__.py
│   ├── rest.py                          # Starlette routes + CORS + ROUTES list
│   ├── timeline.py                      # listar_timeline(desde, hasta, autor, etiqueta)
│   ├── nota.py                          # leer_nota_md(path) + path-safety validation
│   ├── log.py                           # structured logger + Telegram alerter
│   └── tests/
│       ├── test_auth_gate.py
│       ├── test_timeline.py
│       ├── test_buscar_proxy.py
│       └── test_nota_path_safety.py
├── tablero/web/                         # NEW — frontend SPA (TypeScript)
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   ├── postcss.config.js
│   ├── index.html
│   ├── public/
│   │   └── favicon.svg
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── lib/
│       │   ├── api.ts                   # fetch wrapper + JWT injection
│       │   ├── auth.ts                  # localStorage token store + auto-refresh stub
│       │   ├── cache.ts                 # IndexedDB ring buffer of last 30 notes
│       │   ├── format.ts                # date formatting (es-ES)
│       │   └── markdown.tsx             # react-markdown wrapper + attachment rewriting
│       ├── components/
│       │   ├── AuthorChip.tsx
│       │   ├── TagChip.tsx
│       │   ├── TimelineList.tsx
│       │   ├── TimelineItem.tsx
│       │   ├── FilterBar.tsx
│       │   ├── SearchBar.tsx
│       │   ├── NoteDetail.tsx
│       │   ├── EmptyState.tsx
│       │   └── OfflineBanner.tsx
│       ├── pages/
│       │   ├── Login.tsx
│       │   └── Dashboard.tsx
│       └── styles/
│           └── globals.css
└── mcp_server.py                        # MINIMAL edit — import tablero.rest.ROUTES (3 lines, mirrors voz/rest import)
```

**Structure Decision**: Web application split (Option 2 from the template), with the backend living **inside** the existing nosvers-mcp Python process (no new service) and the frontend served as static files by nginx. We chose `/home/nosvers/tablero/` over `/home/nosvers/dashboard/` because the latter already hosts an unrelated Flask trading dashboard (`/home/nosvers/dashboard/app.py`); collision would create confusion. `tablero` also mirrors the chosen subdomain `tablero.nosvers.com`, a useful 1:1 mapping when grepping logs.

The single `mcp_server.py` edit is additive and mirrors the existing `voz.rest` import block exactly — failing safely with a logged warning if the import errors, so a botched dashboard module cannot take down the MCP service.

## Complexity Tracking

> Fill ONLY if Constitution Check has violations that must be justified

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| **Principle X — token TTL deviation** (access tokens live 365 days; no refresh-token mechanism; constitution targets ≤ 15 min access + ≤ 30 day refresh, revocable on use) | Constitution IV (Reuse 001) takes precedence: rebuilding the auth scheme inside 002 would (a) fork the auth contract between voz and tablero, (b) require regenerating tokens for users with the voz PWA, (c) push 002 past its Fase A scope into 001 territory. Tokens remain individually revocable via `voz.auth.revocar_token`. The dashboard makes the situation no worse than it already is for the existing PWA. | (1) Layering a separate refresh-token scheme just for the dashboard would create two parallel auth paths and double the surface for bugs/regressions; rejected as worse than the long-lived TTL. (2) Forcing 001 to add refresh tokens *before* 002 ships would push Angel's first dashboard demo back by weeks for a problem with a known mitigation (revocation). Rejected on velocity. **Follow-up recorded as Fase B candidate**: track in `MEMORY.md` and the project tracker as "001 amendment: refresh tokens"; once delivered, 002 picks it up transparently because the dashboard only calls `validar_token`. |

## Phase 0: Research

Status: complete. See `research.md` for resolution of the single non-trivial choice (in-process import of `dia_buscar` vs. MCP transport) and the smaller decisions (markdown renderer selection, IndexedDB library, frontend routing, attachment delivery path, rate-limit layer placement).

## Phase 1: Design

Status: complete. Artifacts:

- `data-model.md` — entities, endpoint shapes, validation rules, error model.
- `contracts/*.openapi.yaml` — one OpenAPI 3.1 file per endpoint (timeline, buscar, nota, whoami). These are the contract between the React app and the FastAPI backend; the tests in `tablero/tests/` are written against these contracts.
- `quickstart.md` — exact commands to run locally (`uvicorn` + `vite dev`), to test against the real vault, to package the build, and to wire nginx for `tablero.nosvers.com`.

**Agent context update**: The project's `CLAUDE.md` files are intentionally **not** mutated by this plan — the parent `/home/nosvers/CLAUDE.md` describes the entire NosVers org and is owned by Angel; the subproject `/home/nosvers/specs/second-brain-dashboard/CLAUDE.md` already points to "the current plan". A `<!-- SPECKIT START -->` / `<!-- SPECKIT END -->` block could be inserted, but doing so risks confusing the parent CLAUDE.md's manually-curated structure; instead, the plan path is recorded in `.specify/feature.json` (already done by `/speckit-specify`).

## Post-Design Constitution Re-check

Re-evaluating after the design artifacts exist:

- **VIII (Light stack)** — re-confirmed: the OpenAPI files validate that all four endpoints are JSON+GET, with body shapes a frontend can deserialize without a heavy client lib (`fetch` + `JSON.parse`).
- **III (Vault as truth)** — re-confirmed: the OpenAPI for `/tablero/api/nota` returns `{ frontmatter, body_markdown, path, mtime }` where `mtime` is the cache key for the frontend; there is no opaque ID, no DB row, no surrogate state.
- **X (Security)** — partial remains partial; the OpenAPI for `/tablero/api/whoami` returns the token's `exp` so the frontend can pre-emptively redirect to login before a request 401s on a long-expired token (mitigates one symptom of the long TTL).

**Gate decision (post-design)**: PASS. Phase 2 (`/speckit-tasks`) may proceed.

## Phase 2 outlook (for `/speckit-tasks`)

A natural task decomposition, grouped by user story per the tasks template:

1. **Setup** — create `tablero/` and `tablero/web/` skeletons; pin dependencies.
2. **Foundational** — `tablero.rest` Starlette skeleton with CORS + JWT gate; `mcp_server.py` patch to mount routes; nginx site for `tablero.nosvers.com` (HTTP only first, HTTPS in the deploy step).
3. **US1 (P1, MVP)** — `/tablero/api/timeline` GET; React `<TimelineList>` + `<TimelineItem>` + `<AuthorChip>`; Login + token store; the cold-load Lighthouse measurement.
4. **US2 (P2)** — `/tablero/api/timeline` filter params; React `<FilterBar>`; filter persistence in URL query string.
5. **US3 (P2)** — `/tablero/api/buscar` GET (thin proxy over `dia_buscar_impl`); React `<SearchBar>` with debounce; result-row component re-using `<TimelineItem>` plus snippet.
6. **US4 (P3)** — `/tablero/api/nota` GET (with path-safety validation); React `<NoteDetail>` with `react-markdown` + attachment rewriting; nginx static map for `/attachments/`.
7. **Polish** — OfflineBanner + IndexedDB ring buffer (FR-016); 5xx Telegram alerter (FR-019); Lighthouse + p95 latency measurement script; smoke checklist against existing services (Constitution V) before "Fase A done".
