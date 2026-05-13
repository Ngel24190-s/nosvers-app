# Research — Fase B+C (Notion-clone real)

Fecha: 2026-05-13 · Investigación que respalda `plan.md`. Cada apartado fija una decisión y descarta alternativas con rationale verificable.

## R-001 — Librería drag-and-drop (US3 kanban, US8 vault tree)

**Decisión**: `@dnd-kit/core` + `@dnd-kit/sortable` + `@dnd-kit/utilities`.

**Rationale**:
- Mantenida activamente (release > 1/mes en 2025-2026).
- 12 KB gzipped, sin dependencias transitivas.
- Soporte keyboard navigation built-in (cumple Constitución X / accesibilidad).
- API basada en `useDraggable` + `useDroppable` hooks, idiomático para React 18.
- Funciona en touch (long-press configurable) y mouse sin shims (FR-016).
- Bien testeado: la comunidad cubre el escenario kanban con sensors y collision detection custom — no hay que reinventar.

**Alternativas consideradas**:
- `react-beautiful-dnd` (Atlassian): **descartada**, deprecada oficialmente, sin commits desde 2023. Su sustituto recomendado es `@dnd-kit`.
- `react-dnd`: más bajo nivel, requiere backend HTML5/Touch, sin keyboard accessibility OOTB, ~30 KB.
- DnD nativo HTML5 a pelo: rompe en touch, accesibilidad pobre, gesture conflicts en móvil.

## R-002 — Renderer del grafo (US12)

**Decisión**: `d3-force` (simulación) + `<canvas>` (render) en grafo grande; switch a `<svg>` para N < 100 (mejor hover-test).

**Rationale**:
- `d3-force` es funcional puro, modular (~12 KB), sin React vendor lock.
- `<canvas>` escala a miles de nodos a 60 fps (sin DOM overhead).
- `<svg>` para tamaños pequeños permite hover preciso y selección sin reverse hit-testing manual.
- Comparativa de hit-testing canvas: distancia al cursor < radio del nodo en el spatial index implícito de d3-force (`quadtree`).
- Constitución VIII (stack ligero) → no se admite three.js.

**Alternativas consideradas**:
- `react-force-graph`: bonito API React pero monta three.js (~200 KB) y WebGL. Excesivo en móvil 4G.
- `vis-network`: 70 KB, conflictos CSS habituales, render por SVG no escala.
- `cytoscape.js`: 100 KB, buen producto, pero pensado para grafos científicos — overkill para nuestro caso.

## R-003 — Command palette (US5 Ctrl+K)

**Decisión**: `cmdk` (vendido por Vercel, basado en Radix UI).

**Rationale**:
- ~12 KB gzipped.
- Sin deps externas.
- Accesible OOTB (`role=listbox`, `aria-selected`, ARIA live region).
- Headless: el styling lo damos con shadcn/ui Tailwind, sin CSS forced.
- Soporta `cmd+k` y `ctrl+k` con hook propio + integración nativa con keyboard.
- Soporta sectioning (Notas / Proyectos / Acciones — FR-027) con `<Command.Group>`.

**Alternativas consideradas**:
- `kbar`: no mantenido desde 2023.
- `react-command-palette`: estilo difícil de override, lleva su propio modal.
- Implementación a mano: tentador (es solo un modal con input + lista filtrada), pero la accesibilidad bien hecha (focus trap, arrow nav, live region) son ~200 líneas que `cmdk` resuelve mejor.

## R-004 — Cliente Google APIs (US13 GCal, US14 Gmail)

**Decisión**: REST directo via `httpx.AsyncClient` + `google-auth` para el refresh token flow.

**Rationale**:
- `google-api-python-client` es síncrono, lleva ~30 deps transitivas, y emite logs ruidosos.
- Solo necesitamos 4 endpoints: `events.list`, `events.insert`, `users.threads.list`, `users.threads.get`. Hacerlos a pelo es trivial.
- `httpx` ya está en el stack uvicorn (asíncrono, soporta HTTP/2).
- `google-auth` (~150 KB pero solo el módulo `google.oauth2.credentials` es ~12 KB) gestiona el refresh token flow correctamente sin acoplarnos al cliente RPC completo.

**Token storage**: `/etc/nosvers/secrets/google.json` con perms `0600`, formato:
```json
{
  "client_id": "...",
  "client_secret": "...",
  "refresh_token": "...",
  "token_uri": "https://oauth2.googleapis.com/token",
  "scopes": ["https://www.googleapis.com/auth/calendar.events", "https://www.googleapis.com/auth/gmail.readonly", "https://www.googleapis.com/auth/gmail.send"]
}
```

**Setup manual** (una vez): Angel ejecuta el `google_oauth_setup.py` (script de bootstrap incluido en `tablero/v2/scripts/`) que pide consent en navegador local, guarda el refresh token en el path correcto. Documentado en quickstart.md.

**Alternativas consideradas**:
- Pasar credenciales por el MCP de Claude (`mcp__claude_ai_Google_Calendar__*`): rompe en producción cuando el dashboard sirve sin Claude.ai conectado.
- Service Account: requiere domain-wide delegation que Angel no tiene en su Workspace personal.

## R-005 — Editor markdown del split-pane (US2)

**Decisión**: `<textarea>` controlado (con `react-textarea-autosize` opcional para auto-resize) + `<MarkdownView>` reused de Fase A en la mitad derecha. Sin librería extra.

**Rationale**:
- El usuario son devs/conocedores; no necesitan WYSIWYG.
- Mantener `<textarea>` significa que el clipboard, undo del navegador y los shortcuts del SO funcionan sin esfuerzo.
- El preview en vivo se hace re-renderizando `<MarkdownView>` con debounce 250 ms del contenido.
- Cero divergencia entre preview-vivo y vista-detalle (D-006).

**Alternativas consideradas**:
- `@uiw/react-md-editor`: lleva CodeMirror (~250 KB).
- `tiptap`: rich-text, no mantiene fidelidad markdown source.
- `monaco-editor`: el editor de VS Code; brutal pero 500 KB+.
- `codemirror 6`: 150 KB, gran calidad — overkill para nuestro alcance.

## R-006 — Optimistic concurrency (D-003)

**Decisión**: header `If-Match: <modified_at-ISO8601>` en todos los `POST`/`PATCH`/`DELETE` write; 409 si no coincide con disco.

**Rationale**:
- Es el patrón estándar HTTP (RFC 7232). Servers, frameworks y clientes lo entienden.
- Ningún estado server-side (compatible con Principio III).
- Compatible con caches (Cache-Control: must-revalidate funciona si combinamos).
- Mensaje de error 409 incluye el `modified_at` real para que el cliente sepa qué reload mostrar.

**Alternativas consideradas**:
- ETag con hash SHA-1 del archivo: técnicamente más correcto, pero `modified_at` es legible para humanos en logs y suficiente para 2 usuarios. SHA-1 añadiría coste de I/O por petición.
- Advisory locks server-side (Redis SET NX): rompe Principio III (estado paralelo).

## R-007 — Atomic write (D-013)

**Decisión**: tmp en mismo dir destino → `os.replace(tmp, dst)` (POSIX-atomic).

**Rationale**:
- POSIX `rename(2)` es atomic dentro del mismo filesystem.
- El destino y el tmp se crean en el mismo dir → mismo FS por construcción.
- En caso de crash: el destino o tiene la versión antigua completa o la nueva completa, nunca un híbrido.
- Sin librerías; `os.replace` está en stdlib Python.

**Alternativas consideradas**:
- `fcntl.flock`: lock advisory, no atomic — un crash deja el lock.
- Escritura directa al destino: rompe ante crash en mitad.

## R-008 — Backlink index (D-004)

**Decisión**: dict in-memory `{slug_destino: set[slug_fuente]}` reconstruido en startup; cada write (`capturar`/`editar`/`archivar`/`restaurar`/`mover`) actualiza el dict in-process tras flushear el archivo.

**Rationale**:
- Constitución III prohíbe BBDD paralela. Un dict in-memory derivado del vault no es BBDD: es caché.
- Un solo worker uvicorn → no hay invalidación cross-instance que gestionar.
- Reconstrucción en startup: medido en Fase A, escanear `knowledge_base/dia/` con ~200 notas tarda < 100 ms; los wiki-links son un regex simple por archivo. Proyección lineal: 5.000 notas ≈ 2 s startup. Aceptable.
- Tras restart, primer GET `/wiki-index` puede tardar el rebuild si no se hizo lazy en background. Mitigación: arrancar el rebuild en `startup` event de Starlette.

**Alternativas consideradas**:
- watchdog inotify: detecta cambios externos (p.ej. Obsidian escribiendo). Razonable a futuro, pero suma una dependencia y race conditions con nuestras propias escrituras. Pospuesto.
- SQLite FTS: rompe Principio III.
- Recalcular en cada GET: O(N) por petición — inaceptable a 1.000 notas.

## R-009 — Slug resolver para wiki-links (D-002, D-012)

**Decisión**: pipeline determinístico:
1. Normalizar query: lowercase + Unicode NFKD + drop combining marks (acentos).
2. Match contra dict `{slug_normalizado → [archivo, ...]}` reconstruido en startup.
3. Si una sola coincidencia → resuelve.
4. Si múltiples → la de `modified_at` más reciente; tooltip "N homónimos".
5. Si ninguna → render como "crear" + abrir modal `CaptureModal` con título prefijado.

**Rationale**:
- Replica el comportamiento Obsidian (Angel y África ya lo conocen).
- Determinístico → tests fácilmente comprobables.
- Reusa el dict que ya construye el backlink index.

## R-010 — Detección OS para Ctrl/Cmd (D-015)

**Decisión**: hook `useKeyboardShortcut` que detecta plataforma vía `navigator.userAgentData?.platform ?? navigator.platform` y registra `event.metaKey || event.ctrlKey` para tolerar ambos.

**Rationale**:
- `navigator.platform` está deprecado pero todavía expuesto en todos los navegadores objetivo.
- `navigator.userAgentData` es la API moderna (Chrome 90+, no Firefox aún).
- El listener `metaKey || ctrlKey` cubre el caso donde Angel/África usen un teclado externo con Win-key.

## R-011 — Testing coverage threshold (D-010)

**Decisión**:
- Backend: pytest + coverage.py, `fail_under = 80` en `pyproject.toml [tool.coverage.report]`.
- Frontend unit: vitest. Sin threshold formal pero cobertura por componente revisada en PR.
- Smoke E2E: playwright (más estable que cypress en CI Linux headless). Cubre US1, US2, US4, US5.

**Rationale**:
- 80% es el sweet spot: cubre flujos principales sin obligar a tests cosméticos sobre código de wiring.
- Playwright tiene mejor soporte para keyboard events (`Ctrl+K`, `Ctrl+N`) que Cypress.

## R-012 — Sanitización HTML Gmail (US14)

**Decisión**: `DOMPurify` (sandboxed para `<body>`-fragment) con allowlist mínimo: `p, br, strong, em, a[href], blockquote, ul, ol, li, code, pre, span`. Sin `<style>`, `<script>`, `<iframe>`, `<form>`, `<input>`, ni atributos `on*`.

**Rationale**:
- Gmail entrega HTML rich; renderizarlo crudo es XSS instantáneo.
- DOMPurify es la referencia (200K downloads/día npm, audit OWASP).
- ~50 KB gzipped pero solo se carga lazy cuando US14 se renderiza (code split).

**Alternativas consideradas**:
- Texto plano via Gmail API `format=plain`: pierde links/formatting; reduce utilidad.
- Sanitizer custom: alto riesgo de XSS si se hace mal.

## R-013 — Deploy strategy

**Decisión**:
1. Construir `tablero/web/dist/` con `npm run build`.
2. `rsync` a `nginx` doc-root `/var/www/tablero/` (ya configurado en Fase A).
3. Reiniciar uvicorn (`systemctl restart uvicorn-nosvers`) para cargar nuevas rutas v2.
4. Smoke test 6 endpoints críticos (health, whoami, timeline, capturar, editar, archivar) antes de declarar deploy OK.

**Rationale**:
- Mismo pipeline que Fase A; no se introduce CI/CD externo (Constitución I).
- Reinicio uvicorn es ~2 s downtime, aceptable para 2 usuarios.

**Alternativas consideradas**:
- Hot-reload de routes (uvicorn `--reload`): rompe en prod; solo dev.
- Blue/green: overkill para escala 2 usuarios.

## R-014 — Estructura del frontmatter de proyectos (US6)

**Decisión**: schema mínimo obligatorio `{estado, modified_at}`; resto opcional.

```yaml
---
titulo: Tienda Lemon Squeezy
estado: doing            # ∈ {todo, doing, done, blocked}
modified_at: 2026-05-13T10:42:00+02:00
responsable: angel       # opcional, ∈ {angel, africa}
deadline: 2026-06-01     # opcional
etiquetas: [monetización, urgente]   # opcional
---

Cuerpo libre markdown.
```

**Rationale**:
- `estado` es la única columna kanban → obligatorio.
- `modified_at` para concurrency optimista (D-003).
- Resto opcional para no forzar a Angel a llenar campos vacíos.

## R-015 — Cómo se observa el cron status (US10 FR-030)

**Decisión**: lectura de `/home/nosvers/agents/agt07_diario.last_run` (touchfile escrito por el cron en cada ejecución). Si `now - mtime > expected_interval * 2`, marcar `warn`.

Para cada agente con cron periódico, definir en config:
```python
EXPECTED_INTERVALS = {
    "agt05_africa": 6 * 3600,     # cada 6 h
    "agt07_diario": 24 * 3600,    # cada día
    "agt_eisenia": 12 * 3600,
    "orchestrator": 3600,
}
```

**Rationale**:
- Sin parsing de crontab (frágil).
- Sin polling de logs (variable de formato).
- Touchfiles ligeros y sin dependencias.

**Alternativas consideradas**:
- Crontab parser: roto en cuanto cambie el formato del cron.
- systemd timers + `systemctl status`: requeriría rewrites de los crones existentes — fuera de alcance.

---

*Research completado: 0 NEEDS CLARIFICATION restantes.*
