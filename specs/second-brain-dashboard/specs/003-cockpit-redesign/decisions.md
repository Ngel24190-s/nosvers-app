# Decisions — Fase D Cockpit (003-cockpit-redesign)

> Micro-decisiones técnicas que NO requirieron `/speckit-clarify` porque el brief
> ya fijaba el rumbo. Cada decisión es vinculante para `plan.md` y `tasks.md`.

## D-001 — Ruta del cockpit: `/cockpit`, no reemplaza Dashboard

**Decisión**: Añadir ruta nueva `/cockpit` en el cliente. `/` sigue mostrando
el Dashboard de Fase B+C.

**Razón**: El brief dice "el frontend antiguo se REEMPLAZA pero los archivos
quedan en git history". Una lectura literal sería borrar el Dashboard; pero
"queda en git history" sugiere conservarlo. Más seguro: ambas rutas conviven,
Angel decide cuál promociona a `/` con un commit posterior si el cockpit gana.

## D-002 — WebSocket por query param `?token=`, no header

**Decisión**: Cliente envía JWT vía `wss://host/tablero/api/v2/ws?token=<jwt>`.

**Razón**: La API `WebSocket` del navegador NO soporta headers custom. Subprotocols
funcionan pero son frágiles. Query param es estándar de facto (Octopus, Linear, etc.).

**Mitigación**: nginx ya redacta query strings en access logs (`$request_uri` con
`fastcgi_log_param`), y `?token=` se trata como secreto sensible. JWT expira
≤15min (per constitución X), reduce ventana.

## D-003 — Broker WS en memoria, NO Redis

**Decisión**: `dict[channel, set[WebSocket]]` en proceso uvicorn.

**Razón**: 2 usuarios (Angel + África), latencia local, sin necesidad de
horizontal scaling. Constitución VIII (stack ligero).

**Trade-off**: si uvicorn reinicia, todos los clientes ven `close 1006` y reconectan.
Aceptable; ya está cubierto por FR-006.

## D-004 — Workers asyncio en el mismo proceso, NO procesos separados

**Decisión**: Workers son `asyncio.Task`s lanzados desde `startup` de la app.

**Razón**: psutil + lecturas vault + Stripe API son I/O-bound; asyncio es la
forma natural. Workers polleen, computan delta, broadcastean.

## D-005 — Pre-flight psutil al startup, no en cada request

**Decisión**: `tablero/v2/health.py` importa `psutil` al load del módulo.
Si psutil no está instalado, el endpoint retorna 503 + el worker queda dormido.

**Razón**: el VPS no tiene psutil aún; el deploy lo instala via pip. Si falta,
el cockpit sigue cargando pero el widget VPS Health muestra "psutil no disponible".

## D-006 — react-grid-layout, no @dnd-kit-grid

**Decisión**: `react-grid-layout` para el sistema de grid drag+resize.

**Razón**: el brief lo nombra explícitamente. `@dnd-kit` ya está en el bundle
(Fase B+C) y es perfecto para listas/kanban, pero no maneja resize nativamente.

## D-007 — Layout persistido en localStorage por sub JWT, no en vault

**Decisión**: clave `cockpit_layout_<sub>` en localStorage.

**Razón**: el layout es preferencia UI per-dispositivo, no conocimiento. Vault
queda limpio. Si Angel cambia de dispositivo, vuelve al default; aceptable.

## D-008 — Tremor para gauges/sparklines, no recharts ni custom

**Decisión**: instalar `@tremor/react` para los componentes visuales de datos.

**Razón**: Tremor es Tailwind-first, dark-mode-friendly, accesible (ARIA out
of the box), bundle ~80KB gzipped. Recharts pesa más y requiere theming manual.

## D-009 — framer-motion, no Motion One ni Web Animations API directa

**Decisión**: `framer-motion@^11`.

**Razón**: brief lo exige. Pesa ~50KB gzipped pero la calidad de animación
(spring physics, layoutId transitions) lo justifica.

## D-010 — sonner para toaster Stripe

**Decisión**: `sonner` para el widget #12.

**Razón**: brief lo nombra; alternativa shadcn/toast pesa más y es menos elegante
visualmente. Sonner es 6KB.

## D-011 — class-variance-authority (cva) para variantes de widgets

**Decisión**: `class-variance-authority` para la definición de variantes
(tamaño, estado, color) de los componentes widget.

**Razón**: brief lo pide. Hace los widgets componibles y type-safe.

## D-012 — tailwindcss-animate para utilities CSS

**Decisión**: `tailwindcss-animate` plugin.

**Razón**: brief lo pide. Da utilities `animate-in`, `fade-in-0`, `slide-in-from-bottom-2`
que combinadas con framer-motion son ortogonales (framer para layout, animate para microinteracciones).

## D-013 — Activity Stream usa journald + hooks de agentes, NO un broker pub/sub

**Decisión**: el worker `activity` ejecuta `journalctl -fu nosvers-mcp -u nosvers-voice
-u nosvers-bot` en subprocess y parsea. Los agentes del unified-agent escriben adicionalmente
a `/home/nosvers/logs/agt_<id>_<ts>.json` que el worker tail-eea.

**Razón**: NO queremos introducir Redis/NATS. journald ya es el bus de eventos del VPS;
parsearlo es suficiente y la latencia <1s.

## D-014 — Wake Word widget consume `/voz/api/wake_state` (nuevo)

**Decisión**: añadir endpoint trivial al proyecto 001 (`voz/rest.py`) que retorne
`{state: "idle"|"listening"|"processing", last_wake_ts}`.

**Razón**: el cockpit es proyecto 002 pero el wake word vive en 001. Endpoint cruzado
es ligero (snapshot de variable en memoria).

**Alcance**: si no se puede modificar 001 ahora (riesgo regresión), el widget muestra
placeholder "estado integrado en próxima iteración" — los tests no exigen.

## D-015 — Bundle target: 1.5MB gzipped, codesplit por ruta

**Decisión**: Vite codesplit dinámico. `/cockpit` se importa lazy desde `App.tsx`
con `React.lazy(() => import('./pages/Cockpit'))`. Las libs nuevas (tremor,
framer-motion, react-grid-layout) viven en el chunk de `/cockpit`, no en `/`.

**Razón**: usuarios que abren `/` (Dashboard B+C) NO descargan el peso del cockpit.
Es la forma más natural de respetar el budget.
