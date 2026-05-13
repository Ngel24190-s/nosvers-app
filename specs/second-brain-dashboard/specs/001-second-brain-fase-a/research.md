# Phase 0 Research — Second Brain Dashboard Fase A

**Date**: 2026-05-13

Resolves the open architectural decisions surfaced by `spec.md` + the Technical Context in `plan.md`. There is exactly one *non-trivial* decision (how the backend reaches `dia_buscar`) plus four secondary picks for the frontend.

---

## D1 — How does the dashboard backend invoke `dia_buscar`?

**Decision**: **In-process Python import** — `from voz.buscar import dia_buscar_impl` inside `tablero/rest.py`, called synchronously per request. The dashboard REST handler is a thin async wrapper that schedules `dia_buscar_impl` on the default executor when needed; for the current vault size it stays synchronous because file I/O completes in tens of ms.

**Rationale**:
- The `nosvers-mcp` service already imports the same module to back the MCP tool exposed at `/mcp` (verified at `mcp_server.py:363`: `from voz.buscar import dia_buscar_impl as _voz_buscar_impl`). Adding a second importer in `tablero/rest.py` is the **same pattern**, not a new dependency surface.
- It satisfies Constitution II ("MCP-first") on the *correct* reading: "the logic lives in the MCP tool's implementation". The `dia_buscar_impl` function is *the* implementation; the MCP tool wrapping it (`mcp_server.py:451`) and the dashboard endpoint wrapping it would both be thin adapters. Neither adapter owns logic. The principle does not require us to round-trip through the MCP transport.
- Zero new latency. A round-trip through `stdio` or HTTP MCP would add 5–50 ms per call on top of the actual search time — meaningful against the 500 ms p95 budget (SC-003) and indistinguishable on the happy path from a direct call.
- Zero new failure modes. No new transport to retry / time out / detect-disconnection-of.

**Alternatives considered**:

1. **HTTP MCP round-trip** (`POST /mcp/tools/dia_buscar` from the dashboard backend to itself).
   - Rejected. Doubles I/O and introduces a circular dependency on the very service the backend lives in. It also requires the backend to hold and present an MCP token — adding a credential surface the dashboard does not otherwise need.
2. **stdio-based MCP subprocess** (spawn a separate Python process speaking MCP over stdin/stdout, dashboard sends JSON-RPC).
   - Rejected. Same logic-duplication argument as (1) plus process management overhead, plus our hosting model is one uvicorn process; spawning subprocesses per request is anti-pattern at this scale.
3. **Shared library, two services** (factor `voz.buscar` into a pip-installed wheel imported by both `nosvers-mcp` and a hypothetical `nosvers-tablero` service).
   - Rejected for Fase A. There is no operational reason to split processes (Constitution V favors fewer moving parts) and a wheel would add packaging ceremony that no human in this org would maintain. We can do this later if we ever need horizontal scaling, but YAGNI today.

---

## D2 — Markdown renderer for the note detail view

**Decision**: **`react-markdown` v9** with `remark-gfm` and `rehype-highlight`, configured to render to React elements (not raw HTML). Custom transformer rewrites `attachments/...` image src to `/attachments/...` (absolute path served by nginx).

**Rationale**:
- `react-markdown` is the de facto choice for React Markdown rendering, mature (10y), minimal in size (~30 KB gzipped including its deps), and stays on the strict path (no innerHTML by default).
- `remark-gfm` adds tables, task lists, strikethrough — patterns we expect in Angel's notes.
- `rehype-highlight` covers basic code-block highlighting without a multi-megabyte language pack (lazy-loaded languages as needed).
- Image src rewriting via the `urlTransform` (or `components.img`) hook is a one-liner.

**Alternatives considered**:
- `markdown-it` + JSX wrapper — more ceremony for the same result; less idiomatic in React.
- `marked` — would force us to use `dangerouslySetInnerHTML`; rejected for XSS hygiene.

---

## D3 — IndexedDB library for the 30-note ring buffer

**Decision**: **`idb-keyval`** (~600 bytes gzipped) — primitive `get`/`set`/`del`/`keys` over IndexedDB.

**Rationale**:
- We need a tiny key-value store keyed by note path. No queries, no indexes, no schema.
- 600 bytes vs. Dexie's ~20 KB matters for the SC-001 budget.
- The 30-note cap is enforced by the app (sort by `mtime`, prune oldest) — the library does not need to know.

**Alternatives considered**:
- Native IndexedDB API — viable but verbose; idb-keyval is a Pareto improvement at trivial cost.
- Dexie.js — overkill for one untyped table.
- localStorage — synchronous (blocks the main thread) and limited to ~5 MB; markdown bodies can blow that fast.

---

## D4 — Frontend routing

**Decision**: **No router** in Fase A. The app has effectively two views: a Dashboard (timeline + filters + search + detail-as-side-panel) and Login. State is managed in a top-level React component; the detail "panel" is conditionally rendered, not URL-based. The URL query string holds filter state for shareability/back-button consistency (e.g., `?autor=africa&desde=2026-04-01`).

**Rationale**:
- Loading `react-router` adds ~12 KB gzipped for two views; doesn't justify the cost on the 4G budget.
- Filter state in `URLSearchParams` is cheap, native, and gives the back button correct semantics out of the box.

**Alternatives considered**:
- `react-router` v6 — keep in mind for Fase B if the app grows to multiple distinct pages (kanban, settings, etc.).
- `wouter` — viable lightweight alternative if a router becomes needed; deferred.

---

## D5 — Where the attachment images are served from

**Decision**: nginx serves a **read-only** static map at `/attachments/` from `/home/nosvers/public_html/knowledge_base/dia/audio/` (and similar attachment subfolders). The path-rewriting transformer in `react-markdown` turns `attachments/...` references in note bodies into `/attachments/...` URLs.

**Rationale**:
- The vault already has these files at well-known paths; serving them via nginx is zero-code on the application side.
- Nginx applies the same TLS, gzip, and access logging as the rest of `tablero.nosvers.com`.
- Authentication: in Fase A, the attachments endpoint is **public read** under the assumption that knowing the exact file path is itself a weak secret (paths are non-guessable: `audio/2026-05-13/17-23-45_angel.opus`). If this turns out to be too permissive, Fase B adds an `auth_request` directive to nginx that calls a `tablero` endpoint to validate JWT before serving. We'd rather ship Fase A and harden after a real review than block on a hypothetical.

**Alternatives considered**:
- Stream attachments through the FastAPI backend with JWT auth on every byte — wasteful for tens-of-MB audio files; we'd quickly regret it.
- Pre-sign URLs with short-TTL HMACs — complexity that isn't justified for two users with browser-cached tokens.

---

## D6 — Rate-limiting layer

**Decision**: Apply rate-limiting at the **nginx** layer using `limit_req_zone` and `limit_req` directives, scoped per IP (with `limit_req_zone $binary_remote_addr zone=tablero_api:10m rate=20r/s`). Backend FastAPI also keeps a soft per-`sub` counter in an in-memory dict to detect runaway clients but does not return 429 from the application layer in Fase A.

**Rationale**:
- nginx rate-limit is battle-tested and zero cost in the application code.
- Per-IP is sufficient for two known users on home networks; per-sub at the backend gives us a diagnostic without enforcement (we can promote to enforcement in minutes if needed).

**Alternatives considered**:
- `slowapi` (FastAPI-side Redis-backed rate-limit) — requires Redis; rejected (Constitution III: no new persistence).
- Pure in-process token bucket — works but is duplicate effort given nginx is already in the path.

---

## Summary of decisions

| ID | Topic | Decision |
|----|-------|----------|
| D1 | Backend → `dia_buscar` transport | In-process import of `voz.buscar.dia_buscar_impl` |
| D2 | Markdown renderer | `react-markdown` + `remark-gfm` + `rehype-highlight` |
| D3 | IndexedDB library | `idb-keyval` |
| D4 | Frontend routing | None; URL search params hold filter state |
| D5 | Attachment delivery | nginx static map at `/attachments/` |
| D6 | Rate-limit layer | nginx `limit_req`; optional in-process per-sub counter for telemetry |

No `NEEDS CLARIFICATION` markers from `spec.md` remain unresolved.
