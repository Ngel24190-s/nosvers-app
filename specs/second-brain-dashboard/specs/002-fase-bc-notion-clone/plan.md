# Implementation Plan: Second Brain Dashboard — Fase B+C (Notion-clone real)

**Branch**: `002-fase-bc-notion-clone` (monorepo `/home/nosvers/`, rama `main` por convenio Fase A)

**Date**: 2026-05-13

**Spec**: [spec.md](./spec.md) · [decisions.md](./decisions.md)

**Input**: Feature specification from `specs/002-fase-bc-notion-clone/spec.md`

## Summary

Extender la arquitectura ya consolidada en Fase A (FastAPI/Starlette `tablero/rest.py` + React+Vite+Tailwind+shadcn/ui bajo `tablero/web/`) para entregar los 14 sub-componentes de Fase B+C. Toda escritura al vault pasa por nuevos endpoints `POST/PATCH/DELETE` bajo el prefijo `/tablero/api/v2/` (los endpoints `GET` de Fase A bajo `/tablero/api/` permanecen intactos). Las invocaciones a tools MCP (`dia_capturar`, `agente_ejecutar`, etc.) se hacen por import directo de las funciones `voz/*` (D-001). La concurrencia se gestiona con optimismo (header `If-Match: <modified_at>` + HTTP 409 — D-003). Drag-and-drop con `@dnd-kit`. Grafo con `d3-force` sobre `<canvas>`. Integración Google Calendar/Gmail via REST directo a `googleapis.com` con OAuth refresh token almacenado server-side (D-005). Vault permanece markdown puro; toda "base de datos" tipo Notion es un `.md` con frontmatter.

## Technical Context

**Language/Version**: Python 3.11 (backend, mismo proceso uvicorn que `voz.rest` y MCP) · TypeScript 5.x (frontend, Vite 5 + React 18).

**Primary Dependencies**:
- Backend (nuevas): `httpx` (cliente Google APIs), `google-auth` (OAuth refresh). Reuso 001: `voz/auth.py`, `voz/buscar.py`, `voz/capturar.py`, `voz/vault_io.py`, `voz/contexto.py`. Reuso Fase A: `tablero/timeline.py`, `tablero/nota.py`, `tablero/log.py`.
- Frontend (nuevas): `@dnd-kit/core`, `@dnd-kit/sortable`, `@dnd-kit/utilities`, `d3-force`, `d3-selection`, `d3-zoom`, `cmdk` (command palette base). Reuso Fase A: `react`, `react-dom`, `react-markdown`, `remark-gfm`, `rehype-highlight`, `idb-keyval`, `clsx`, `lucide-react`, Tailwind + shadcn/ui.

**Storage**: vault markdown files bajo `/home/nosvers/public_html/knowledge_base/` (single source of truth, Constitución III). Índice de backlinks in-memory en el proceso uvicorn, reconstruido en startup (D-004). Cliente: localStorage para preferencias de vista y borradores de captura; IndexedDB (`idb-keyval`) reutilizado para caché de timeline.

**Testing**: pytest (backend, extiende suite Fase A 78 tests · target cobertura ≥ 80% en módulos nuevos, D-010) · vitest (frontend unitarios) · playwright smoke E2E para US1/US2/US4/US5.

**Target Platform**: Linux Hostinger VPS (srv1313138.hstgr.cloud, IPv4 72.61.160.108). Frontend servido por nginx desde `tablero/web/dist`; backend por uvicorn proxypaseado en `/tablero/api/*`. Subdominio dev `tablero.72.61.160.108.nip.io` (ya activo), prod futuro `tablero.nosvers.com`. Clientes: Chrome móvil Android, Firefox/Chrome desktop Linux, Safari iOS ocasional.

**Project Type**: Web application — backend FastAPI/Starlette + frontend SPA React+Vite.

**Performance Goals**:
- Captura `Ctrl+N` → nota en timeline ≤ 5 s sobre 4G (SC-001).
- Edición guardar → render ≤ 1 s desktop (SC-002).
- Cambio de vistas (lista/tabla/kanban/calendario/galería) ≤ 200 ms (SC-003).
- Command palette `Ctrl+K` abre ≤ 100 ms, resultados ≤ 300 ms p95 (SC-004).
- Drag-and-drop kanban → frontmatter actualizado ≤ 500 ms (SC-005).
- Latencia inicial dashboard < 2 s sobre 4G (SC-008, alineado con Lighthouse budget de la constitución).

**Constraints**:
- Constitución I (Soberanía): nada propietario nuevo.
- Constitución II (MCP-first): tools MCP siguen siendo dueñas de la lógica; el dashboard llama por import directo (D-001) — sigue siendo "thin client" lógicamente.
- Constitución III (Vault SoT): nada de SQLite/Postgres/Redis-as-store; índice de backlinks es derivado y rebuilt-from-vault.
- Constitución V (No regresión): 78 tests Fase A pasan; `/tablero/api/*` (sin `/v2/`) intacto.
- Constitución VII (Multi-user real): JWT con paridad Angel/África.
- Constitución VIII (Stack ligero): Vite+React+TS+Tailwind+shadcn, sin Next/Remix/Astro. Backend en el mismo uvicorn.
- Constitución X (Security): HTTPS+HSTS prod, access tokens ≤ 15 min, refresh ≤ 30 d, rate limit nginx, CORS estricto, secrets server-side.

**Scale/Scope**:
- Vault objetivo 1.000 notas + 5.000 wiki-links (SC-010). Grafo soporta 500 visibles con sampling automático.
- 2 usuarios activos (Angel + África); diseñado para concurrencia baja pero correcta (optimistic concurrency cubre el caso edge de doble pestaña).
- 14 sub-componentes; el plan los implementa secuencialmente agrupados por dependencia y prioridad spec.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Estado | Justificación / Mitigación |
|---|---|---|
| **I. Soberanía** | ✅ Compliant | Toda lógica corre en VPS Hostinger; única nueva integración externa = Google APIs (ya admitidas en proyecto 001 vía conector) usando OAuth refresh token local. Sin Vercel/Supabase/Firebase/etc. |
| **II. MCP-first** | ✅ Compliant | Captura, búsqueda y agentes invocan los mismos `voz/*` que el MCP server expone como tools (`dia_capturar`, `dia_buscar`, `agente_ejecutar`). D-001 hace import in-process — sigue siendo el mismo Python; no se duplica lógica. |
| **III. Vault SoT** | ✅ Compliant | Toda escritura va a `.md` con frontmatter (D-013 atomic write). Backlinks índice = derivado, rebuilt on startup + write-through (D-004). No se introduce DB. |
| **IV. Reuse 001** | ✅ Compliant | Imports explícitos de `voz/auth.py`, `voz/buscar.py`, `voz/capturar.py`, `voz/vault_io.py`. Nuevos módulos en `tablero/v2/*` solo orquestan/exponen REST; sin duplicar lógica. |
| **V. No regresión** | ✅ Compliant | Endpoints `/tablero/api/*` Fase A intactos (D-014 prefijo `/v2/` para todo lo nuevo). Suite de 78 tests sigue. Verificación: smoke test en quickstart.md + assert en CI. |
| **VI. Read-only Fase A** | ✅ Cycle release | El principio limita Fase A. Fase B+C explícitamente abre el ciclo write (constitución dice: "Capture, edit, delete, kanban moves — all MUST wait for an explicit Fase B/C cycle"). Estamos en ese cycle. |
| **VII. Multi-user real** | ✅ Compliant | JWT `sub` exigido en todos los endpoints write. Paridad Angel/África absoluta (A-005). Logs anotan `editor_sub` vs `autor` para trazabilidad sin restricción de acceso. |
| **VIII. Stack ligero** | ✅ Compliant | Sin Next/Remix/Astro. Dependencias nuevas listadas y justificadas: `@dnd-kit` (drag-and-drop estándar), `d3-force` (sin alternativa lite con la misma calidad de simulación), `cmdk` (paleta de comandos accesible OOTB), `httpx` (cliente HTTP backend para Google), `google-auth` (manejo OAuth refresh). Ninguna es un meta-framework. |
| **IX. Observability** | ✅ Compliant | Cada nuevo endpoint loguea con el mismo formato `rid=… sub=… route=… status=… latency_ms=…` que Fase A. Alertas Telegram para 5xx repetidos vía `alert_critical` ya existente. Frontend errores en console + IndexedDB ring buffer (extendiendo `tablero/web/src/lib/diag.ts` si hace falta). |
| **X. Security baseline** | ✅ Compliant | HTTPS + HSTS ya en nginx Fase A. Access tokens y refresh tokens reutilizados de `voz.auth` (ya cumplen ≤ 15 min / ≤ 30 d). Rate limit nginx para los nuevos endpoints `/tablero/api/v2/*`. CORS ya restringido en `_allowed_origin()`. Secrets Google en `/etc/nosvers/secrets/google.json` con perms `0600` (root-only readable). Versiones pinadas en `package-lock.json` + `pyproject.toml`. |

**Gate result**: PASS. Sin violaciones. No se requiere Complexity Tracking.

**Re-evaluación post-Phase 1** (sección "Post-Design Re-check" al final del documento): mantenida PASS tras escribir `data-model.md` y `contracts/*` — ningún diseño emergente fuerza nuevas dependencias o relaja principios.

## Project Structure

### Documentation (this feature)

```text
specs/002-fase-bc-notion-clone/
├── plan.md              # Este archivo
├── decisions.md         # 15 micro-decisiones técnicas (D-001..D-015)
├── spec.md              # User stories + FRs + SCs
├── research.md          # Phase 0 — investigaciones y elecciones
├── data-model.md        # Phase 1 — entidades + transiciones de estado
├── quickstart.md        # Phase 1 — guía mínima dev → smoke prod
├── contracts/           # Phase 1 — OpenAPI por endpoint nuevo
│   ├── capturar.openapi.yaml
│   ├── nota_editar.openapi.yaml
│   ├── nota_archivar.openapi.yaml
│   ├── nota_restaurar.openapi.yaml
│   ├── vault_tree.openapi.yaml
│   ├── vault_mkdir.openapi.yaml
│   ├── vault_move.openapi.yaml
│   ├── proyectos_list.openapi.yaml
│   ├── proyectos_update.openapi.yaml
│   ├── wiki_index.openapi.yaml
│   ├── infra_status.openapi.yaml
│   ├── agentes_ejecutar.openapi.yaml
│   ├── google_calendar.openapi.yaml
│   └── google_gmail.openapi.yaml
├── checklists/
│   └── requirements.md
└── tasks.md             # Phase 2 (generado por /speckit-tasks)
```

### Source Code (repository root)

```text
/home/nosvers/
├── voz/                         # Proyecto 001 — sin cambios
│   ├── auth.py
│   ├── buscar.py
│   ├── capturar.py              # ← se importa desde tablero/v2
│   ├── vault_io.py              # ← se importa desde tablero/v2
│   ├── contexto.py
│   └── rest.py
│
├── tablero/                     # Proyecto 002 — backend
│   ├── __init__.py
│   ├── rest.py                  # Fase A intacto + monta routes Fase B+C
│   ├── timeline.py              # Fase A
│   ├── nota.py                  # Fase A (lectura) — añade soporte para v2/edit
│   ├── log.py                   # Fase A
│   ├── v2/                      # ← NUEVO — todas las rutas escritura/Fase B+C
│   │   ├── __init__.py
│   │   ├── capturar.py          # POST /tablero/api/v2/capturar
│   │   ├── editar.py            # PATCH /tablero/api/v2/nota
│   │   ├── archivar.py          # POST /tablero/api/v2/nota/archivar
│   │   ├── restaurar.py         # POST /tablero/api/v2/nota/restaurar
│   │   ├── vault_tree.py        # GET  /tablero/api/v2/vault/tree
│   │   ├── vault_mkdir.py       # POST /tablero/api/v2/vault/mkdir
│   │   ├── vault_move.py        # POST /tablero/api/v2/vault/move
│   │   ├── proyectos.py         # GET+PATCH /tablero/api/v2/proyectos
│   │   ├── wiki_index.py        # GET  /tablero/api/v2/wiki-index (lazy index)
│   │   ├── infra.py             # GET  /tablero/api/v2/infra/status (badges)
│   │   ├── agentes.py           # POST /tablero/api/v2/agentes/ejecutar
│   │   ├── google_calendar.py   # GET+POST /tablero/api/v2/google/calendar/events
│   │   ├── google_gmail.py      # GET /tablero/api/v2/google/gmail/threads
│   │   ├── atomic_write.py      # helper tmp→rename (D-013)
│   │   ├── frontmatter.py       # helper parse/serialize seguro (delega en voz.vault_io)
│   │   ├── slug_resolver.py     # resolución de wiki-links (D-002, D-012)
│   │   └── concurrency.py       # decorador If-Match → 409 (D-003)
│   │
│   ├── tests/                   # extiende suite Fase A
│   │   ├── conftest.py          # Fase A
│   │   ├── test_auth_gate.py    # Fase A
│   │   ├── test_timeline.py     # Fase A
│   │   ├── test_buscar_proxy.py # Fase A
│   │   ├── test_nota_path_safety.py  # Fase A
│   │   ├── test_v2_capturar.py        # ← NUEVO
│   │   ├── test_v2_editar.py
│   │   ├── test_v2_archivar.py
│   │   ├── test_v2_restaurar.py
│   │   ├── test_v2_vault_tree.py
│   │   ├── test_v2_vault_move.py
│   │   ├── test_v2_vault_mkdir.py
│   │   ├── test_v2_proyectos.py
│   │   ├── test_v2_wiki_index.py
│   │   ├── test_v2_concurrency.py     # 409 paths
│   │   ├── test_v2_slug_resolver.py
│   │   ├── test_v2_atomic_write.py
│   │   ├── test_v2_infra_status.py
│   │   ├── test_v2_agentes.py
│   │   ├── test_v2_google_calendar.py # mocks httpx
│   │   └── test_v2_google_gmail.py
│   │
│   ├── scripts/
│   │   └── dev_server.py        # Fase A (sin cambios)
│   │
│   └── web/                     # Proyecto 002 — frontend
│       ├── package.json         # ← actualizado: +@dnd-kit/*, +d3-force, +cmdk
│       ├── vite.config.ts
│       ├── tailwind.config.cjs
│       ├── tsconfig.json
│       └── src/
│           ├── main.tsx
│           ├── App.tsx
│           ├── components/
│           │   ├── AuthorChip.tsx                # Fase A
│           │   ├── EmptyState.tsx
│           │   ├── FilterBar.tsx
│           │   ├── NoteDetail.tsx                # extiende — botón editar/archivar
│           │   ├── OfflineBanner.tsx
│           │   ├── SearchBar.tsx
│           │   ├── TagChip.tsx
│           │   ├── TimelineItem.tsx
│           │   ├── TimelineList.tsx
│           │   ├── CaptureModal.tsx              # ← NUEVO — US1
│           │   ├── NoteEditor.tsx                # ← NUEVO — US2 (markdown + preview)
│           │   ├── ArchiveDialog.tsx             # ← NUEVO — US3
│           │   ├── PapeleraView.tsx              # ← NUEVO — US3 lista archivadas
│           │   ├── ViewSwitcher.tsx              # ← NUEVO — US4 selector
│           │   ├── TableView.tsx                 # ← NUEVO — US4
│           │   ├── KanbanByTagView.tsx           # ← NUEVO — US4 (kanban por etiqueta)
│           │   ├── CalendarMonthView.tsx         # ← NUEVO — US4
│           │   ├── GalleryView.tsx               # ← NUEVO — US4
│           │   ├── CommandPalette.tsx            # ← NUEVO — US5 (cmdk)
│           │   ├── ProyectosKanban.tsx           # ← NUEVO — US6 (dnd-kit)
│           │   ├── WikiLinkRenderer.tsx          # ← NUEVO — US7 (extiende lib/markdown.tsx)
│           │   ├── BacklinksPanel.tsx            # ← NUEVO — US7
│           │   ├── VaultTreeSidebar.tsx          # ← NUEVO — US8 (dnd-kit + collapse)
│           │   ├── StatsWidget.tsx               # ← NUEVO — US9
│           │   ├── InfraSidebar.tsx              # ← NUEVO — US10
│           │   ├── AgentRunner.tsx               # ← NUEVO — US11
│           │   ├── GraphView.tsx                 # ← NUEVO — US12 (canvas + d3-force)
│           │   ├── CalendarSidebar.tsx           # ← NUEVO — US13
│           │   └── GmailSidebar.tsx              # ← NUEVO — US14
│           ├── pages/
│           │   ├── Dashboard.tsx                 # extiende — añade sidebars + viewswitcher
│           │   ├── Login.tsx
│           │   ├── Papelera.tsx                  # ← NUEVO — vista archivadas
│           │   ├── Grafo.tsx                     # ← NUEVO
│           │   └── Stats.tsx                     # ← NUEVO
│           ├── hooks/                            # ← NUEVO directorio
│           │   ├── useKeyboardShortcut.ts        # D-015
│           │   ├── useOptimisticConcurrency.ts   # D-003
│           │   ├── useWikiIndex.ts               # D-004
│           │   ├── useVaultTree.ts
│           │   ├── useVistaPersist.ts            # FR-012 localStorage
│           │   └── useDragAndDrop.ts             # wrapper dnd-kit
│           ├── lib/
│           │   ├── api.ts                        # extiende — añade v2 fetchers
│           │   ├── auth.ts
│           │   ├── cache.ts
│           │   ├── format.ts
│           │   ├── markdown.tsx                  # extiende — wiki-link plugin
│           │   ├── types.ts                      # extiende — Proyecto, VaultNode, etc.
│           │   ├── slug.ts                       # ← NUEVO — cliente espejo D-002
│           │   └── googleSanitize.ts             # ← NUEVO — saneado HTML Gmail (DOMPurify-lite)
│           ├── styles/
│           │   └── globals.css
│           └── tests/                            # vitest unitarios
│               └── (espejo de components/)
│
├── public_html/
│   └── knowledge_base/          # vault (single source of truth)
│       ├── dia/
│       │   ├── 2026-05-13-...md
│       │   └── archivo/         # ← NUEVO al primer archivado
│       ├── proyectos/           # ← NUEVO al primer acceso kanban
│       │   └── bienvenida.md
│       ├── contexto/
│       └── operaciones/
│
└── /etc/nosvers/secrets/
    └── google.json              # ← NUEVO — OAuth refresh token (perms 0600)
```

**Structure Decision**: Web-app layout (Opción 2 del template), con backend Python en `/home/nosvers/tablero/` (subpaquete `v2/` para todo lo nuevo de Fase B+C) y frontend React en `/home/nosvers/tablero/web/`. La elección preserva el "monorepo NosVers" sin cambios estructurales y deja `tablero/v2/` claramente delimitado para code-review focalizado en lo nuevo.

## Phase 0 — Outline & Research

Ver `research.md` para el detalle. Resumen ejecutivo:

1. **Librería drag-and-drop**: `@dnd-kit/core` + `@dnd-kit/sortable` (D-007). Comparativa contra `react-beautiful-dnd` (deprecada), `react-dnd` (más bajo nivel, menos accesible OOTB). `@dnd-kit` soporta keyboard navigation built-in (Constitución X / accesibilidad), 12 KB gzipped, sin dependencias.
2. **Renderer grafo**: `d3-force` + `<canvas>` con switch a `<svg>` para vaults < 100 nodos (D-008). Comparativa contra `react-force-graph` (envoltura sobre three.js, demasiado pesada para móvil) y `vis-network` (CSS conflict potential).
3. **Command palette**: `cmdk` (12 KB, no deps, vendrida por Vercel — Radix-base, accesible). Comparativa contra `kbar` (deprecado), `react-command-palette` (mantenimiento mínimo).
4. **Google APIs**: REST directo via `httpx` + `google-auth` (D-005). Comparativa contra `google-api-python-client` (~30 deps, pesado para un solo proceso uvicorn). REST cubre 100% de los endpoints que necesitamos (events.list, events.insert, threads.list, threads.get).
5. **Markdown editor**: `<textarea>` controlado + `react-markdown` preview en split-pane (D-006). Comparativa contra `@uiw/react-md-editor` (lleva CodeMirror, 250 KB) y `tiptap` (rich-text WYSIWYG, no markdown-source-fidelity). El usuario de Angel y África es desarrollador/conocedor de markdown; el split-pane simple es suficiente y consistente con la sintaxis Obsidian que ya usan.
6. **Concurrency model**: optimistic con `If-Match: <modified_at>` header (D-003). Comparativa contra ETags (overkill para texto plano), advisory locks server-side (estado que rompe Principio III).
7. **Atomic write**: `os.replace(tmp, dst)` POSIX-atomic (D-013). Garantiza zero-corruption sin librerías.
8. **Backlink index**: in-memory dict + write-through + reconstruct-on-startup (D-004). Comparativa contra SQLite FTS (rompe Principio III) o watchdog inotify (race-prone, dependency extra).

**Unknowns resueltos**: ninguno marcado `NEEDS CLARIFICATION` — la combinación spec + decisions.md cubre el plano técnico.

## Phase 1 — Design & Contracts

Ver `data-model.md` para entidades y transiciones. Ver `contracts/*.openapi.yaml` para los 14 contratos REST. Ver `quickstart.md` para el smoke test mínimo dev → prod.

### Resumen de cambios al agent context

`/home/nosvers/specs/second-brain-dashboard/CLAUDE.md` ya contiene un puntero genérico al "current plan"; se actualiza el marker `<!-- SPECKIT START -->/<!-- SPECKIT END -->` para apuntar a este archivo (`specs/002-fase-bc-notion-clone/plan.md`).

## Post-Design Re-check (Constitución)

Tras escribir `data-model.md` y los 14 contratos, ningún diseño emergente fuerza dependencias nuevas no listadas o relaja principios. La Constitución sigue PASS. Las 15 decisiones registradas en `decisions.md` se honran end-to-end:

- **D-001** in-process MCP → backend importa `voz.capturar`, `voz.buscar`.
- **D-002/D-012** slug resolver → `tablero/v2/slug_resolver.py`.
- **D-003** optimistic concurrency → `tablero/v2/concurrency.py` decorator + frontend hook `useOptimisticConcurrency.ts` + `If-Match` header en todos los contratos write.
- **D-004** lazy+write-through backlinks → `tablero/v2/wiki_index.py` mantiene dict global, GET `/wiki-index` lo expone, escrituras (capturar/editar/archivar/restaurar/move) actualizan in-process tras escribir.
- **D-005** REST directo Google → `tablero/v2/google_*.py` con `httpx.AsyncClient` + token cargado de `/etc/nosvers/secrets/google.json`.
- **D-006** mismo renderer markdown → `<MarkdownView>` compartido.
- **D-007** `@dnd-kit` → tanto `ProyectosKanban.tsx` como `VaultTreeSidebar.tsx`.
- **D-008** canvas + d3-force → `GraphView.tsx` con switch SVG/canvas por N.
- **D-009** TZ Europe/Madrid → `tablero/v2/stats_helpers.py` (sólo si se decide tener helper server-side; per FR-039 los cálculos son client-side, así que el TZ se aplica con `Intl.DateTimeFormat('es-ES', {timeZone: 'Europe/Madrid'})` en frontend).
- **D-010** coverage threshold → `pyproject.toml` `[tool.coverage]` fail_under = 80.
- **D-011** soft-delete forever → no cron de purga.
- **D-013** atomic write → `tablero/v2/atomic_write.py`.
- **D-014** prefijo `/v2/` → router config en `tablero/rest.py`.
- **D-015** detección OS → `useKeyboardShortcut.ts`.

## Complexity Tracking

> No hay violaciones de la Constitución. Sección informativa de complejidades aceptadas:

| Decisión | Por qué necesaria | Alternativa más simple rechazada porque |
|---|---|---|
| Subpaquete `tablero/v2/` separado | Diferenciar code-review focus + permitir borrado quirúrgico si algo no funciona | Mezclar archivos en `tablero/` raíz haría difícil saber qué pertenece a B+C vs Fase A en blame |
| Backlink index in-memory | Constitución III prohíbe BBDD paralela | SQLite FTS habría sido más fácil pero rompe principio Vault-SoT |
| `@dnd-kit` ~12 KB | Drag-and-drop accesible (Constitución X) sin reescribir gestures a mano | Reescribir DnD a mano es horas de bugs + accesibilidad pobre |
| `d3-force` standalone | Constitución VIII prohíbe meta-frameworks; d3-force es funcional puro | `react-force-graph` lleva three.js (200 KB) — fuera de budget |
| OAuth refresh server-side | Constitución X exige secrets server-side | Token en frontend rompe el modelo de seguridad |

---

*Plan generado por Claude Opus 4.7 vía /speckit-plan · 2026-05-13*
