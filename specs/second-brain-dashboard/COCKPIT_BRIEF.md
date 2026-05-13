# COCKPIT BRIEF — Rediseño visual estilo Mission Control

Angel ha pedido **abandonar el look Notion** del tablero v2 y rediseñar con estética **command center / mission control tecnológico**. NO es un proyecto nuevo, es rediseño del frontend del 002 conservando todos los endpoints v2 ya existentes (10 rutas + el WS que vamos a añadir).

## Filosofía visual

- Tema **oscuro permanente** (no light/dark toggle): fondo base `#0a0a0f`, paneles `#13131a` con blur
- Acentos: **verde NosVers** `#34d399`, naranja `#fb923c`, púrpura `#a78bfa`. Cero pastel.
- **Glassmorphism**: panels con `backdrop-blur-xl` + borde sutil semi-transparente
- Tipografía: **Inter** para UI, **JetBrains Mono** para datos técnicos y números
- **Animaciones obligatorias** con framer-motion: cada widget tiene entrada animada (fade-in + slide), updates con transiciones suaves
- Datos en vivo via **WebSocket** (`/tablero/api/v2/ws`), NO polling
- Densidad alta: como Grafana / Vercel dashboard / Linear, no como Notion

## Los 12 widgets a construir

Ordenados por prioridad de implementación:

### Tier 1 — Imprescindibles (semana 1)
1. **Claude Status** — Online/Listening/Offline + última interacción + tokens usados hoy
   - Luz LED pulsante grande según estado (verde online, ámbar listening, gris offline)
   - Sparkline de tokens últimas 24h
   - Source: `systemctl is-active nosvers-voz`, log del asistente, contador interno de tokens
2. **VPS Health** — CPU%, RAM%, disco%, network in/out, uptime, load avg
   - 4 gauges circulares animados (tremor)
   - Sparkline 60min de CPU debajo
   - Source: `psutil` en Python — endpoint nuevo `/v2/ws/health`
3. **Activity Stream** — log en vivo terminal-style
   - Tipografía monospace, scroll auto, cada línea con timestamp + nivel coloreado
   - Eventos: nueva nota, agente ejecutado, AEGIS, freqtrade, push git, MCP call
   - Source: WS subscribirse a `journalctl -f` + hooks de los agentes
4. **Agentes Status** — 7-8 agentes del unified-agent con estado
   - Nodo por agente (idle/running/error/last_run)
   - Cuando uno corre, animación de pulso
   - Source: `agentes_estado` del MCP

### Tier 2 — Importantes (semana 2)
5. **NosVers Revenue** — €/día, €/mes, gauge hacia objetivo M3 (600€)
   - Contador animado (cuenta-atrás visual hasta target)
   - Barra de progreso glow
   - Source: Stripe API (cargar STRIPE_SECRET_KEY del .env), nuevo endpoint `/v2/ws/stripe`
6. **AEGIS Briefing** — última activación + alertas activas
   - Texto + glow rojo si alerta crítica
   - Botón "ver briefing completo" → modal
   - Source: `knowledge_base/aegis/briefing_*.md` más reciente
7. **Vault Stats** — notas hoy/semana, etiquetas dominantes, autor activo
   - Gauges circulares + mini bar chart
   - Source: ya existe `/v2/stats` del backend
8. **Wake Word & Speaker ID** — estado del asistente Linux casa
   - "Esperando wake word" / "Escuchando" / "Procesando"
   - Waveform animado en vivo cuando está activo (Canvas API)
   - Source: estado del servicio nosvers-voz + WS push cuando se activa

### Tier 3 — Nice to have (semana 3)
9. **Gmail Mini** — 5 emails prioritarios
   - Avatars circulares, asunto truncado, hover-expand al panel completo
   - Requiere OAuth Google → marcar como BLOCKED_OAUTH_HUMAN si no hay credenciales
   - Source: gmail.googleapis.com API (Angel debe configurar service account)
10. **Próximos eventos calendario** — hoy + mañana
    - Cards glassmorphism timeline vertical
    - Source: Google Calendar API (mismo OAuth que Gmail)
11. **Freqtrade** — PnL del día, posiciones abiertas, sparkline equity
    - Verde/rojo según PnL, números grandes JetBrains Mono
    - Source: API local de freqtrade (verificar que está expuesta)
12. **Stripe Live Toaster** — notificación esquina inferior derecha cuando entra un pago
    - Sound opcional, slide-in animation, auto-dismiss 8s
    - Source: webhook Stripe → push a WS

## Layout

Grid responsivo con `react-grid-layout` (drag-to-rearrange + resize). Default layout:
- Top row (fila grande): Claude Status (1/4) | VPS Health (1/4) | Revenue (1/4) | AEGIS (1/4)
- Middle row: Activity Stream (2/4 ancha) | Wake Word (1/4) | Vault Stats (1/4)
- Lower row: Agentes (1/4) | Gmail (1/4) | Calendar (1/4) | Freqtrade (1/4)
- Stripe Toaster: floating, no en grid

Angel puede mover y redimensionar; layout se persiste en localStorage por usuario.

## Stack frontend

Mantener lo que ya hay y AÑADIR:
- `framer-motion` — animaciones de entrada y transiciones
- `@tremor/react` — gauges, sparklines, bar charts (mejor que recharts para tema oscuro)
- `lucide-react` — iconos (ya estaba)
- `react-grid-layout` — grid drag-and-drop
- `class-variance-authority` (cva) — variantes de componentes
- `tailwindcss-animate` — utilities de animación
- `sonner` — toaster para Stripe Live

NO se necesita reemplazar shadcn/ui, se usa para botones, modales, etc.

## Stack backend (cambios)

Añadir al `tablero/rest.py` o crear `tablero/ws.py`:
- `WebSocket /tablero/api/v2/ws` con autenticación JWT por query param `?token=...`
- Broker en memoria (set de connections, dict por canal)
- Canales: `health`, `claude`, `activity`, `agentes`, `revenue`, `aegis`, `wake`
- Workers asyncio que polleen cada N segundos y broadcasteen al broker

Endpoint nuevo síncrono `/tablero/api/v2/health` (psutil) por si alguien quiere snapshot sin WS.

## Constraints

- Mantener todos los 10 endpoints v2 existentes intactos
- El frontend antiguo del tablero v2 se REEMPLAZA pero los archivos quedan en git history para volver atrás si algo falla
- NO romper la PWA voice (`/home/nosvers/public_html/voz/`) — ese es proyecto 001 separado
- Soberanía: usar APIs propias (Stripe, Gmail) cuando hay credenciales; si no hay, widget muestra placeholder elegante
- Performance: animaciones a 60fps, payload WS < 5KB por update, reconexión automática si se cae el WS
- Privacidad: como Angel y África ven todo (decisión sesión 14.3 del 001), todos los widgets son compartidos

## Flujo Spec Kit

Como esta es **Fase D** del proyecto 002 (no proyecto separado), inicializar en
`specs/003-cockpit-redesign/` dentro del mismo directorio del 002:

1. `/speckit-specify` desde este brief
2. `/speckit-clarify` — solo si crítico, decidir solo si no es obvio
3. `/speckit-plan` — stack definitivo
4. `/speckit-tasks` — desglose
5. `/speckit-implement` — ejecuta sin parar
6. Commits agrupados por widget (12 commits máx) + setup inicial + commit del WebSocket layer

## Bug telegram_enviar ya conocido

NO usar `telegram_enviar` para Telegrams intermedios. Solo UNO al final. Si se cuelga >30s, marcar MCP_STALL_RESOLVED_BY_OPUS_MOBILE en tasks.md y dejarlo. Angel/Opus móvil mandará el Telegram desde su sesión.

## Definition of done

- 12 widgets visibles en producción (`tablero.72.61.160.108.nip.io`)
- 8 funcionando con datos reales (Tier 1+2)
- 4 con OAuth marcados como BLOCKED y mostrando placeholder elegante (Gmail/Calendar) o con datos si la API está accesible (Freqtrade/Stripe)
- WS con reconexión automática
- Layout drag-and-drop persiste por usuario
- Tests: smoke tests del WS, unit tests de los workers
- Bundle final < 1.5MB (acepto un poco más que los 684K actuales por las libs nuevas)

## Estimación

Si fuera trabajo humano: 2-3 semanas. Para Claude Code: probablemente 4-6h, similar a Fase B+C combinada.

---
*Brief preparado por Claude Opus 4.7 (sesión móvil), 2026-05-13 15:50 UTC*

---

## ADDENDUM 1 — Detalle del Widget 1 (Claude Status) — Red neuronal animada

Angel pidió que la indicación visual del estado de Claude sea **una red neuronal estilo grafo de Obsidian**, NO un simple LED pulsante. Reemplaza el LED de la especificación inicial.

### Visual

- Canvas (~280×200px en el widget) con **8-12 nodos circulares** conectados por líneas
- Física **force-directed**: cada nodo tiene posición + velocidad, las conexiones aplican fuerza atractiva (resorte), nodos cercanos se repelen (Coulomb-like). Damping suave para que no oscile eternamente.
- **Color de nodos y conexiones depende del estado**:

| Estado | Nodos | Conexiones | Movimiento | Pulse |
|---|---|---|---|---|
| `offline` | Gris `#3f3f46` apagado | Gris muy tenue, casi invisibles | Casi quieto, drift mínimo | Sin pulso |
| `listening` | Verde NosVers `#34d399` con leve glow | Verde semi-transparente | Movimiento suave, ondulante | Pulso lento sincronizado todos los nodos (~1.5s) |
| `thinking` | Naranja `#fb923c` brillante | Naranja con destellos | Activo, las conexiones se "encienden" en oleadas como sinapsis | Pulso rápido aleatorio por nodo |
| `speaking` | Púrpura `#a78bfa` muy brillante | Púrpura con flujo direccional | Ondas de activación se propagan del centro hacia fuera | Pulse sincronizado al ritmo del audio TTS si disponible |
| `online` (idle) | Verde NosVers tenue | Verde tenue | Drift lento, casi imperceptible | Cada N segundos un nodo individual pulsa breve |

### Implementación recomendada

- Canvas 2D nativo (NO Three.js, sería overkill para un widget pequeño)
- Bucle `requestAnimationFrame` con throttling: 60fps cuando hay animación intensa (thinking/speaking), 30fps en listening, 15fps en offline (ahorra batería en móvil)
- Algoritmo: Verlet integration simple o Euler. Hay implementaciones de force-directed en <200 líneas en JS, no hace falta D3 entero.
- Componente React aislado `<NeuralGraph state={status} />` que recibe estado via prop y reacciona. Posiciones de nodos persisten entre renders.

### Sin dependencias pesadas

NO añadir `d3`, `react-force-graph`, ni `vis-network`. Implementación canvas custom de unos 150-250 LOC. La animación es el alma del widget, merece código propio bien hecho.

### Reactividad al estado real

El estado viene por WebSocket en el canal `claude` con shape:
```json
{
  "state": "listening" | "thinking" | "speaking" | "online" | "offline",
  "last_interaction": "2026-05-13T16:00:00Z",
  "current_tokens": 1234,
  "tokens_today": 45678
}
```

Cuando el state cambia, transición suave de 800ms en colores y velocidad del movimiento (no salto brusco).

### Toques finales

- Hover sobre un nodo: tooltip pequeño con "Claude · NosVers"
- Click: expande el widget mostrando estadísticas más detalladas (tokens hoy, modelo activo, última conversación)
- Si tokens_today > umbral diario, un nodo extra aparece con color de alerta

Esto es la **firma visual del cockpit**. Ponedle cariño.
