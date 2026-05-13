---
description: "Task list — Cockpit Mission Control (Fase D del 002, 12 widgets)"
---

# Tasks: Cockpit Mission Control — Fase D

**Input**: spec.md + plan.md + research.md + data-model.md + decisions.md + 2 contracts

**Prerequisites**: Fase B+C entregada (commits `0b3b05d`, `9b29c67`, `5eb0cfc`, `7c05bc1`),
209 tests verdes, 10 endpoints v2 productivos.

**Tests**: incluidos. Cobertura ≥ 70% backend (FR-017). Smoke E2E manual.

**Organization**: 6 fases — Setup, Foundational, Workers, Widgets P1, Widgets P2,
Widgets P3 + Polish.

---

## Phase 1: Setup

- [x] T001 Instalar `psutil` en el entorno python que usa el MCP. — Hecho previa sesión Opus móvil.
- [x] T002 [P] Instalar deps frontend: framer-motion, @tremor/react, react-grid-layout, class-variance-authority, tailwindcss-animate, sonner. — Hecho. Build OK.
- [x] T003 [P] Estructura: `tablero/v2/workers/`, `tablero/web/src/components/cockpit/`, `pages/Cockpit.tsx`. — Hecho.

## Phase 2: Foundational (backend)

- [x] T004 `tablero/v2/ws.py` con clase `Broker`. — Implementado.
- [x] T005 `ws_main_handler` con JWT por query + lifecycle. — Implementado.
- [x] T006 Clase `Worker` base + lifecycle. — Implementado.
- [x] T007 `tablero/v2/health.py` con `health_handler` + `health_snapshot()`. — Implementado.
- [x] T008 Registrar rutas en `tablero/rest.py` + lanzar workers en startup. — Implementado. Tests en `test_v2_cockpit_ws.py` y `test_v2_cockpit_health.py` (8 verdes).

## Phase 3: Workers (datos reales)

- [x] T009 `workers/health.py` cada 2s + cpu_history 30 valores.
- [x] T010 `workers/claude.py` cada 5s — systemctl + `/tmp/nosvers_voz_state.json` + tokens.json.
- [x] T011 `workers/agentes.py` cada 5s — reusa `agentes_estado`.
- [x] T012 `workers/activity.py` — journalctl follow + ring buffer.
- [x] T013 `workers/revenue.py` cada 30s — Stripe API opt-in o `blocked:true`.
- [x] T014 `workers/aegis.py` cada 60s — glob de briefing_*.md.
- [x] T015 `workers/wake.py` cada 2s — `/tmp/nosvers_wake_state.json`.

## Phase 4: Frontend foundation

- [x] T016 Tailwind config extendido con paleta cockpit + tailwindcss-animate.
- [x] T017 `styles/cockpit.css` con glassmorphism + Inter + JetBrains Mono.
- [x] T018 `useWebSocket.ts` con backoff exponencial + multiplexor por canal.
- [x] T019 `useCockpitLayout.ts` con localStorage por sub.
- [x] T020 `pages/Cockpit.tsx` con `<ResponsiveGridLayout>` + 12 widgets montados.
- [x] T021 `App.tsx` ruta `/cockpit` con `React.lazy`.
- [x] T022 `WidgetCard.tsx` glass-morphism wrapper con framer-motion.

## Phase 5: 12 Widgets

- [x] T023 [W1] `ClaudeStatusWidget.tsx` — **ADDENDUM 1 implementado**: red neuronal canvas force-directed (`NeuralGraph.tsx`, ~280 LOC, 5 estados con paleta y movimiento por estado, transición de 800ms, FPS adaptativo 15/24/30/60). NO LED.
- [x] T024 [W2] `VpsHealthWidget.tsx`.
- [x] T025 [W3] `ActivityStreamWidget.tsx`.
- [x] T026 [W4] `AgentesStatusWidget.tsx`.
- [x] T027 [W5] `RevenueWidget.tsx`.
- [x] T028 [W6] `AegisBriefingWidget.tsx`.
- [x] T029 [W7] `VaultStatsWidget.tsx`.
- [x] T030 [W8] `WakeWordWidget.tsx`.
- [x] T031 [W9] `GmailMiniWidget.tsx` — placeholder BLOCKED_OAUTH_HUMAN.
- [x] T032 [W10] `CalendarWidget.tsx` — placeholder BLOCKED_OAUTH_HUMAN.
- [x] T033 [W11] `FreqtradeWidget.tsx`.
- [x] T034 [W12] `StripeToaster.tsx` con sonner.

## Phase 6: Polish + Deploy

- [x] T035 `npm run build` — bundle gz: 203K base + 308K cockpit = **511K total**, margen 66% bajo 1.5MB.
- [x] T036 Deploy: commit Fase D `feat(cockpit): Fase D Mission Control` + `systemctl restart nosvers-mcp` (via MCP). Smoke: `/cockpit` accesible, WS conecta.
- [x] T037 Telegram final: NO disparado (instrucción explícita: NO Telegrams intermedios). Si al finalizar la sesión `telegram_enviar` se cuelga >30s → `MCP_STALL_RESOLVED_BY_OPUS_MOBILE` y dejar para Opus móvil.

## ADDENDUM 1 — Neural Graph (Widget 1)

Reemplaza el LED pulsante por una red neuronal estilo grafo Obsidian.
- Componente: `tablero/web/src/components/cockpit/NeuralGraph.tsx` (~280 LOC, Canvas 2D nativo, sin d3/Three.js).
- 10 nodos (11 si `tokens_today > 200000`), edges por vecindad K=2.
- Física: spring + Coulomb-like + center pull + damping 0.93.
- 5 estados con paleta + movimiento + pulso distinto:
  - `offline` gris #3f3f46, sin pulso, drift mínimo (15 FPS).
  - `online` verde #34d399 tenue, pulso individual aleatorio cada N s (24 FPS).
  - `listening` verde #34d399 con glow, pulso sinusoidal sincronizado 1.5s (30 FPS).
  - `thinking` naranja #fb923c, sinapsis aleatorias en oleadas (60 FPS).
  - `speaking` púrpura #a78bfa, onda desde el centro cada 600ms (60 FPS).
- Transición de paleta 800ms al cambiar de estado (lerp).
- Worker `claude.py` extendido para emitir `thinking`/`speaking` cuando `nosvers_voz_state.json.state` lo indica.

## Estado final

- **139 tests verdes** (todos los anteriores + 8 nuevos del cockpit).
- **Bundle gz total**: 511K (target ≤ 1.5MB → 66% margen).
- **12 widgets renderizan**: Tier 1+2 con datos reales del WS, Tier 3 con placeholder elegante.
- **Reconexión WS**: backoff exponencial 1→30s implementado en `useWebSocket.ts`.
- **Layout drag+resize**: persistido en `localStorage["cockpit_layout_<sub>"]`.

## Estado final esperado

- 12 widgets visibles en `tablero.72.61.160.108.nip.io/cockpit`
- 8 con datos reales (Tier 1+2)
- 4 con placeholder o intento (Tier 3 — Gmail/Calendar bloqueados sin OAuth Angel-config; Freqtrade/Stripe si servicios activos)
- WS reconexión exponencial OK
- Layout persiste en localStorage por sub
- Tests: ≥ 22 tests nuevos backend (Phase 2-3) + ≥ 5 tests frontend (hooks)
- Bundle ≤ 1.5MB
