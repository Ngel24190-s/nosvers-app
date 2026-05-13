---
description: "Task list for Second Brain Dashboard Fase A (MVP read-only)"
---

# Tasks: Second Brain Dashboard — Fase A (MVP read-only)

**Input**: Design documents from `/home/nosvers/specs/second-brain-dashboard/specs/001-second-brain-fase-a/`

**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/timeline.openapi.yaml, contracts/buscar.openapi.yaml, contracts/nota.openapi.yaml, contracts/whoami.openapi.yaml, quickstart.md

**Tests**: Smoke tests only — minimal coverage for the auth gate, the timeline payload shape, the search proxy round-trip, and the note path-safety check. No exhaustive TDD; the constitution does not mandate it for Fase A and spec.md does not request it.

**Organization**: Tasks are grouped by user story (US1 P1, US2 P2, US3 P2, US4 P3) so each story is independently implementable and shippable. Phase boundaries are checkpoints — STOP at each and validate before moving on.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Task can run in parallel (different file from siblings, no incomplete dependencies).
- **[Story]**: User story label — only present on user-story phase tasks. Setup, Foundational, and Polish phases have no label.

## Path Conventions

This is a **web application** split across two new top-level directories under `/home/nosvers/`:

- Backend: `/home/nosvers/tablero/` (Python, mounted on the existing `nosvers-mcp` uvicorn at `:8765`).
- Frontend: `/home/nosvers/tablero/web/` (Vite + React + TypeScript single-page app, built to `tablero/web/dist/`, served by nginx).
- Design artifacts (read-only references): `/home/nosvers/specs/second-brain-dashboard/specs/001-second-brain-fase-a/`.

Existing repo state (Constitution V — must remain untouched): `/home/nosvers/voz/*`, `/home/nosvers/agents/agt07_diario/`, `/home/nosvers/mcp_server.py` (only a 3-line additive edit is allowed), nginx config for `voz.nosvers.com` and `nosvers.com`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the empty skeletons and pin dependencies so all later tasks have a place to drop files.

- [X] T001 Create the backend module skeleton at `/home/nosvers/tablero/` with empty `__init__.py`, `rest.py`, `timeline.py`, `nota.py`, `log.py`, and `tests/__init__.py` files (zero implementation; just files so imports resolve).
- [X] T002 [P] Create the frontend skeleton at `/home/nosvers/tablero/web/` by running `npm create vite@latest . -- --template react-ts` (when prompted, accept overwrite of empty dir). Result: `package.json`, `tsconfig.json`, `vite.config.ts`, `index.html`, `src/main.tsx`, `src/App.tsx`.
- [X] T003 [P] Add Tailwind + shadcn dependencies to `/home/nosvers/tablero/web/package.json` and initialize: `npm install -D tailwindcss postcss autoprefixer && npx tailwindcss init -p`, then create `/home/nosvers/tablero/web/tailwind.config.ts`, `/home/nosvers/tablero/web/postcss.config.js`, and `/home/nosvers/tablero/web/src/styles/globals.css` with the Tailwind directives. Run `npx shadcn@latest init` accepting Tailwind defaults; pin shadcn output dir to `src/components/ui/`.
- [X] T004 [P] Add the rest of the frontend runtime deps in `/home/nosvers/tablero/web/package.json`: `react-markdown`, `remark-gfm`, `rehype-highlight`, `idb-keyval`, `clsx`, `lucide-react`. Then `npm install`.
- [X] T005 [P] Configure linting and formatting: add `eslint`, `@typescript-eslint/parser`, `eslint-plugin-react` to `/home/nosvers/tablero/web/package.json` devDeps and write `.eslintrc.json`; add a `lint` script. (Backend: no new lint config — relies on the existing project's `voz/*` style.)
- [X] T006 Create `/home/nosvers/tablero/web/.env.development` with `VITE_API_BASE=http://127.0.0.1:8766` and add `/home/nosvers/tablero/web/.env.example` checked-in placeholder. Add `.env.local` to `/home/nosvers/.gitignore` if not already present.

**Checkpoint**: All skeleton files exist; `cd tablero/web && npm run dev` boots Vite (showing the default React page) without errors; `python3 -c "import tablero"` works on the VPS.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Wire up the cross-cutting plumbing that every user story depends on — auth gate, CORS, logging, the `mcp_server.py` mount point, the frontend API client, and the login flow stub. No user-facing feature is built here yet.

**CRITICAL**: User-story phases cannot start until this phase is complete.

- [X] T007 Implement structured logger + Telegram alerter at `/home/nosvers/tablero/log.py`: a `get_logger(name)` returning a `logging.Logger` configured with the same format as `voz.rest`, plus an `alert_critical(error_key, message)` function that calls the `notify()` helper from `mcp_server.py` (import lazily to avoid a circular import) with a 60-second in-memory dedup window per `error_key`.
- [X] T008 Implement the Starlette REST skeleton at `/home/nosvers/tablero/rest.py`: define `_cors_headers()` with `Access-Control-Allow-Origin: https://tablero.nosvers.com` (override to `http://localhost:5173` when `TABLERO_DEV=1` env), an async `_autenticar(request)` that mirrors `voz.rest._autenticar` and additionally rejects `sub` values outside `{angel, africa}`, an `_json(data, status)` helper, and an `options_handler`. Export `ROUTES: list[starlette.routing.Route]` (empty for now); export a `montar_en_fastmcp(app)` helper that appends each route to `app.router.routes` (mirror the `voz.rest` pattern). Wire request-id middleware (read `X-Request-Id` header or `uuid.uuid4().hex[:12]`) and emit one structured log line per request.
- [X] T009 Add the `whoami` and `health` GET handlers to `/home/nosvers/tablero/rest.py`. `health_handler` is unauthenticated and returns `{ok: true, service: "tablero", version: "0.1.0"}`. `whoami_handler` requires auth and returns the `identidad` payload exactly per `contracts/whoami.openapi.yaml`. Register both in `ROUTES`. (Constitution VI: GET-only.)
- [X] T010 Patch `/home/nosvers/mcp_server.py` with an additive 3-line block immediately after the existing `voz.rest` mount block (currently at lines 533-539): import `tablero.rest.ROUTES`, append to `app.router.routes`, log success/failure with the same defensive try/except as the voz block. Verify the file diff is exactly 3 lines + 1 try-block; no other edits.
- [X] T011 [P] Implement the frontend HTTP client at `/home/nosvers/tablero/web/src/lib/api.ts`: a `fetchJSON<T>(path, init)` wrapping `fetch`, prepending `import.meta.env.VITE_API_BASE`, injecting `Authorization: Bearer <token>` from `auth.ts`, throwing typed errors for 401/4xx/5xx, returning parsed JSON for 2xx. Generate the TypeScript types from the four OpenAPI files using a minimal hand-coded `src/lib/types.ts` (no codegen tooling) that mirrors `data-model.md`.
- [X] T012 [P] Implement the auth store at `/home/nosvers/tablero/web/src/lib/auth.ts`: `getToken()`, `setToken(jwt)`, `clearToken()` over `localStorage.tablero_token`; a `useIdentity()` React hook that calls `/tablero/api/whoami` on mount and caches the result in React state; an `isExpired(exp)` helper returning true when `Date.now()/1000 >= exp - 60`.
- [X] T013 [P] Implement the Login page at `/home/nosvers/tablero/web/src/pages/Login.tsx`: single `<textarea>` for the JWT, "Entrar" button, on submit calls `setToken` and reloads. Use shadcn `<Card>`, `<Textarea>`, `<Button>`. Style: minimal centered card on the NosVers palette (cream `#FEFAF4` background, green `#5A7A2E` button) — Tailwind classes only.
- [X] T014 [P] Implement the global `App.tsx` shell at `/home/nosvers/tablero/web/src/App.tsx`: conditional render between `<Login>` (no token) and `<Dashboard>` (has token); add a top bar with author chip + logout button + (placeholder) search slot. Use the IndexedDB cache stub from `src/lib/cache.ts` (initialized empty for now).
- [X] T015 [P] Implement `/home/nosvers/tablero/web/src/lib/cache.ts` ring-buffer over `idb-keyval`: `getCachedTimeline()`, `setCachedTimeline(entries)` (cap 30 newest by `ts`), `getCachedNote(path)`, `setCachedNote(path, note)` (cap 30 newest by access time). Used by US1 + Polish for offline.
- [X] T016 Smoke test the foundation: write `/home/nosvers/tablero/tests/test_auth_gate.py` exercising health (200, no auth), whoami without token (401 `auth_invalido`), whoami with a freshly minted Angel JWT (200, `identidad.sub == "angel"`), whoami with a JWT that has `sub: hacker` (401). Run with `cd /home/nosvers && python3 -m pytest tablero/tests/test_auth_gate.py -v`.

**Checkpoint**: Foundation ready. `nosvers-mcp` reloads cleanly with the tablero routes mounted; `/tablero/api/health` returns 200 and `/tablero/api/whoami` correctly accepts/rejects tokens. The React shell shows Login → Dashboard switch driven by the token store. **All four user stories can now be built in parallel** (if staffed); on a single-implementer run, do them in priority order P1 → P2 → P2 → P3.

---

## Phase 3: User Story 1 — Timeline unificado (Priority: P1) 🎯 MVP

**Goal**: An authenticated user lands on the dashboard and sees a merged timeline of Angel + África notes from the last 30 days, ordered by date descending, with author chips.

**Independent Test**: Open the dashboard with a valid Angel JWT → see at least N entries spanning both authors in descending date order. Open with a valid África JWT → identical merged list. Without a token → login screen, no data fetched.

### Backend

- [X] T017 [US1] Implement `listar_timeline(desde, hasta, autor, etiqueta, limit, offset)` in `/home/nosvers/tablero/timeline.py`: call `voz.vault_io.listar_dias(desde, hasta)` to get day files in range, then `voz.vault_io.leer_dia(f)` per file; flatten the resulting `Nota` objects; filter by `autor` (skip if `autor in {"ambos", ""}`) and `etiqueta`; build `TimelineEntry` dicts per `data-model.md` (path = `f"dia/{f.isoformat()}.md#{n.ts}"`, titulo = first non-empty line of `n.texto` capped 120 chars, preview = first 200 chars newline-collapsed, `tiene_audio = n.audio is not None`, `metadata_incompleta = False` for now); sort by `(fecha, ts) DESC`; apply offset/limit. Return list of dicts.
- [X] T018 [US1] Add the timeline GET handler to `/home/nosvers/tablero/rest.py`: `timeline_handler(request)` validates JWT via `_autenticar`, parses query params per `contracts/timeline.openapi.yaml` (defaults: `desde = today-30d`, `hasta = today`, `autor = "ambos"`, `limit = 200`, `offset = 0`), validates dates and enums (return 400 `parametro_invalido` on failure with the offending detail), calls `listar_timeline`, returns `_json({"ok": True, "entradas": ..., "total": ..., "rango": {...}})`. Add `Route("/tablero/api/timeline", timeline_handler, methods=["GET"])` and the matching `OPTIONS` route. Log latency.
- [X] T019 [US1] Smoke test the timeline at `/home/nosvers/tablero/tests/test_timeline.py`: with a real Angel token against the dev uvicorn, `GET /tablero/api/timeline` returns 200 with `ok: true`, `entradas` is a list, every entry has `fecha/autor/etiqueta`, list is sorted descending, default range is last 30 days. Add cases for `autor=africa`, `etiqueta=trabajo`, and a date-range filter.

### Frontend

- [X] T020 [P] [US1] Implement `/home/nosvers/tablero/web/src/components/AuthorChip.tsx`: a small pill component showing "Angel" or "África" with a distinct color per author (Angel = green `#5A7A2E`, África = warm orange — pick the existing NosVers palette accent). Accepts `autor: 'angel' | 'africa'` prop.
- [X] T021 [P] [US1] Implement `/home/nosvers/tablero/web/src/components/TagChip.tsx`: a smaller chip rendering an etiqueta with a muted background.
- [X] T022 [P] [US1] Implement `/home/nosvers/tablero/web/src/lib/format.ts`: `formatDateES(d: string): string` returning `"hoy"`, `"ayer"`, `"hace N días"`, or `"DD MMM"` for dates in the current year, `"DD MMM YYYY"` otherwise. Uses `Intl.DateTimeFormat('es-ES')`.
- [X] T023 [US1] Implement `/home/nosvers/tablero/web/src/components/TimelineItem.tsx`: a clickable card showing `AuthorChip`, formatted date, titulo (fallback "Sin título"), preview (truncated), and the list of TagChips. Calls `onClick(entry)` prop. Styled with Tailwind + shadcn `<Card>`.
- [X] T024 [US1] Implement `/home/nosvers/tablero/web/src/components/TimelineList.tsx`: receives `entries: TimelineEntry[]` and `onSelect(entry)`; renders a vertical list of `TimelineItem`. Empty state when `entries.length === 0` (delegates to `<EmptyState>`, T025).
- [X] T025 [P] [US1] Implement `/home/nosvers/tablero/web/src/components/EmptyState.tsx`: shown when timeline is empty — short helpful copy and a discreet CTA pointing to the voz PWA for capturing the first note.
- [X] T026 [US1] Implement `/home/nosvers/tablero/web/src/pages/Dashboard.tsx`: on mount, call `/tablero/api/timeline` with default params; while loading, render a Tailwind skeleton list (3-4 shimmery rows); on success, render `<TimelineList>`; on 401, call `clearToken()` and reload (returns to Login). Persist the last successful response into IndexedDB via `setCachedTimeline`. On offline / network error, fall back to `getCachedTimeline()` and render `<OfflineBanner>` (T044 — stub it for now if not yet implemented).
- [ ] T027 [US1] Measure cold-load Lighthouse on the timeline page (Slow-4G profile) — record the TTI in `quickstart.md` Section 9. Bundle must be ≤ 200 KB gzipped initial JS; if exceeded, audit deps (lazy-load `rehype-highlight` languages, drop unused shadcn primitives).

**Checkpoint**: US1 done. Angel and África can each log in and see a merged 30-day timeline. SC-001 measurable. STOP — this alone is the MVP and demoable.

---

## Phase 4: User Story 2 — Filtros combinables (Priority: P2)

**Goal**: User can narrow the timeline by author, etiqueta, and custom date range; filters combine with AND and don't reload the page.

**Independent Test**: With the timeline loaded, tick "África only" + "etiqueta nosvers" + "last 7 days" → list narrows to the intersection. Clear all → returns to default.

### Backend

The timeline endpoint already accepts the filter params (T018). This phase mostly verifies + extends edge cases.

- [X] T028 [US2] Extend `/home/nosvers/tablero/tests/test_timeline.py` with three filter cases: combined `autor=africa&etiqueta=nosvers`, `desde=YYYY-MM-DD&hasta=YYYY-MM-DD` covering a 3-day window, and the invalid `hasta < desde` returning 400 `parametro_invalido`.
- [X] T029 [US2] Add `autor=ambos` short-circuit at the start of `listar_timeline` in `/home/nosvers/tablero/timeline.py` to skip the filter loop (small perf win; documents the default).

### Frontend

- [X] T030 [P] [US2] Implement `/home/nosvers/tablero/web/src/components/FilterBar.tsx` using shadcn `<Select>` + `<Popover>` (date range picker). Three controls: author (`angel | africa | ambos`), etiqueta (six fixed values + "todas"), date range (two `<input type="date">` with a "limpiar" button). Emits a `filters` object via `onChange`.
- [X] T031 [US2] Wire `FilterBar` into `Dashboard.tsx`: store filters in `useState` synced to `URLSearchParams` (read on mount, write on change with `history.replaceState`). When filters change, debounce 150 ms and refetch `/tablero/api/timeline`. Render active filter chips above the list with an "x" to remove individually.
- [X] T032 [US2] Add client-side validation: reject `hasta < desde` before fetching (matches FR edge case); show a small inline error in `<FilterBar>`.

**Checkpoint**: US2 done. SC-002 measurable.

---

## Phase 5: User Story 3 — Búsqueda full-text (Priority: P2)

**Goal**: A search bar in the top nav queries `dia_buscar` (debounced) and returns matched notes with author chip, date, and a highlighted snippet.

**Independent Test**: Type a known term ("lombrithé", "composteur") → results appear in under 500 ms p95 with `<mark>` highlights; empty result set shows the "sin resultados" state; rapid typing fires one request, not five.

### Backend

- [X] T033 [US3] Add the buscar GET handler to `/home/nosvers/tablero/rest.py`: parse query params (`q` required, `autor`, `etiqueta`, `desde`, `hasta`, `limite` per `contracts/buscar.openapi.yaml`), call `voz.buscar.dia_buscar_impl(...)` directly (Decision D1), translate the returned dict 1:1 to the response shape, log latency. Return 400 `input_vacio` when `q` is missing/empty.
- [X] T034 [US3] Smoke test at `/home/nosvers/tablero/tests/test_buscar_proxy.py`: empty `q` → 400 `input_vacio`; valid `q` matching a known note → 200 with at least one `SearchHit` containing `<mark>` in `fragmento`; `q` with no matches → 200 with `total: 0` and `resultados: []`; with `autor=angel` filter → only Angel hits.

### Frontend

- [X] T035 [P] [US3] Implement `/home/nosvers/tablero/web/src/components/SearchBar.tsx`: a controlled `<Input>` with a 300 ms debounce; on change, calls `onSearch(query)`. Includes a small `<X>` (lucide-react) to clear.
- [X] T036 [US3] Implement search-result rendering in `/home/nosvers/tablero/web/src/pages/Dashboard.tsx`: when a search query is non-empty, hide `<TimelineList>` and render a results section that reuses `<TimelineItem>` but adds a `dangerouslySetInnerHTML`-safe rendering of `fragmento` (a small `<SearchSnippet>` sub-component that parses the string with a tiny regex allowing only `<mark>…</mark>`, escaping everything else). Sort by relevance order returned from the API.
- [X] T037 [US3] Add the search bar slot in `App.tsx` top bar — always visible on the dashboard.

**Checkpoint**: US3 done. SC-003 measurable.

---

## Phase 6: User Story 4 — Vista detalle nota (Priority: P3)

**Goal**: Clicking a timeline or search result opens a detail panel rendering the note's full markdown with attachment images, code blocks, and frontmatter shown separately.

**Independent Test**: Click an entry with mixed markdown → headings, lists, code blocks, links all render; an embedded image at `attachments/...` shows up via `/attachments/`; close (Esc or back arrow) returns to the previous list state preserving filters and scroll.

### Backend

- [X] T038 [US4] Implement `read_nota(path)` in `/home/nosvers/tablero/nota.py`: parse the `path` into `(date_str, ts)` from `dia/YYYY-MM-DD.md#<ts>`; resolve the day-file absolute path; verify the resolved path lies under `voz.vault_io.DIA_DIR` (compare `Path(...).resolve()` prefixes); raise `PathUnsafe` (custom exception) otherwise. Call `voz.vault_io.leer_dia(date)`; pick the note whose `ts == ts_fragment`; return `{path, frontmatter, body_markdown, mtime, attachments}` where `attachments` is a list built from regex-scanning `body_markdown` for `!\[.*?\]\((attachments/[^)]+)\)` and stat-checking each file.
- [X] T039 [US4] Add the nota GET handler to `/home/nosvers/tablero/rest.py`: validate JWT, read `path` query param (400 `parametro_invalido` if missing), call `read_nota(path)`, return the `NoteFull` payload per `contracts/nota.openapi.yaml`. Map `PathUnsafe` → 400 `path_unsafe`; `FileNotFoundError` / no-matching-`ts` → 404 `not_found`; everything else → 500 `internal_error` + Telegram alert via `log.alert_critical`.
- [X] T040 [US4] Smoke test at `/home/nosvers/tablero/tests/test_nota_path_safety.py`: requesting `path=../../../etc/passwd` → 400 `path_unsafe`; requesting `path=dia/9999-99-99.md#x` → 404 `not_found`; requesting a real path from the timeline → 200 with non-empty `body_markdown`; requesting without auth → 401.

### Frontend

- [X] T041 [P] [US4] Implement `/home/nosvers/tablero/web/src/lib/markdown.tsx`: a thin wrapper around `react-markdown` configured with `remarkPlugins=[remarkGfm]`, `rehypePlugins=[rehypeHighlight]`, and a custom `components.img` that rewrites `src="attachments/..."` to `src="/attachments/..."` and falls back to a placeholder `<div class="broken-img">` when `attachments[].exists === false` (passed in via prop).
- [X] T042 [US4] Implement `/home/nosvers/tablero/web/src/components/NoteDetail.tsx`: receives `nota: NoteFull | null` and `onClose()`. Renders a side panel (desktop ≥ 1024 px) or full-screen sheet (mobile) via shadcn `<Sheet>`. Top section: chip-style frontmatter (autor, fecha, etiqueta, origen) styled distinctly from the body. Body section: the markdown renderer from T041. Bottom: a "cerrar" button + handle Esc keypress + browser back-button. Cache the fetched `NoteFull` via `cache.setCachedNote`.
- [X] T043 [US4] Wire `<NoteDetail>` into `Dashboard.tsx`: clicking a `TimelineItem` or search result fetches `/tablero/api/nota?path=...`, sets `selectedNote` state, renders `<NoteDetail nota={selectedNote} onClose={() => setSelectedNote(null)} />`. Preserve scroll position by not unmounting the list; the panel overlays it.

**Checkpoint**: US4 done. SC-004 measurable.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Wrap-up tasks that touch multiple stories or operationalize the deploy.

- [X] T044 [P] Implement `/home/nosvers/tablero/web/src/components/OfflineBanner.tsx`: shown when `navigator.onLine === false` OR the last fetch failed with a network error; reuses `cache.getCachedTimeline()` for the list. Disappears when connectivity returns.
- [X] T045 [P] Implement the 5xx Telegram alert dedup in `/home/nosvers/tablero/log.py` (referenced by T007 — finalize): use `(error_key, now()/60)` minute buckets in an in-memory dict to throttle alerts to once per minute per key. Tested by hand with a deliberately broken request.
- [ ] T046 [P] Write the Lighthouse + latency measurement script at `/home/nosvers/tablero/scripts/measure_phase_a.sh`: runs `lighthouse https://tablero.nosvers.com --preset=desktop --form-factor=mobile --throttling-method=simulate`, plus an `httpx`-based loop hitting `/tablero/api/buscar?q=<word>` 100 times to compute p95 latency. Prints both numbers; used in the SC verification step.
- [ ] T047 Wire the nginx vhost: copy the config from `quickstart.md` Section 7 to `/etc/nginx/sites-available/tablero.nosvers.com`, symlink to `sites-enabled`, ensure the `limit_req_zone` is declared in `nginx.conf`, run `nginx -t`, `systemctl reload nginx`. DO NOT touch other vhosts.
- [ ] T048 Issue Let's Encrypt cert per `quickstart.md` Section 8 (requires DNS A record for `tablero.nosvers.com` pointing to the VPS).
- [X] T049 Run the **Constitution V regression smoke checklist** (mandatory before "Fase A done"):
  - [ ] `curl -s http://localhost:8765/voz/api/health` returns `{"ok": true, "service": "voz"}` (voz REST still healthy).
  - [ ] Most recent log file at `/home/nosvers/logs/agt07_diario*.log` has a today-dated entry (cron still firing).
  - [ ] `systemctl is-active nosvers-bot` returns `active`.
  - [ ] `curl -sI https://nosvers.com/ | head -1` returns `HTTP/2 200` or `HTTP/1.1 200 OK` (WordPress still reachable).
  - [ ] `systemctl is-active freqtrade.service grid_trading.service` (or equivalent) — bots still up.
  - All five must pass before continuing.
- [ ] T050 Run the **SC verification gate**:
  - [ ] Lighthouse Slow-4G TTI on a timeline of 30 notes ≤ 2 s (SC-001).
  - [ ] Manual filter toggle: visible list updates ≤ 200 ms (SC-002).
  - [ ] T046 script: search p95 ≤ 500 ms (SC-003).
  - [ ] Manual click-to-detail: visible content ≤ 300 ms (SC-004).
  - [ ] Unauthenticated `curl /tablero/api/timeline` → 401 in ≤ 50 ms (SC-006).
  - [ ] `grep -E '"(POST|PUT|PATCH|DELETE)"' /home/nosvers/tablero/rest.py` returns nothing (Constitution VI / FR-014).
- [ ] T051 Run the **manual UAT checklist** in two browser sessions (one with Angel's token, one with África's): both see the same 30-day mix; both can filter to "only the other"; both can search "nosvers"; both can open a detail; both can close it.
- [ ] T052 Document the deploy in `/home/nosvers/specs/second-brain-dashboard/specs/001-second-brain-fase-a/quickstart.md` Section 9 — fill in the measured numbers and tick the checklist.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately.
- **Foundational (Phase 2)**: Depends on Setup. BLOCKS all user-story phases.
- **User Stories (Phases 3-6)**: All depend on Foundational. Within a single-implementer run, do P1 → P2 → P2 → P3. With more than one implementer they can run in parallel.
- **Polish (Phase 7)**: T044-T046 can start during US1+US2+US3+US4. T047-T052 must wait for at least US1 to be deployable; they finalize the deploy.

### User Story Dependencies

- **US1 (P1)**: Independent. Needs only the foundational JWT gate.
- **US2 (P2)**: Lightly extends US1 (the same `/tablero/api/timeline` endpoint, now with active filter params). Practically: do US1 first, then US2 layers on top.
- **US3 (P2)**: Independent of US2 — pure search path; shares the foundation only.
- **US4 (P3)**: Triggered by clicks from US1 or US3 results, but the detail endpoint and component are otherwise independent. Build last because the smallest incremental value vs. the others.

### Within Each User Story

- Backend handler → frontend component → wired into Dashboard.
- Smoke test sits after the backend handler so 401/200/400 paths are covered before the UI is even attached.

### Parallel Opportunities

- **Phase 1**: T002-T005 all run in parallel after T001 lands the directory.
- **Phase 2**: T011-T015 run in parallel once T008/T010 land (different frontend files).
- **Within a story**: components marked [P] (T020/T021/T022/T025/T030/T035/T041/T044/T045/T046) are independent files.
- **Across stories**: with two implementers, one tackles US1+US2 (backend timeline + filters) while the other tackles US3 (backend search). US4 waits because the frontend reuses pieces from US1.

---

## Parallel Example: User Story 1

```bash
# After T017 (backend listar_timeline) + T018 (handler) + T019 (smoke) are green,
# launch all the UI primitives together (different files):
Task: "T020 Implement AuthorChip in tablero/web/src/components/AuthorChip.tsx"
Task: "T021 Implement TagChip in tablero/web/src/components/TagChip.tsx"
Task: "T022 Implement formatDateES in tablero/web/src/lib/format.ts"
Task: "T025 Implement EmptyState in tablero/web/src/components/EmptyState.tsx"

# Then T023 (TimelineItem) consumes T020+T021+T022, T024 (TimelineList) consumes T023+T025,
# T026 (Dashboard) consumes T024 — sequential after the parallel burst.
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1: Setup (T001-T006).
2. Phase 2: Foundational (T007-T016).
3. Phase 3: US1 (T017-T027).
4. **STOP and VALIDATE**: log in as Angel, log in as África, take a Lighthouse snapshot, run the Constitution V smoke (T049 subset).
5. Demo to the CEO. If approved, continue.

### Incremental Delivery

1. Setup + Foundational + US1 → MVP. Demo. Get green light.
2. + US2 (filters) → second demo.
3. + US3 (search) → third demo.
4. + US4 (detail) → "Fase A complete" deliverable.
5. Polish (Phase 7) wraps it before the Telegram-to-CEO notification.

### Parallel Team Strategy

Single-implementer in this run — parallel team note retained for the future:

1. All implementers complete Setup + Foundational together.
2. After Foundational:
   - Backend specialist: T017, T018, T019, T028, T029, T033, T034, T038, T039, T040.
   - Frontend specialist: T020-T027 + T030-T032 + T035-T037 + T041-T043.
3. Each story converges and integrates independently.

---

## Notes

- [P] tasks = different files, no incomplete dependencies.
- [Story] label maps task to a specific user story for traceability.
- Each user story is independently completable and testable per the spec.md "Independent Test" sections.
- Smoke tests verify the contract endpoints; they are not a substitute for the manual UAT in T051.
- Commit after each task (or each tight logical group) — the parent `/home/nosvers` repo is on `main`; keep commit messages prefixed `tablero:` to make later `git log --grep=tablero` filters easy.
- STOP at any checkpoint to validate before continuing.
- Avoid: vague tasks, same-file conflicts (each [P] task is in a distinct file), cross-story dependencies that would break independence.
