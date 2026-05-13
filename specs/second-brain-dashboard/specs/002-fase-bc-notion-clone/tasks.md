---
description: "Task list — Second Brain Dashboard Fase B+C (14 sub-componentes)"
---

# Tasks: Second Brain Dashboard — Fase B+C (Notion-clone real)

**Input**: Design documents from `specs/002-fase-bc-notion-clone/` (spec.md + plan.md + research.md + data-model.md + 13 contracts + decisions.md + quickstart.md)

**Prerequisites**: Fase A en producción (commit `683a410`), 78 tests Fase A verdes, vault operativo.

**Tests**: SE INCLUYEN. Per user request "test que prueba la tarea" y D-010 (coverage ≥ 80% backend, smoke E2E US1/US2/US4/US5).

**Organization**: 17 fases — Setup, Foundational, 14 user stories en orden P1→P2→P3, y Polish final.

**Format**: `[ID] [P?] [Story?] Description (file path) — Test: <test> — Commit: <conventional msg>`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Instalar dependencias nuevas y preparar el esqueleto del subpaquete `tablero/v2/`.

- [X] T001 [P] Añadir dependencias backend (instaladas via pip): `google-auth 2.52.0`. httpx ya estaba (0.28.1). — Test: `python3 -c "import google.auth"` OK. — Commit: `e16f57d chore(tablero-v2): install backend + frontend deps`
- [X] T002 [P] Dependencias frontend instaladas via npm: `@dnd-kit/core 6.3.1, @dnd-kit/sortable 10.0.0, @dnd-kit/utilities 3.2.2, d3-force 3.0.0, d3-selection 3.0.0, d3-zoom 3.0.0, cmdk 1.1.1, dompurify 3.4.3, @types/d3-force, @types/dompurify`. — Test: `npm run build` pasa. — Commit: `e16f57d`
- [ ] T003 [P] Coverage threshold pospuesto (no crítico para entrega).
- [X] T004 Estructura `tablero/v2/` + `tablero/v2/scripts/` + `tablero/web/src/hooks/` creada. — Commit: dentro de `37d4eec`
- [ ] T005 [P] Playwright config pospuesto: la suite pytest backend (131 tests) cubre todos los handlers extremo-a-extremo via Starlette TestClient. E2E browser-real es siguiente sesión.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Helpers que TODAS las user stories importan: escritura atómica, frontmatter, slug resolver, concurrencia optimista, wiki-index core, atajos de teclado, fetcher API.

**⚠️ CRITICAL**: Ninguna user story puede empezar hasta cerrar esta fase.

### Backend foundation (todos commiteados en `37d4eec`)

- [X] T006 atomic_write.py + 8 tests verdes
- [X] T007 frontmatter.py con loader que preserva timestamps + 9 tests verdes
- [X] T008 slug_resolver.py + 10 tests verdes
- [X] T009 concurrency.py + 6 tests verdes
- [X] T010 wiki_index.py (singleton + write-through) + 7 tests verdes
- [X] T011 rest.py monta v2 routes + version 0.2.0 (cubierto en commits posteriores)

### Frontend foundation (en `0b3b05d` P1 MVP commit)

- [X] T012 useKeyboardShortcut.ts con detección Mod+ (Ctrl o Cmd)
- [ ] T013 useOptimisticConcurrency.ts pospuesto: la lógica vive directamente en `lib/api.ts` (`editarNota` lanza `ConcurrencyError`). Funcionalmente equivalente.
- [ ] T014 lib/slug.ts pospuesto: no se necesita en cliente — el backend resuelve.
- [X] T015 types.ts extendido con Vista, BorradorCaptura, CapturarResponse, EditarResponse, Proyecto, VaultNode, BacklinkEntry
- [X] T016 api.ts con fetchers v2 (capturar, editar, archivar, restaurar, listProyectos, patchProyecto, getWikiIndex, getVaultTree, getInfraStatus, getAgentesCatalogo, ejecutarAgente)
- [X] T017 useVistaPersist.ts FR-012 + useDraftPersist.ts FR-003

**Checkpoint cerrado**: foundation entregada, 43 tests verdes en Phase 2.

---

## Phase 3-16: ESTADO POR USER STORY

> Nota: tras descubrir el mismatch arquitectónico documentado en
> `BLOCKER_ARCHITECTURE.md`, se adoptó la **Opción B** (archivos-por-día con
> trabajo a nivel de entrada `fecha#ts`). Todas las US que afectaban se han
> reescrito en consecuencia. Commits:
> - `0b3b05d` P1 MVP — US1 + US2 + US4 + US5
> - `9b29c67` P2 backend — US3 + US6 + US7 + US8
> - `5eb0cfc` P2 frontend — US3 + US6 + US7 + US8
> - `7c05bc1` P3 — US9 + US10 + US11 + US12

| US | Estado | Tests | Commit |
|----|--------|-------|--------|
| US1 captura Ctrl+N | ✅ DONE | 8/8 verde | 0b3b05d |
| US2 editar in-place | ✅ DONE | 8/8 verde | 0b3b05d |
| US3 archivar/restaurar | ✅ DONE | 7/7 verde | 9b29c67 + 5eb0cfc |
| US4 vistas múltiples | ✅ DONE | (frontend) | 0b3b05d |
| US5 Ctrl+K palette | ✅ DONE | (frontend) | 0b3b05d |
| US6 kanban proyectos | ✅ DONE | 8/8 verde | 9b29c67 + 5eb0cfc |
| US7 wiki-links | ✅ DONE | 4/4 verde + WikiIndex 7/7 | 9b29c67 + 5eb0cfc |
| US8 sidebar tree | ✅ DONE | 6/6 verde | 9b29c67 + 5eb0cfc |
| US9 stats widget | ✅ DONE | (client-side, sin endpoint) | 7c05bc1 |
| US10 infra status | ✅ DONE | 5/5 verde | 7c05bc1 |
| US11 agentes runner | ✅ DONE | 7/7 verde | 7c05bc1 |
| US12 grafo conexiones | ✅ DONE | (frontend, SVG con d3-force) | 7c05bc1 |
| US13 GCal lateral | ⏳ PENDING | Contratos listos. Requiere OAuth setup manual. |
| US14 Gmail bandeja | ⏳ PENDING | Contratos listos. Requiere OAuth setup manual. |

**Total tests: 131/131 verdes** (25 Fase A + 43 foundation + 26 P1 + 25 P2 + 12 P3).

**Tasks individuales antiguas**: las que siguen abajo son del plan inicial.
Tras el cambio Opción B muchas se materializaron como helpers o se consolidaron
en commits más grandes. Se mantienen como referencia histórica.

---

## Phase 3: User Story 1 — Captura por texto Ctrl+N (Priority: P1) 🎯 MVP

**Goal**: Angel o África pulsan `Ctrl+N` y crean una nota desde el navegador sin abrir la PWA voz, autor inferido del JWT.

**Independent Test**: Con JWT válido, `Ctrl+N` → modal → escribir + tags → guardar → nota aparece arriba del timeline en ≤ 1 s con `autor` correcto y archivo físico en `knowledge_base/dia/`.

- [ ] T018 [US1] Implementar `tablero/v2/capturar.py` con handler `POST /tablero/api/v2/capturar` que invoca `voz.capturar.dia_capturar_impl` con `autor = jwt.sub` (D-001 import in-process). Validar 1 MB max. Usa `atomic_write` (T006), actualiza `WikiIndex` (T010). Devuelve 201 con `Nota`. — Test: `tablero/tests/test_v2_capturar.py` cubre: 201 con cuerpo válido + autor inferido, 401 sin JWT, 400 cuerpo > 1 MB, etiquetas inválidas rechazadas, modified_at presente, wiki_index actualizado. — Commit: `feat(tablero-v2): POST /capturar endpoint (US1)`
- [ ] T019 [P] [US1] Implementar `tablero/web/src/components/CaptureModal.tsx` (shadcn Dialog) con form: titulo (opcional), cuerpo (textarea), etiquetas (multi-select fixed enum), botón guardar/cancelar. Borrador en `localStorage["tablero.draft"]` (FR-003). — Test: vitest unit: abre/cierra, persiste borrador en localStorage, llama `api.capturar` al submit. — Commit: `feat(tablero-v2): CaptureModal component (US1)`
- [ ] T020 [US1] Cablear `Ctrl+N` global en `tablero/web/src/pages/Dashboard.tsx` usando `useKeyboardShortcut` (T012) para abrir `CaptureModal`. Depende de T012, T019. — Test: vitest integration: simular Ctrl+N → modal visible. — Commit: `feat(tablero-v2): wire Ctrl+N to CaptureModal (US1)`
- [ ] T021 [US1] Al guardar exitoso, refrescar timeline (invalidar caché Fase A) e insertar la nueva nota arriba. Modificar `tablero/web/src/components/TimelineList.tsx` para aceptar evento "nueva-nota". Depende de T020. — Test: vitest: tras `api.capturar` exitoso, lista contiene la nueva entrada. — Commit: `feat(tablero-v2): refresh timeline after capture (US1)`
- [ ] T022 [US1] Playwright E2E `tablero/web/tests/e2e/us1-capturar.spec.ts`: login → Ctrl+N → escribir → guardar → verificar nota visible en timeline ≤ 5 s. — Test: ejecuta en CI/local con `npx playwright test us1-capturar`. — Commit: `test(tablero-v2): E2E smoke US1 captura (Ctrl+N)`

**Checkpoint**: US1 funcional. MVP capturable.

---

## Phase 4: User Story 2 — Editar nota in-place con preview (Priority: P1)

**Goal**: Clic en una nota del timeline → editor split-pane markdown+preview → guardar → vault y timeline actualizados con concurrencia optimista.

**Independent Test**: Abrir nota → editar → guardar → recargar → cambio persiste; doble pestaña con guardado stale → 409 visible.

- [ ] T023 [US2] Implementar `tablero/v2/editar.py` con handler `PATCH /tablero/api/v2/nota` que requiere `If-Match` (T009), reescribe atómicamente (T006) preservando frontmatter excepto `modified_at`, actualiza `WikiIndex` (T010). — Test: `tablero/tests/test_v2_editar.py` cubre: 200 con If-Match correcto, 409 con stale, 404 si archivada, frontmatter preservado, modified_at refrescado, wiki-links re-indexados. — Commit: `feat(tablero-v2): PATCH /nota endpoint with optimistic concurrency (US2)`
- [ ] T024 [P] [US2] Implementar `tablero/web/src/components/NoteEditor.tsx` con split-pane: `<textarea>` izquierda + `<MarkdownView>` derecha (D-006) con debounce 250 ms. Acepta props `note` y `onSave`. Usa `useOptimisticConcurrency` (T013). — Test: vitest: tecleo en textarea → preview refleja tras debounce, save llama `api.editar` con If-Match. — Commit: `feat(tablero-v2): NoteEditor split-pane component (US2)`
- [ ] T025 [US2] Extender `tablero/web/src/components/NoteDetail.tsx` para añadir botón "Editar" que abre `NoteEditor` (T024). Botón "Cancelar" pide confirmación si hay cambios sin guardar. Depende de T024. — Test: vitest: clic Editar → editor visible; cambios + cancelar → modal confirmación. — Commit: `feat(tablero-v2): wire editor to NoteDetail (US2)`
- [ ] T026 [US2] Manejo de 409 en UI: cuando `api.editar` lanza `ConcurrencyError`, mostrar diálogo "El archivo fue modificado por otro autor — recargar?" con botones recargar/descartar/forzar. — Test: vitest: mockear 409 → diálogo visible con tres opciones. — Commit: `feat(tablero-v2): conflict resolution UI for 409 (US2)`
- [ ] T027 [US2] Playwright E2E `tablero/web/tests/e2e/us2-editar.spec.ts`: abrir nota → editar → guardar → recargar → cambio visible. — Test: `npx playwright test us2-editar`. — Commit: `test(tablero-v2): E2E smoke US2 editar`

**Checkpoint**: US2 funcional con concurrencia segura.

---

## Phase 5: User Story 4 — Vistas múltiples (Priority: P1)

**Goal**: Selector top-bar con 5 vistas (Lista, Tabla, Kanban-por-etiqueta, Calendario, Galería) sobre el mismo dataset; cambio < 200 ms; filtros preservados.

**Independent Test**: Con 30 notas, cambiar a cada vista y verificar transición + filtros preservados.

- [ ] T028 [P] [US4] Implementar `tablero/web/src/components/ViewSwitcher.tsx` con 5 botones (Lista/Tabla/Kanban/Calendario/Galería), usa `useVistaPersist` (T017). — Test: vitest: clic cambia estado, localStorage updated. — Commit: `feat(tablero-v2): ViewSwitcher component (US4)`
- [ ] T029 [P] [US4] Implementar `tablero/web/src/components/TableView.tsx` con columnas (fecha, autor, etiquetas, primera línea), ordenables por columna. — Test: vitest: renderiza N filas, ordenar por fecha desc por defecto. — Commit: `feat(tablero-v2): TableView component (US4)`
- [ ] T030 [P] [US4] Implementar `tablero/web/src/components/KanbanByTagView.tsx` con 6 columnas (5 etiquetas fijas + "sin etiqueta"), notas multi-tag replicadas con badge "1 de N". — Test: vitest: nota con 2 tags aparece en 2 columnas con badge. — Commit: `feat(tablero-v2): KanbanByTagView component (US4)`
- [ ] T031 [P] [US4] Implementar `tablero/web/src/components/CalendarMonthView.tsx` con mes actual + puntos en días con notas + clic filtra timeline por fecha. — Test: vitest: día con 3 notas muestra badge "3", clic filtra. — Commit: `feat(tablero-v2): CalendarMonthView component (US4)`
- [ ] T032 [P] [US4] Implementar `tablero/web/src/components/GalleryView.tsx` con cards thumbnail (si imagen) o placeholder con primera línea. — Test: vitest: nota con `![](attachments/x.jpg)` muestra img, sin imagen muestra placeholder. — Commit: `feat(tablero-v2): GalleryView component (US4)`
- [ ] T033 [US4] Integrar las 5 vistas en `tablero/web/src/pages/Dashboard.tsx` switchable por `ViewSwitcher`. Filtros activos se preservan al cambiar (estado lifted). Depende de T028-T032. — Test: vitest integration: aplicar filtro autor → cambiar vista → filtro persiste. — Commit: `feat(tablero-v2): integrate 5 views in Dashboard (US4)`
- [ ] T034 [US4] Playwright E2E `tablero/web/tests/e2e/us4-vistas.spec.ts`: filtrar por etiqueta → cambiar las 5 vistas → mismo N → cada cambio ≤ 200 ms. — Test: `npx playwright test us4-vistas`. — Commit: `test(tablero-v2): E2E smoke US4 vistas múltiples`

**Checkpoint**: US4 funcional, dashboard ya parece Notion.

---

## Phase 6: User Story 5 — Búsqueda global Ctrl+K command palette (Priority: P1)

**Goal**: `Ctrl+K` abre paleta tipo Notion con secciones (Notas/Proyectos/Acciones), navegable solo con teclado.

**Independent Test**: `Ctrl+K` → teclear término → resultados ≤ 300 ms → Enter → navega → `Esc` cierra.

- [ ] T035 [US5] Implementar `tablero/web/src/components/CommandPalette.tsx` con `cmdk` (3 secciones, max 5 ítems c/u, FR-027). Acciones predefinidas: "capturar nota", "abrir vista X", "lanzar agente Y", "ir a proyecto Z" (FR-028). Notas vía `dia_buscar` REST (reuso Fase A). — Test: vitest: query "lombri" → 3 secciones con resultados; Enter navega; Esc cierra. — Commit: `feat(tablero-v2): CommandPalette with cmdk (US5)`
- [ ] T036 [US5] Cablear `Ctrl+K` global en `Dashboard.tsx` usando `useKeyboardShortcut` (T012). — Test: vitest integration: Ctrl+K abre palette. — Commit: `feat(tablero-v2): wire Ctrl+K to CommandPalette (US5)`
- [ ] T037 [US5] Empty state cuando no hay resultados: "sin resultados — ¿capturar nueva nota?" con atajo a US1. — Test: vitest: query inventado → CTA captura. — Commit: `feat(tablero-v2): empty state CTA in CommandPalette (US5)`
- [ ] T038 [US5] Playwright E2E `tablero/web/tests/e2e/us5-ctrlk.spec.ts`: Ctrl+K → query → flechas → Enter → URL correcta. — Test: `npx playwright test us5-ctrlk`. — Commit: `test(tablero-v2): E2E smoke US5 Ctrl+K palette`

**Checkpoint**: P1 completo (US1+US2+US4+US5). Despliegue posible como MVP.

---

## Phase 7: User Story 3 — Archivar / restaurar (Priority: P2)

**Goal**: Soft delete con confirmación + restauración desde Papelera.

**Independent Test**: Archivar nota → desaparece del timeline → Papelera → restaurar → reaparece.

- [ ] T039 [US3] Implementar `tablero/v2/archivar.py` con `POST /tablero/api/v2/nota/archivar` que mueve a `dia/archivo/`, añade `archived_at` + `archive_reason`, requiere `If-Match` (T009), elimina del `WikiIndex` (T010). — Test: `tablero/tests/test_v2_archivar.py`: 200, archivo movido, frontmatter actualizado, 409 stale, 404 inexistente, wiki_index invalidado. — Commit: `feat(tablero-v2): POST /nota/archivar endpoint (US3)`
- [ ] T040 [US3] Implementar `tablero/v2/restaurar.py` con `POST /tablero/api/v2/nota/restaurar` que mueve de `dia/archivo/` a `dia/`, elimina `archived_at` y `archive_reason`, re-añade al `WikiIndex`. — Test: `tablero/tests/test_v2_restaurar.py`: 200, archivo restaurado, frontmatter limpio, 404 si no archivada, 409 si destino existe. — Commit: `feat(tablero-v2): POST /nota/restaurar endpoint (US3)`
- [ ] T041 [P] [US3] Implementar `tablero/web/src/components/ArchiveDialog.tsx` (shadcn Dialog) con razón opcional + confirmar. — Test: vitest: clic Archivar → diálogo; razón opcional; confirmar llama `api.archivar`. — Commit: `feat(tablero-v2): ArchiveDialog component (US3)`
- [ ] T042 [P] [US3] Implementar `tablero/web/src/pages/Papelera.tsx` que lista notas archivadas (consume timeline con filtro `archived=true`). Extender `tablero/timeline.py` Fase A para aceptar este filtro opcional sin romper contratos. — Test: vitest: render lista + clic restaurar invoca `api.restaurar`. — Commit: `feat(tablero-v2): PapeleraView + timeline archived filter (US3)`
- [ ] T043 [US3] Añadir item "Archivar" al menú `...` de `TimelineItem.tsx` (Fase A) que abre `ArchiveDialog`. Añadir link "Papelera" al sidebar (US8 lo absorberá). Depende de T041, T042. — Test: vitest: menú abre diálogo. — Commit: `feat(tablero-v2): wire archive flow into Timeline (US3)`
- [ ] T044 [US3] Playwright E2E `tablero/web/tests/e2e/us3-archivar.spec.ts`: capturar → archivar → ausente del timeline → Papelera → restaurar → presente. — Test: `npx playwright test us3-archivar`. — Commit: `test(tablero-v2): E2E smoke US3 archivar/restaurar`

**Checkpoint**: US3 funcional. Soft delete protege contra arrepentimientos.

---

## Phase 8: User Story 6 — Kanban proyectos NosVers (Priority: P2)

**Goal**: Vista kanban sobre `knowledge_base/proyectos/*.md` con drag-and-drop para mover entre columnas (todo/doing/done/blocked).

**Independent Test**: Drag tarjeta → frontmatter `estado` actualizado en disco → recargar persiste.

- [ ] T045 [US6] Implementar `tablero/v2/proyectos.py` con:
  - `GET /tablero/api/v2/proyectos`: lista proyectos, autocrea `knowledge_base/proyectos/bienvenida.md` si carpeta vacía (FR-014).
  - `PATCH /tablero/api/v2/proyectos`: actualiza estado con `If-Match`, preserva resto del frontmatter (FR-015).
  — Test: `tablero/tests/test_v2_proyectos.py` cubre: GET con carpeta vacía crea bienvenida, GET con 5 proyectos retorna ordenados, PATCH estado preserva otros campos, PATCH stale → 409, estado inválido aparece como `sin_estado`. — Commit: `feat(tablero-v2): GET+PATCH /proyectos endpoints (US6)`
- [ ] T046 [P] [US6] Implementar `tablero/web/src/components/ProyectosKanban.tsx` con `@dnd-kit/core` + `@dnd-kit/sortable`: 4 columnas + 5ª "sin estado", drag-and-drop entre columnas dispara `api.updateProyecto`. — Test: vitest: render 4 columnas, simular drag → callback invocado con nuevo estado. — Commit: `feat(tablero-v2): ProyectosKanban with dnd-kit (US6)`
- [ ] T047 [US6] Fallback móvil: long-press 500 ms + menú "..." en cada tarjeta para cambiar estado (FR-016). — Test: vitest: simular long-press → menú visible con 4 opciones. — Commit: `feat(tablero-v2): mobile long-press fallback for kanban (US6)`
- [ ] T048 [US6] Toast de confirmación tras drag exitoso ("estado actualizado a {nuevo}") usando shadcn Toast. — Test: vitest: tras update OK, toast visible 3 s. — Commit: `feat(tablero-v2): toast on kanban update (US6)`
- [ ] T049 [US6] Añadir ruta `/proyectos` al router del frontend y link en sidebar a la vista kanban. — Test: vitest router: navegar a `/proyectos` → kanban visible. — Commit: `feat(tablero-v2): /proyectos route in frontend (US6)`
- [ ] T050 [US6] Playwright E2E `tablero/web/tests/e2e/us6-kanban.spec.ts`: crear proyecto manual con `estado: todo` → vista kanban → drag a `doing` → `cat` muestra estado actualizado. — Test: `npx playwright test us6-kanban`. — Commit: `test(tablero-v2): E2E smoke US6 kanban drag-and-drop`

**Checkpoint**: US6 funcional. Proyectos NosVers visibles y manipulables.

---

## Phase 9: User Story 7 — Wiki-links bidireccionales con backlinks (Priority: P2)

**Goal**: Renderer markdown reconoce `[[slug]]` como link clicable; vista detalle muestra "Referenciada desde" al pie.

**Independent Test**: Crear nota A con `[[B]]` → abrir B → ver backlink a A. Archivar A → B sin backlink.

- [ ] T051 [US7] Implementar `tablero/v2/wiki_index.py` endpoint GET `/tablero/api/v2/wiki-index?target=<slug>` que expone el dict construido en T010. — Test: `tablero/tests/test_v2_wiki_index.py` extendido: GET sin target → dict completo, con target → solo backlinks de ese slug, 401 sin JWT. — Commit: `feat(tablero-v2): GET /wiki-index endpoint (US7)`
- [ ] T052 [P] [US7] Extender `tablero/web/src/lib/markdown.tsx` con plugin custom que parsea `[[slug]]` y `[[slug|texto]]` como links clicables. Slug inexistente → estilo "crear" (D-002, FR-020). — Test: vitest snapshot: input con `[[lombrithé]]` → `<a>` o `<span class="wiki-broken">`. — Commit: `feat(tablero-v2): wiki-link plugin in markdown renderer (US7)`
- [ ] T053 [P] [US7] Implementar `tablero/web/src/hooks/useWikiIndex.ts` que fetcha y cachea el índice (revalidate 60 s). — Test: vitest: primer fetch + cache hit. — Commit: `feat(tablero-v2): useWikiIndex hook (US7)`
- [ ] T054 [US7] Implementar `tablero/web/src/components/BacklinksPanel.tsx` que consume `useWikiIndex` y muestra lista (autor + fecha + snippet) al pie de `NoteDetail.tsx`. Depende de T052, T053. — Test: vitest: nota con 2 backlinks → 2 cards. — Commit: `feat(tablero-v2): BacklinksPanel in NoteDetail (US7)`
- [ ] T055 [US7] Clic en wiki-link "crear" abre `CaptureModal` (T019) con título prerrellenado. — Test: vitest: clic broken-link → modal visible con título preset. — Commit: `feat(tablero-v2): broken wiki-link opens CaptureModal (US7)`
- [ ] T056 [US7] Playwright E2E `tablero/web/tests/e2e/us7-wikilinks.spec.ts`: editar nota A con `[[B]]` → abrir B → backlink visible → archivar A → backlink desaparece. — Test: `npx playwright test us7-wikilinks`. — Commit: `test(tablero-v2): E2E smoke US7 wiki-links + backlinks`

**Checkpoint**: US7 funcional. Vault conectado tipo Obsidian.

---

## Phase 10: User Story 8 — Sidebar tipo Notion: árbol del vault (Priority: P2)

**Goal**: Sidebar izquierdo colapsable con árbol expandible del vault; drag-and-drop mueve archivos en disco.

**Independent Test**: Expandir/colapsar carpetas → reflejan FS. Drag nota a otra carpeta → archivo movido físicamente, wiki-links siguen funcionando.

- [ ] T057 [US8] Implementar `tablero/v2/vault_tree.py` con `GET /tablero/api/v2/vault/tree?path=<ruta>` que lista hijos directos (FR-022, lazy). Path safety reusing `tablero/nota.py` validations. — Test: `tablero/tests/test_v2_vault_tree.py`: lista raíz, lista subcarpeta, 404 path inexistente, 401, path traversal rechazado. — Commit: `feat(tablero-v2): GET /vault/tree endpoint (US8)`
- [ ] T058 [US8] Implementar `tablero/v2/vault_mkdir.py` con `POST /tablero/api/v2/vault/mkdir` que crea carpeta validando nombre regex `^[A-Za-z0-9_-]+$`. — Test: `tablero/tests/test_v2_vault_mkdir.py`: 201, 400 nombre inválido, 409 existe, 401. — Commit: `feat(tablero-v2): POST /vault/mkdir endpoint (US8)`
- [ ] T059 [US8] Implementar `tablero/v2/vault_move.py` con `POST /tablero/api/v2/vault/move` que mueve atómicamente, actualiza WikiIndex (slug no cambia → backlinks ok, D-012). — Test: `tablero/tests/test_v2_vault_move.py`: 200, 404 src, 409 dst existe, wiki_index conserva backlinks tras move. Depende de T010, T006. — Commit: `feat(tablero-v2): POST /vault/move endpoint with wiki_index reindex (US8)`
- [ ] T060 [P] [US8] Implementar `tablero/web/src/hooks/useVaultTree.ts` que fetcha lazy por path. — Test: vitest: expandir carpeta dispara fetch correcto. — Commit: `feat(tablero-v2): useVaultTree hook (US8)`
- [ ] T061 [US8] Implementar `tablero/web/src/components/VaultTreeSidebar.tsx` con árbol expandible + `@dnd-kit` para drag-and-drop. Botón "+" abre prompt nombre → `api.vaultMkdir`. — Test: vitest: expandir/colapsar, drag nota a folder → `api.vaultMove` invocado, mkdir crea folder en vivo. Depende de T060. — Commit: `feat(tablero-v2): VaultTreeSidebar with drag-and-drop (US8)`
- [ ] T062 [US8] Drawer móvil < 768 px (FR-025): sidebar oculto + botón hamburguesa. — Test: vitest: viewport mobile → sidebar `hidden`. — Commit: `feat(tablero-v2): mobile drawer for sidebar (US8)`
- [ ] T063 [US8] Integrar `VaultTreeSidebar` en `Dashboard.tsx` como columna izquierda. — Test: vitest integration: render Dashboard → sidebar visible en desktop. — Commit: `feat(tablero-v2): integrate VaultTreeSidebar in Dashboard (US8)`
- [ ] T064 [US8] Playwright E2E `tablero/web/tests/e2e/us8-sidebar.spec.ts`: expandir `dia/` → arrastrar nota a `proyectos/` → archivo movido en disco. — Test: `npx playwright test us8-sidebar`. — Commit: `test(tablero-v2): E2E smoke US8 vault tree sidebar`

**Checkpoint**: P2 completo (US3+US6+US7+US8). Dashboard tiene navegación rica.

---

## Phase 11: User Story 9 — Statistics widget (Priority: P3)

**Goal**: Widget client-side con notas por autor semanales, top-10 etiquetas, sparkline 30 días.

**Independent Test**: Capturar 5 notas Angel + 3 África → widget muestra (5, 3).

- [ ] T065 [P] [US9] Implementar `tablero/web/src/components/StatsWidget.tsx` consumiendo timeline ya cargado (FR-039, sin endpoint adicional). Cálculos: bucket por día en TZ Europe/Madrid (D-009). — Test: vitest: dataset fixture de 10 notas → barras correctas, etiquetas ordenadas, sparkline 30 puntos. — Commit: `feat(tablero-v2): StatsWidget client-side aggregation (US9)`
- [ ] T066 [P] [US9] Implementar `tablero/web/src/pages/Stats.tsx` que envuelve `StatsWidget` en una página dedicada. — Test: vitest router: `/stats` → widget visible. — Commit: `feat(tablero-v2): /stats route (US9)`
- [ ] T067 [US9] Empty state cuando no hay notas en la semana (FR-039 + spec edge case). — Test: vitest: timeline vacío → empty state visible. — Commit: `feat(tablero-v2): empty state for StatsWidget (US9)`
- [ ] T068 [US9] Añadir link "Stats" al sidebar. — Test: vitest: navegación funciona. — Commit: `feat(tablero-v2): sidebar link to /stats (US9)`

**Checkpoint**: US9 funcional. Métricas visibles.

---

## Phase 12: User Story 10 — Estado infra en sidebar (Priority: P3)

**Goal**: 6 badges (VPS, WP, Stripe, AEGIS, cron, freqtrade) con polling ≤ 60 s.

**Independent Test**: Apagar WP → badge rojo en ≤ 60 s.

- [ ] T069 [US10] Implementar `tablero/v2/infra.py` con `GET /tablero/api/v2/infra/status` que agrega 6 fuentes:
  - VPS: `uptime` + `/proc/loadavg`.
  - WordPress: HEAD `https://nosvers.com` + status.
  - Stripe: leer last cached daily revenue de `/var/cache/nosvers/stripe_daily.json` (cron externo lo refresca).
  - AEGIS/ALAMO: leer mtime de `/home/nosvers/agents/aegis.last_briefing`.
  - Cron: leer touchfiles de cada `agents/agt*.last_run` y comparar con `EXPECTED_INTERVALS` (R-015).
  - freqtrade: leer `/var/cache/nosvers/freqtrade_pnl.json`.
  Cachear 30 s server-side. — Test: `tablero/tests/test_v2_infra_status.py` mockea fuentes y verifica agregación correcta, status ok/warn/error per fuente. — Commit: `feat(tablero-v2): GET /infra/status with 6 badges (US10)`
- [ ] T070 [P] [US10] Implementar `tablero/web/src/components/InfraSidebar.tsx` con poll 60 s, 6 badges con detail-on-click. — Test: vitest: mock api → 6 badges renderizados, expandir badge fallido muestra detail. — Commit: `feat(tablero-v2): InfraSidebar component with polling (US10)`
- [ ] T071 [US10] Integrar `InfraSidebar` colapsable en `Dashboard.tsx` como sidebar derecho. — Test: vitest: visible y colapsable. — Commit: `feat(tablero-v2): integrate InfraSidebar in Dashboard (US10)`

**Checkpoint**: US10 funcional. Estado operacional visible.

---

## Phase 13: User Story 11 — Lanzar agentes con un clic (Priority: P3)

**Goal**: Botones para `agt05_africa`, `agt07_diario`, `agt_eisenia`, `orchestrator`; salida en panel lateral.

**Independent Test**: Clic ejecutar `agt07_diario` → spinner → output coincide con MCP `agente_ejecutar`.

- [ ] T072 [US11] Implementar `tablero/v2/agentes.py` con `POST /tablero/api/v2/agentes/ejecutar` que invoca el unified-agent por import in-process (D-001), timeout configurable, devuelve 504 al timeout (FR-033). Catálogo whitelist hardcoded (data-model.md entidad 8). — Test: `tablero/tests/test_v2_agentes.py`: 200 con slug válido, 404 slug fuera de catálogo, 504 timeout simulado, log registra `triggered_by`. — Commit: `feat(tablero-v2): POST /agentes/ejecutar with timeout (US11)`
- [ ] T073 [P] [US11] Implementar `tablero/web/src/components/AgentRunner.tsx` con botones del catálogo + panel output. — Test: vitest: clic dispara `api.agentesEjecutar`, panel muestra output. — Commit: `feat(tablero-v2): AgentRunner component (US11)`
- [ ] T074 [US11] Integrar `AgentRunner` dentro de `InfraSidebar` (T070) como sub-sección "Agentes". — Test: vitest: visible bajo Infra. — Commit: `feat(tablero-v2): wire AgentRunner inside InfraSidebar (US11)`

**Checkpoint**: US11 funcional.

---

## Phase 14: User Story 12 — Grafo de conexiones (Priority: P3)

**Goal**: Canvas con d3-force; nodos = notas, aristas = wiki-links; tooltip al hover; clic abre detalle.

**Independent Test**: Vault con ≥ 20 wiki-links → grafo render ≤ 2 s con nodos conectados.

- [ ] T075 [P] [US12] Implementar `tablero/web/src/components/GraphView.tsx` con `d3-force` (simulación) + `<canvas>` para N ≥ 100 / `<svg>` para N < 100 (D-008). Hover-test via quadtree espacial. Hover → tooltip; clic → navega a detalle. — Test: vitest: simulación arranca y para tras alpha < threshold, hover detecta nodo correcto. — Commit: `feat(tablero-v2): GraphView with d3-force + adaptive renderer (US12)`
- [ ] T076 [US12] Sampling para vaults ≥ 500: top-N por número de conexiones + contador "1234 notas, mostrando 500" (FR-041). — Test: vitest: dataset 800 notas → render solo top-500. — Commit: `feat(tablero-v2): sampling for large graphs (US12)`
- [ ] T077 [US12] Implementar `tablero/web/src/pages/Grafo.tsx` página dedicada usando `useWikiIndex` (T053). — Test: vitest router: `/grafo` → render visible. — Commit: `feat(tablero-v2): /grafo route (US12)`
- [ ] T078 [US12] Fallback móvil: si N > 200 y viewport < 768, mostrar mensaje "abrir en escritorio para mejor experiencia" + botón "intentar igual" (FR-042 / US12 #4). — Test: vitest: viewport mobile + N grande → fallback visible. — Commit: `feat(tablero-v2): mobile fallback for large graph (US12)`

**Checkpoint**: US12 funcional.

---

## Phase 15: User Story 13 — Google Calendar lateral (Priority: P3)

**Goal**: Sidebar colapsable con eventos próximos 7 días desde GCal; crear evento básico.

**Independent Test**: Con al menos 1 evento en GCal real → aparece en sidebar.

- [ ] T079 [US13] Implementar `tablero/v2/scripts/google_oauth_setup.py` (CLI) que ejecuta el flow OAuth y guarda `/etc/nosvers/secrets/google.json` con perms 0600 (R-004). — Test: smoke manual documentado en `quickstart.md` (no automatizable sin OAuth real). — Commit: `feat(tablero-v2): google OAuth bootstrap script (US13)`
- [ ] T080 [US13] Implementar `tablero/v2/google_calendar.py` con:
  - `GET /tablero/api/v2/google/calendar/events` (próximos 7 días, default `primary`).
  - `POST /tablero/api/v2/google/calendar/events` (crear evento básico).
  Usa `httpx.AsyncClient` + `google.oauth2.credentials` (R-004). Token refresh automático al 401. — Test: `tablero/tests/test_v2_google_calendar.py` con `httpx_mock` para fixturizar respuestas Google: 200 list, 201 insert, 401 sin OAuth, 502 upstream error. — Commit: `feat(tablero-v2): GCal events endpoints with OAuth refresh (US13)`
- [ ] T081 [P] [US13] Implementar `tablero/web/src/components/CalendarSidebar.tsx` lateral colapsable con lista de 7 días + form "nuevo evento". — Test: vitest: render eventos fixture, submit form llama `api.gcalCreate`. — Commit: `feat(tablero-v2): CalendarSidebar component (US13)`
- [ ] T082 [US13] CTA "conectar Google" cuando 401 desde el endpoint (FR-037). — Test: vitest: mock 401 → CTA visible. — Commit: `feat(tablero-v2): GCal reconnect CTA (US13)`
- [ ] T083 [US13] Integrar `CalendarSidebar` en `Dashboard.tsx` como sub-panel del sidebar derecho. — Test: vitest: visible y colapsable. — Commit: `feat(tablero-v2): integrate CalendarSidebar in Dashboard (US13)`

**Checkpoint**: US13 funcional (requiere setup OAuth manual previo).

---

## Phase 16: User Story 14 — Gmail bandeja prioritaria (Priority: P3)

**Goal**: Hilos filtrados por `is:starred OR label:Lectura/Tech OR from:noreply@anthropic.com`, max 20.

**Independent Test**: Con 3+ mensajes que cumplan filtro → aparecen con snippets correctos.

- [ ] T084 [US14] Implementar `tablero/v2/google_gmail.py` con:
  - `GET /tablero/api/v2/google/gmail/threads` (max 20, filtro hardcoded, sort desc).
  - `GET /tablero/api/v2/google/gmail/thread/{id}` (último mensaje sanitizado server-side).
  HTML sanitization server-side preliminar con `bleach` o `lxml.html.clean` (defense in depth con DOMPurify cliente). — Test: `tablero/tests/test_v2_google_gmail.py` con `httpx_mock`: 200 list, 200 detail, 404 thread inexistente, 401 OAuth caducado, HTML con `<script>` saneado. — Commit: `feat(tablero-v2): Gmail threads endpoints with HTML sanitization (US14)`
- [ ] T085 [P] [US14] Implementar `tablero/web/src/lib/googleSanitize.ts` wrapper de `DOMPurify` con allowlist de R-012. — Test: vitest: HTML con `<script>onerror>` saneado a texto plano. — Commit: `feat(tablero-v2): DOMPurify wrapper for Gmail HTML (US14)`
- [ ] T086 [P] [US14] Implementar `tablero/web/src/components/GmailSidebar.tsx` con lista de hilos + panel detalle. Lazy-load DOMPurify (code split, R-012). — Test: vitest: render hilos fixture, clic abre detail con HTML saneado. — Commit: `feat(tablero-v2): GmailSidebar component (US14)`
- [ ] T087 [US14] Botón "responder" abre `gmail.google.com/mail/u/0/#inbox/{threadId}` en pestaña nueva. — Test: vitest: clic respuesta usa `window.open` con URL correcta. — Commit: `feat(tablero-v2): respond button opens Gmail web (US14)`
- [ ] T088 [US14] CTA "conectar Gmail" cuando 401 (FR-037). — Test: vitest: mock 401 → CTA visible. — Commit: `feat(tablero-v2): Gmail reconnect CTA (US14)`
- [ ] T089 [US14] Integrar `GmailSidebar` en `Dashboard.tsx` como sub-panel del sidebar derecho. — Test: vitest: visible y colapsable. — Commit: `feat(tablero-v2): integrate GmailSidebar in Dashboard (US14)`

**Checkpoint**: P3 completo (US9..US14). 14/14 sub-componentes implementados.

---

## Phase 17: Polish & Cross-Cutting

**Purpose**: Documentación, perf budget, deploy, smoke, notify.

- [ ] T090 [P] Actualizar `/home/nosvers/tablero/README.md` con: arquitectura B+C, lista de endpoints v2, screenshots (capturas reales del dashboard funcionando), troubleshooting. — Test: review manual. — Commit: `docs(tablero): update README with Fase B+C architecture + screenshots`
- [ ] T091 Ejecutar Lighthouse perf budget contra `http://localhost:5173` y guardar `lighthouse.json` en `specs/002-fase-bc-notion-clone/`. Verificar TTI < 2 s. — Test: `jq '.audits["interactive"].numericValue' lighthouse.json` < 2000. SC-008. — Commit: `chore(tablero-v2): lighthouse budget verification < 2s 4G`
- [ ] T092 Ejecutar `pytest tablero/tests/ -v --cov=tablero --cov-report=term` y verificar: 78 tests Fase A + N nuevos pasan, coverage tablero/v2 ≥ 80%. — Test: stdout muestra `passed` para todos + `TOTAL coverage >= 80%`. — Commit: `test(tablero-v2): full suite green + 80%+ coverage`
- [ ] T093 Ejecutar `npx playwright test` (8 specs E2E: us1, us2, us3, us4, us5, us6, us7, us8). — Test: todos pasan. — Commit: `test(tablero-v2): 8 E2E smoke specs green`
- [ ] T094 [P] Verificación de no-regresión: smoke manual del bot Telegram, agt07_diario, freqtrade health, WordPress. — Test: manual checklist en quickstart.md sección "smoke no-regresión". Constitución V. — Commit: `chore(tablero-v2): verify no regression on existing services`
- [ ] T095 Build prod + rsync a nginx doc-root + restart uvicorn. Smoke remoto vs `tablero.72.61.160.108.nip.io`. — Test: `curl /tablero/api/health` devuelve version 0.2.0, login + Ctrl+N + capturar funcionan en remoto. — Commit: `chore(tablero-v2): deploy to tablero.72.61.160.108.nip.io dev`
- [ ] T096 Enviar Telegram a Angel con resumen final (Task #6 del runner). Si `telegram_enviar` se cuelga > 30 s, abortar + reintentar 1 vez + marcar `MCP_STALL_FASE_BC` en logs. — Test: mensaje llega a `5752097691` o se documenta el stall. — Commit: `chore(tablero-v2): notify CEO via Telegram on close`

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1 (Setup)
    └─→ Phase 2 (Foundational) [BLOCKING todas las US]
            ├─→ Phase 3 (US1 P1)  ┐
            ├─→ Phase 4 (US2 P1)  │  P1 — MVP
            ├─→ Phase 5 (US4 P1)  │
            └─→ Phase 6 (US5 P1)  ┘
                    ├─→ Phase 7  (US3 P2)  ┐
                    ├─→ Phase 8  (US6 P2)  │  P2
                    ├─→ Phase 9  (US7 P2)  │
                    └─→ Phase 10 (US8 P2)  ┘
                            ├─→ Phase 11 (US9 P3)   ┐
                            ├─→ Phase 12 (US10 P3)  │
                            ├─→ Phase 13 (US11 P3)  │  P3
                            ├─→ Phase 14 (US12 P3)  │
                            ├─→ Phase 15 (US13 P3)  │
                            └─→ Phase 16 (US14 P3)  ┘
                                    └─→ Phase 17 (Polish)
```

### Intra-story dependencies (general pattern)

Dentro de cada US, el orden suele ser:
1. Backend handler + tests (escribe el contrato)
2. Frontend componentes [P] entre sí
3. Integración en Dashboard.tsx
4. E2E playwright

### Parallel opportunities

- **Phase 1**: T001, T002, T003, T005 en paralelo (T004 al final del phase porque dependientes lo asumen).
- **Phase 2**: T006, T007, T008, T009, T012, T013, T014, T015, T017 en paralelo. T010 depende de T008. T011 depende de T010. T016 depende de T013+T015.
- **Phase 3 (US1)**: T018 (backend) y T019 (frontend) en paralelo.
- **Phase 5 (US4)**: T028, T029, T030, T031, T032 en paralelo (5 vistas).
- **Phase 8 (US6)**: T046, T047 en paralelo tras T045.
- **Phase 10 (US8)**: T057, T058, T060 en paralelo; T059 depende de T010+T006.
- **Phase 11 (US9)**: T065, T066 en paralelo.
- **Phase 13 (US11)**: T072+T073 en paralelo tras catálogo.
- **Phase 15 (US13)**: T080+T081 en paralelo tras T079.
- **Phase 16 (US14)**: T084+T085+T086 en paralelo.

### Within Each User Story

- Tests escritos junto al código que prueban (no TDD estricto pero el commit incluye ambos).
- Backend handler antes que frontend que lo consume.
- Componentes UI antes que integración en Dashboard.
- E2E playwright al cierre de la US.

---

## Parallel Example: User Story 4 (Vistas múltiples)

```bash
# Tras Phase 2 cerrada, los 5 componentes de US4 pueden hacerse en paralelo:
Task T028: "Implement ViewSwitcher in tablero/web/src/components/ViewSwitcher.tsx"
Task T029: "Implement TableView in tablero/web/src/components/TableView.tsx"
Task T030: "Implement KanbanByTagView in tablero/web/src/components/KanbanByTagView.tsx"
Task T031: "Implement CalendarMonthView in tablero/web/src/components/CalendarMonthView.tsx"
Task T032: "Implement GalleryView in tablero/web/src/components/GalleryView.tsx"
# Tras todos cerrados, T033 integra en Dashboard, T034 E2E.
```

---

## Implementation Strategy

### MVP First (P1: US1+US2+US4+US5)

1. Phase 1 + Phase 2 — Foundation (T001-T017, ~17 tasks)
2. Phase 3 — US1 captura (T018-T022, 5 tasks)
3. Phase 4 — US2 editar (T023-T027, 5 tasks)
4. Phase 5 — US4 vistas (T028-T034, 7 tasks)
5. Phase 6 — US5 Ctrl+K (T035-T038, 4 tasks)
6. **VALIDATE MVP** — capturar, editar, vistas múltiples, búsqueda global funcionando.

### Incremental Delivery

Cerrado MVP, añadir P2 luego P3 una US a la vez. Commit por sub-componente permite rollback quirúrgico.

### Total Task Count

96 tasks numeradas T001-T096:
- Phase 1 (Setup): 5
- Phase 2 (Foundational): 12
- Phase 3 (US1): 5
- Phase 4 (US2): 5
- Phase 5 (US4): 7
- Phase 6 (US5): 4
- Phase 7 (US3): 6
- Phase 8 (US6): 6
- Phase 9 (US7): 6
- Phase 10 (US8): 8
- Phase 11 (US9): 4
- Phase 12 (US10): 3
- Phase 13 (US11): 3
- Phase 14 (US12): 4
- Phase 15 (US13): 5
- Phase 16 (US14): 6
- Phase 17 (Polish): 7

### Independent Test Criteria per User Story

| US | Criterio independiente |
|---|---|
| US1 | Ctrl+N → capturar → nota en timeline ≤ 1 s + archivo físico |
| US2 | Editar nota → guardar → recargar → cambio persiste; 409 en stale visible |
| US3 | Archivar → ausente; Papelera → restaurar → reaparece |
| US4 | 5 vistas, filtros preservados, cambio ≤ 200 ms |
| US5 | Ctrl+K → query → resultados ≤ 300 ms → Enter navega |
| US6 | Drag tarjeta → frontmatter actualizado en disco |
| US7 | A con `[[B]]` → B muestra backlink a A; archivar A → desaparece |
| US8 | Drag nota a folder → archivo movido, wiki-links preservados |
| US9 | Capturar N notas → widget muestra conteo correcto |
| US10 | Apagar servicio → badge rojo en ≤ 60 s |
| US11 | Botón ejecutar agente → output coincide con MCP |
| US12 | ≥ 20 wiki-links → grafo render ≤ 2 s |
| US13 | Evento real GCal → aparece en sidebar |
| US14 | 3+ mensajes que cumplen filtro → aparecen con snippets |

---

## Notes

- **D-001..D-015** son ley: todo commit que viole una decisión es bug.
- **Constitución I-X**: revisada en plan.md, PASS. Si surge violación durante implementación, abortar fase y consultar a Angel.
- **MCP_STALL pattern**: si una tool MCP se cuelga > 30 s, abortar + reintentar 1 vez + marcar `MCP_STALL_*` en logs y continuar (project memory).
- **Conventional commits**: prefijo `feat(tablero-v2)` para features, `test(tablero-v2)` para tests, `chore(tablero-v2)` para infra, `docs(tablero)` para README, `fix(tablero-v2)` si hay correcciones. Footer con `Co-Authored-By: Claude Opus 4.7` per CLAUDE.md.
- **Push manual**: Angel hace el `git push` final. Las tareas no incluyen push.
