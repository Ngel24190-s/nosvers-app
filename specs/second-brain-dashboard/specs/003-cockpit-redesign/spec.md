# Feature Specification: Mission Control Cockpit (Fase D del proyecto 002)

**Feature Branch**: `003-cockpit-redesign` (mismo monorepo `main`; subproyecto del 002)

**Created**: 2026-05-13

**Status**: Draft

**Input**: User description: "Rediseño visual del tablero v2 con estética mission control / command center: tema oscuro permanente (#0a0a0f base, #13131a panels con glassmorphism), acentos verde NosVers #34d399 + naranja #fb923c + púrpura #a78bfa, Inter + JetBrains Mono, framer-motion en todos los widgets, datos en vivo por WebSocket (NO polling), densidad alta tipo Grafana/Vercel/Linear. 12 widgets en grid drag-to-rearrange (react-grid-layout) persistido por usuario. Backend nuevo: WS `/tablero/api/v2/ws` con JWT por query + broker en memoria + canales (health, claude, activity, agentes, revenue, aegis, wake) + workers asyncio. Endpoint síncrono `/v2/health` (psutil) para snapshot. Mantener 10 endpoints v2 existentes intactos. NO romper PWA voz. Soberanía: usar APIs propias cuando hay credenciales, placeholders elegantes si no. Performance: 60fps, payload WS <5KB, reconexión automática. Privacidad: todos los widgets compartidos entre Angel y África."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Cockpit operativo en una sola pantalla (Priority: P1)

Angel está en obra (desamiantage), abre tablero desde el móvil, y necesita en 3 segundos saber: ¿está Claude online? ¿está el VPS sano? ¿hay alguna alerta crítica? ¿cuánto facturó NosVers hoy? En la fila superior del cockpit ve los 4 widgets clave (Claude Status, VPS Health, Revenue, AEGIS Briefing) con luces LED, gauges animados y números grandes. No hace clic en nada — sólo mira. Si todo está verde, cierra el móvil y vuelve al trabajo. Si una LED parpadea rojo, expande el widget y actúa.

**Why this priority**: Sin esta fila, el tablero es "una página bonita más". Esta historia es la frontera entre "Notion-clone" y "torre de control". Angel reconoce el estado del negocio sin leer texto.

**Independent Test**: Con un JWT válido, abrir `/cockpit`. En <2s sobre 4G se ven 4 panels con datos reales (Claude online, CPU del VPS, ingresos del día Stripe o placeholder, último briefing AEGIS o "Sin alertas"). Cada panel tiene animación de entrada distinta (no son todos iguales). LED de Claude pulsa cada 2s si está online.

**Acceptance Scenarios**:
1. **Given** Angel autenticado como `angel`, **When** abre `/tablero/cockpit`, **Then** la fila superior pinta los 4 widgets P1 en <1s después de conectar el WS.
2. **Given** servicio `nosvers-voz` parado, **When** Angel mira el widget Claude Status, **Then** la LED se renderiza gris y el texto dice "Offline" en JetBrains Mono.
3. **Given** un alerta AEGIS reciente con nivel `crítico`, **When** el widget AEGIS renderiza, **Then** el borde tiene glow rojo animado y un botón "ver briefing completo" abre el .md en modal.

---

### User Story 2 — Datos en vivo sin recargar (Priority: P1)

Angel deja el cockpit abierto en una segunda pestaña del Linux casa. Mientras trabaja en VS Code, el AGT-02 (Instagram) se ejecuta automáticamente. Sin tocar nada, el widget Agentes muestra el nodo de AGT-02 pulsando naranja, y el Activity Stream añade una línea `2026-05-13 16:42:11 [INFO] AGT-02 instagram_curator: ejecución iniciada`. Cuando termina, la línea se completa con `[OK] 5 posts generados (3.2s)` y el nodo vuelve a verde. Sin polling — el WS empujó el evento.

**Why this priority**: Sin tiempo real, no es cockpit, es sólo un dashboard polleado. La diferencia es perceptiva: Angel ve que el sistema vive.

**Independent Test**: Abrir cockpit en una pestaña. En otra terminal, lanzar `python3 /home/nosvers/agents/agt_eisenia.py`. Sin recargar la pestaña, en <3s el Activity Stream añade la línea correspondiente y el widget Agentes anima el nodo de Eisenia.

**Acceptance Scenarios**:
1. **Given** WS conectado, **When** psutil muestra CPU subiendo de 5% a 60%, **Then** el gauge del VPS Health interpola suavemente en <500ms.
2. **Given** WS conectado, **When** un agente del unified-agent emite log con nivel `ERROR`, **Then** el Activity Stream añade la línea coloreada rojo y la cuenta de errores del widget Agentes incrementa.
3. **Given** WS cae (servicio reiniciado), **When** cliente detecta `close`, **Then** intenta reconectar con backoff exponencial (1s, 2s, 4s, 8s, max 30s) y muestra un indicador "reconectando…" en la esquina.

---

### User Story 3 — Layout drag-to-rearrange persistente por usuario (Priority: P2)

África abre el cockpit por primera vez desde su móvil. El layout default tiene Revenue en la fila superior, pero a ella le importa más Vault Stats. Arrastra Vault Stats a la primera posición, agranda el widget de Gmail, y cierra el navegador. Al día siguiente vuelve a abrir: ve su layout personalizado intacto. Angel, en su Linux, sigue viendo el suyo (no se mezclan).

**Why this priority**: Pensar el cockpit como periódico estático es perder. Cada usuario tiene prioridades distintas; el cockpit debe ceder.

**Independent Test**: Autenticar como `africa`, arrastrar dos widgets, refrescar — orden persistido en `localStorage["cockpit_layout_africa"]`. Autenticar como `angel` en otra pestaña, layout intacto y diferente.

**Acceptance Scenarios**:
1. **Given** layout default cargado, **When** usuaria arrastra el widget Gmail de fila 3 col 2 → fila 1 col 1, **Then** al recargar la página el widget sigue en fila 1 col 1.
2. **Given** layout personalizado, **When** usuaria pulsa "restaurar default", **Then** vuelve al layout original sin perder la sesión.
3. **Given** Angel y África en pestañas distintas mismo navegador (no aplica multi-usuario real, pero localStorage va por JWT.sub), **When** Angel modifica su layout, **Then** layout de África no cambia.

---

### User Story 4 — Stripe Live Toaster (Priority: P3)

Angel está en el cockpit cuando entra un pago de 45€ por un Extrait Vivant. En la esquina inferior derecha aparece un toast con slide-in: avatar de Stripe, "Pago recibido — 45,00€ — Extrait Vivant Lombric". Auto-dismiss en 8s. Si Angel hace clic, lo lleva al panel completo de Stripe (o al detalle del pago). Sin sonido por defecto (lo activa con un toggle en preferencias).

**Why this priority**: Es nice-to-have pero crea "tirón de dopamina" — convierte el cockpit en algo que Angel querrá dejar abierto.

**Independent Test**: Disparar un evento Stripe simulado vía webhook (`curl` al endpoint local). En <2s aparece toast con slide-in animation. Auto-dismiss verifica con `setTimeout`.

**Acceptance Scenarios**:
1. **Given** webhook Stripe configurado (o stub), **When** entra evento `payment_intent.succeeded`, **Then** WS empuja al canal `revenue` y aparece toast.
2. **Given** preferencia `cockpit_sound=true` en localStorage, **When** llega toast, **Then** reproduce ding corto (`/static/ding.mp3`, <2KB).
3. **Given** 5 pagos en 5s, **When** aparecen, **Then** stack vertical (no se solapan) con un máximo de 3 visibles y resto en cola.

---

## Functional Requirements *(mandatory)*

**FR-001** El sistema DEBE servir un endpoint `GET /tablero/api/v2/health` (síncrono, sin auth o con auth opcional) que retorne `{cpu_pct, ram_pct, ram_used_mb, ram_total_mb, disk_pct, disk_used_gb, disk_total_gb, load_1, load_5, load_15, net_in_kbps, net_out_kbps, uptime_s}` calculado con `psutil`.

**FR-002** El sistema DEBE exponer `WebSocket /tablero/api/v2/ws` que acepte `?token=<JWT>` por query string (workaround: WS no soporta header `Authorization` de forma uniforme entre navegadores) y rechace conexiones sin token válido con código de cierre 4401.

**FR-003** El broker WS DEBE soportar los canales: `health`, `claude`, `activity`, `agentes`, `revenue`, `aegis`, `wake`. Cliente se subscribe enviando `{"type":"subscribe","channel":"<nombre>"}` y se desuscribe con `unsubscribe`.

**FR-004** Cada canal DEBE tener un worker asyncio que poletee la fuente con período configurable (default: health=2s, agentes=5s, revenue=30s, aegis=60s) y broadcastee SOLO si el snapshot cambió respecto al último (delta-only).

**FR-005** El payload por mensaje WS DEBE ser ≤ 5KB después de JSON serialize. Si excede, el worker hace sampling (p. ej. Activity Stream trunca a últimas 50 líneas).

**FR-006** El cliente DEBE reconectar con backoff exponencial (1s, 2s, 4s, 8s, 16s, máx 30s) ante cierres distintos de 1000 (normal closure) y mostrar indicador visual "reconectando…".

**FR-007** El cockpit DEBE renderizar 12 widgets:
- **Tier 1 (P1, datos reales obligatorios)**: Claude Status, VPS Health, Activity Stream, Agentes Status.
- **Tier 2 (P2, datos reales si credenciales OK)**: NosVers Revenue, AEGIS Briefing, Vault Stats, Wake Word.
- **Tier 3 (P3, placeholders elegantes aceptados)**: Gmail Mini, Próximos eventos calendario, Freqtrade, Stripe Live Toaster.

**FR-008** El layout DEBE ser drag-to-rearrange y resize por widget usando `react-grid-layout`. Cambios se persisten en `localStorage["cockpit_layout_<sub>"]`. Botón "restaurar default" vuelve al layout inicial.

**FR-009** Tema oscuro permanente: fondo base `#0a0a0f`, paneles `#13131a` con `backdrop-blur-xl` y borde `rgba(255,255,255,0.06)`. NO hay toggle a light. Acentos: `#34d399` (verde NosVers), `#fb923c` (naranja), `#a78bfa` (púrpura), `#ef4444` (rojo crítico).

**FR-010** Tipografía: `Inter` para todo el UI; `JetBrains Mono` para datos técnicos (gauges, contadores, timestamps, logs).

**FR-011** Cada widget DEBE tener animación de entrada con `framer-motion` (fade + slide desde abajo, stagger 50ms entre widgets) y animar las transiciones de datos (gauges interpolan, contadores hacen "count up").

**FR-012** El cockpit DEBE mantener intactos los 10 endpoints v2 ya existentes (`/v2/capturar`, `/v2/nota`, `/v2/nota/archivar`, `/v2/nota/restaurar`, `/v2/proyectos` GET+PATCH, `/v2/wiki-index`, `/v2/vault/tree`, `/v2/infra/status`, `/v2/agentes/catalogo`, `/v2/agentes/ejecutar`).

**FR-013** El cockpit DEBE convivir con el tablero v2 actual: ruta `/cockpit` añade el nuevo shell sin reemplazar el Dashboard de Fase B+C. El usuario decide cuál usa.

**FR-014** Performance: el bundle final compactado DEBE ser ≤ 1.5MB. Animaciones DEBEN mantenerse a 60fps sobre Chrome desktop estándar.

**FR-015** Privacidad: TODOS los widgets son compartidos entre `angel` y `africa` (paridad total, alineado con decisión sesión 14.3 del proyecto 001). El cockpit NO filtra contenido por autor — sólo el layout es per-user.

**FR-016** Soberanía: cuando una integración externa (Stripe, Gmail, Google Calendar) no tiene credenciales en `.env`, el widget DEBE mostrar placeholder elegante con texto "BLOCKED_OAUTH_HUMAN — configurar credenciales en .env" (sin romper el cockpit).

**FR-017** Tests: cobertura del backend WS y workers ≥ 70% (más bajo que B+C por ser código asyncio polling, difícil de testear exhaustivamente sin flakiness). Smoke E2E mínimo: conectar WS, recibir mensaje en canal `health`, desconectar.

## Success Criteria *(mandatory)*

**SC-001** Carga inicial del cockpit (HTML + JS + WS connect + primer frame de cada widget) ≤ 2.5s sobre 4G.

**SC-002** Latencia entre evento real (p. ej. agente lanzado por cron) y aparición en Activity Stream ≤ 3s p95.

**SC-003** Drag-to-rearrange un widget: el reordenamiento se persiste en localStorage y el layout vuelve a cargar idéntico tras refresh, ≤ 200ms.

**SC-004** Reconexión automática del WS tras caída del backend (test: `systemctl restart nosvers-mcp`): reconexión completa ≤ 35s (cubriendo backoff exponencial hasta 30s).

**SC-005** Bundle frontend gz < 1.5MB. Lighthouse Performance ≥ 80 en cockpit con WS desconectado.

**SC-006** 12 widgets visibles en producción `tablero.72.61.160.108.nip.io/cockpit` tras el deploy.

**SC-007** Ningún test del 001/002 anterior regresa (78 + 131 = 209 tests siguen verdes).

## Out of Scope

- Sustituir el Dashboard de Fase B+C (queda accesible en `/`); el cockpit es ruta nueva `/cockpit`.
- Multi-tenant real más allá de Angel/África (proyecto 001 lo dejó cerrado).
- Light theme.
- Integración con sistemas no listados (Slack, Discord, etc.).
- Histórico/series temporales largas (mostramos sparkline de últimos 60min, no charts persistidos).
