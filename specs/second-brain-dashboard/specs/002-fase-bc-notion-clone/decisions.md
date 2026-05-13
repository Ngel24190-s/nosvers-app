# Decisiones técnicas — Fase B+C (registro autónomo, sin Angel)

Per `CONTINUE_FASE_BC.md`: las decisiones técnicas o menores se toman aquí en lugar de bloquear con preguntas a Angel. Este archivo es el log autoritativo de elecciones que el plan/tasks/implement honrarán.

**Fecha**: 2026-05-13
**Autor**: Claude Opus 4.7 (Director Ejecutivo NosVers)

## D-001 — Mecanismo de invocación MCP desde el backend tablero

**Contexto**: `tablero/rest.py` (FastAPI, Python) necesita llamar a tools como `dia_capturar`, `agente_ejecutar`, etc. expuestas por el MCP server `nosvers-mcp-2026`.

**Decisión**: Invocación in-process por **import directo** de las funciones Python que sirven cada tool. El MCP server y el backend tablero corren en la misma VPS, así que importar las funciones es más rápido y elimina dependencia de red local. El protocolo MCP queda como interfaz secundaria para clientes externos (Claude.ai, bot Telegram); el dashboard backend usa la API Python plana.

**Fallback**: si la división modular del MCP server impide imports limpios, el backend del tablero llama al MCP server por HTTP sobre `127.0.0.1:<puerto-MCP>`.

**Por qué**: latencia mínima, menos partes móviles, fácil de mockear en tests.

---

## D-002 — Resolución de slug en wiki-links `[[nota]]`

**Contexto**: una nota en `dia/2026-05-01-lombrithé.md` debe resolverse al teclear `[[lombrithé]]` aunque haya prefijo de fecha. El spec menciona "resolución por slug, no por ruta" pero no fija el algoritmo.

**Decisión**: el resolver intenta, en orden:
1. Match exacto contra `<basename sin .md>` en todo `knowledge_base/`.
2. Match exacto contra `<basename sin prefijo YYYY-MM-DD- ni .md>` (notas diarias).
3. Match insensible a mayúsculas y acentos sobre los dos anteriores.
4. Si hay múltiples coincidencias, la nota con `modified_at` más reciente gana (con tooltip "N notas con este slug").

**Por qué**: el patrón Obsidian de Angel y África ya usa basenames sin pensar en fechas; soportar prefijo de fecha sin obligar a teclearlo da ergonomía sin penalty.

---

## D-003 — Concurrencia optimista para todos los archivos editables del vault

**Contexto**: el spec define `modified_at` + HTTP 409 para notas (FR-006). El kanban (FR-015) y el árbol del sidebar (FR-023) también escriben archivos `.md`.

**Decisión**: extender el mismo patrón a TODOS los endpoints que modifiquen archivos del vault — notas diarias, proyectos, cualquier `.md` movido por el árbol. Cada archivo lleva `modified_at` en el frontmatter; cualquier PATCH/PUT requiere enviarlo y devuelve 409 si está desactualizado.

**Por qué**: consistencia, código compartible (un solo middleware), evita race conditions también entre kanban y árbol que afecten al mismo archivo.

---

## D-004 — Freshness del índice de backlinks

**Contexto**: FR-018 dice "refrescado tras crear/editar/archivar/restaurar"; US7 acceptance #3 dice "≤ 1 s tras el archivado". No fija si es watchdog real-time o lazy.

**Decisión**: lazy + write-through. El backend mantiene un dict `{slug_destino → [slug_fuente, ...]}` en memoria construido al startup escaneando todo `knowledge_base/`. Cada operación de write (capturar/editar/archivar/restaurar/mover) actualiza el dict in-process tras escribir el archivo. La invalidación cross-instance no es relevante porque solo hay un worker FastAPI. Tras restart, se reconstruye el índice.

**Por qué**: sin watchdog FS, sin polling. El backend siempre conoce todos los cambios porque pasan por sus endpoints. Tiempo de rebuild en startup ≤ 1 s para vaults < 5.000 notas (benchmark Fase A muestra escaneo del directorio en ≤ 200 ms).

---

## D-005 — GCal y Gmail: integración por REST con token OAuth almacenado

**Contexto**: A-004 ofrece dos caminos (MCP directo vs REST proxy). Elige uno definitivo.

**Decisión**: REST directo desde el backend del tablero contra `googleapis.com`, usando un OAuth refresh token guardado en `/etc/nosvers/secrets/google.json` (mismo formato que ya usa el conector AEGIS). El MCP layer NO se usa para estas integraciones porque su contexto es por-sesión-de-Claude y no por-deploy-de-dashboard.

**Por qué**: el dashboard corre como servicio independiente; necesita credenciales propias, no las del MCP de Claude.ai. La integración MCP solo aplica cuando un cliente Claude habla con su propio Gmail; aquí queremos las cuentas Google del dominio NosVers.

**Implicación**: requiere setup manual de OAuth una vez (Angel hace), pero después es autónomo.

---

## D-006 — Renderer markdown del editor en vivo (US2)

**Contexto**: FR-005 pide preview en vivo idéntico a la vista detalle.

**Decisión**: misma stack que Fase A — `react-markdown` + `remark-gfm` + `rehype-highlight` + extensión custom para wiki-links `[[slug]]`. Sin segundo renderer alternativo. El preview y la vista detalle comparten el mismo componente React `<MarkdownView>`.

**Por qué**: garantiza fidelidad visual y evita drift de renderers paralelos.

---

## D-007 — Drag-and-drop: librería `@dnd-kit/core` para todas las superficies

**Contexto**: kanban (FR-015) y árbol del sidebar (FR-023) necesitan DnD. La opción react-beautiful-dnd está deprecada y `@dnd-kit` es el estándar actual.

**Decisión**: `@dnd-kit/core` + `@dnd-kit/sortable` + `@dnd-kit/utilities` para todas las superficies de drag-and-drop. Mismo gesture model entre kanban y árbol (long-press móvil + pointer escritorio).

**Por qué**: mantenido, accesible (keyboard navigation built-in), un solo paradigma para el equipo.

---

## D-008 — Grafo: librería `d3-force` standalone + canvas, no SVG

**Contexto**: FR-040 pide d3-force; el spec no fija el renderer.

**Decisión**: `d3-force` para la simulación + `<canvas>` para el render. SVG queda para vaults < 100 nodos (modo high-fidelity con hover preciso); canvas para tamaños mayores (mejor rendimiento). La elección la hace el componente automáticamente según el N.

**Por qué**: canvas escala a miles de nodos sin DOM overhead; SVG ayuda con accesibilidad y hover-test en grafos pequeños.

---

## D-009 — Stats sparkline: agrupación diaria en zona Europe/Madrid

**Contexto**: US9 #3 pide barras "por día"; el spec no fija TZ.

**Decisión**: agrupación por día naturaleza en zona horaria `Europe/Madrid` (donde viven Angel y África). Las fechas en el frontmatter (`fecha: YYYY-MM-DD`) ya son naive — se interpretan como esta zona.

**Por qué**: evita off-by-one al cruzar medianoche; consistente con la PWA voz de Fase 001.

---

## D-010 — Testing: cobertura mínima 80% en backend nuevo, smoke E2E en frontend

**Contexto**: el spec exige "78/78 tests Fase A + nuevos" pero no fija umbral de cobertura.

**Decisión**:
- Backend Python (nuevos módulos de tablero): pytest con cobertura ≥ 80% en `coverage.py`, fail si baja.
- Frontend React: vitest unitarios por componente, + playwright/cypress smoke E2E para US1 (captura), US2 (editar), US4 (cambio de vistas), US5 (Ctrl+K). El resto se cubre por unitarios.

**Por qué**: cubre los flujos críticos sin gastar el doble de tiempo de implementación en suite E2E completa.

---

## D-011 — Soft delete: política de retención indefinida explícita

**Contexto**: A-010 ya lo dice; lo confirmo.

**Decisión**: `knowledge_base/dia/archivo/` NO tiene política de purga. Los archivos quedan ahí indefinidamente. Si crece sin control, en una fase posterior se introducirá un agente cron `agt_archivero` que mueva archivos > 1 año a `knowledge_base/dia/archivo/cold/`. Para Fase B+C, sin purga.

**Por qué**: simpleza; el espacio en disco no es un problema con vaults markdown a esta escala.

---

## D-012 — Identificador de notas para wiki-links y backlinks

**Contexto**: si una nota se renombra/mueve, los wiki-links que la apuntaban quedarían rotos por path.

**Decisión**: los wiki-links se resuelven por **slug** (basename sin .md, sin prefijo de fecha), NO por ruta. Mover una nota entre carpetas (US8/FR-023) NO rompe los backlinks; renombrarla SÍ (igual que Obsidian).

**Por qué**: equivalencia exacta con el comportamiento Obsidian que ya usan África y Angel; predecible para ambos.

---

## D-013 — Permisos de filesystem y atomicidad de escritura

**Contexto**: el spec menciona "reescribir atómicamente" varias veces (FR-004, FR-015, US2 acceptance #1).

**Decisión**: toda escritura al vault se hace via patrón `escribir-a-tmp-y-rename`:
1. Crear archivo `<destino>.tmp.<pid>.<nonce>` con el contenido completo (frontmatter + cuerpo).
2. `os.replace(tmp, destino)` — atómico en POSIX.
3. Si el rename falla, eliminar el tmp y devolver 5xx.

**Por qué**: garantiza que un crash a mitad de escritura no deja archivo corrupto; consistente con cómo Obsidian guarda.

---

## D-014 — Endpoints REST: prefijo `/tablero/v2/` para los nuevos

**Contexto**: Fase A expone `/tablero/timeline`, `/tablero/nota/<path>`, etc. Los nuevos endpoints podrían pisar el namespace.

**Decisión**: prefijo `/tablero/v2/` para todos los endpoints nuevos de Fase B+C (`/tablero/v2/capturar`, `/tablero/v2/nota/<path>/editar`, `/tablero/v2/proyectos/`, etc.). Los endpoints de Fase A (`/tablero/timeline`, etc.) permanecen sin cambios bajo `/tablero/` para preservar contratos.

**Por qué**: zero-regresión por construcción; los tests de Fase A siguen apuntando al mismo namespace; el frontend nuevo elige `v2/` para lo nuevo y los mismos endpoints `/tablero/` para lo existente.

---

## D-015 — Atajos de teclado: detección OS para `Ctrl+N` vs `Cmd+N`

**Contexto**: FR-002 y FR-026 mencionan ambos.

**Decisión**: hook `useKeyboardShortcut` que detecta `navigator.platform` (deprecated pero suficiente) o `navigator.userAgentData.platform` (moderno) y registra el modificador adecuado: `Cmd` en macOS, `Ctrl` en el resto. Los listeners usan `event.metaKey || event.ctrlKey` para tolerar ambos sin error.

**Por qué**: ergonomía nativa por plataforma; Angel y África usan principalmente Linux y Android, pero un visitante puntual desde macOS no debe pelearse con el atajo.

---

## Resumen ejecutivo

15 decisiones técnicas tomadas autónomamente. Ninguna requiere a Angel. Si surge una nueva ambigüedad durante `/speckit-plan` o `/speckit-implement`, se añadirá aquí con el siguiente `D-NNN` y se aplicará sin pausa. Las decisiones aquí registradas tienen precedencia sobre cualquier asunción tácita; el plan y los tasks deben honrarlas explícitamente.
