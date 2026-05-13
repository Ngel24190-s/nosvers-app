# Implementation Plan: Cockpit Mission Control (Fase D del 002)

**Branch**: monorepo `main` (sub-proyecto del 002, no rama separada)

**Date**: 2026-05-13

**Spec**: [spec.md](./spec.md) · [decisions.md](./decisions.md)

## Summary

Añadir un cockpit (ruta `/cockpit`) sobre el frontend de Fase B+C ya en producción.
12 widgets renderizados en grid drag+resize, datos por WebSocket. Backend: nuevo
módulo `tablero/v2/ws.py` (broker + auth + workers asyncio) + nuevo endpoint
síncrono `/v2/health` (psutil). Frontend: nuevo `pages/Cockpit.tsx` codesplit-lazy,
12 componentes `components/cockpit/*.tsx`, hook `useWebSocket`, hook `useCockpitLayout`.
Stack añadido: `framer-motion`, `@tremor/react`, `react-grid-layout`, `cva`,
`tailwindcss-animate`, `sonner`. Mantiene los 10 endpoints v2 existentes intactos
y el Dashboard de B+C en `/`.

## Technical Context

**Language/Version**: Python 3.11 (backend, mismo proceso uvicorn que mcp_server),
TypeScript 5.x (frontend, Vite 5 + React 18).

**Primary Dependencies — backend (nuevas)**:
- `psutil ^5.9`: métricas del VPS (CPU, RAM, disco, red, uptime, load).
- (stdlib) `asyncio`, `WebSocket` de Starlette ya disponible.
- Re-uso: `voz.auth.validar_token` para JWT en WS.

**Primary Dependencies — frontend (nuevas)**:
- `framer-motion ^11`: animaciones de entrada y transiciones.
- `@tremor/react ^3`: gauges circulares, sparklines, mini-bar.
- `react-grid-layout ^1.5`: grid drag+resize.
- `class-variance-authority ^0.7`: variantes type-safe de widgets.
- `tailwindcss-animate ^1.0`: utilities CSS keyframes.
- `sonner ^1.5`: toaster Stripe.

**Storage**: layout cliente en localStorage. Backend en memoria (broker dict, deltas).
Vault intacto.

**Testing**: pytest backend (smoke WS handshake + worker delta). vitest frontend
(snapshot widgets, hook reconexión). Sin Playwright en esta fase.

**Target Platform**: VPS Hostinger (srv1313138.hstgr.cloud), nginx delante,
subdominio dev `tablero.72.61.160.108.nip.io`, prod futuro `tablero.nosvers.com`.

**Project Type**: Web application (extiende 002).

**Performance Goals** (FR-014 + SC-001..SC-005):
- Cockpit primera pantalla útil ≤ 2.5s sobre 4G.
- Animaciones 60fps en Chrome desktop.
- Payload WS por mensaje ≤ 5KB.
- Reconexión WS completa ≤ 35s con backoff exponencial.

**Constraints**:
- Constitución I (Soberanía): Stripe/Gmail/Calendar son opt-in con credenciales locales.
- Constitución II (MCP-first): el cockpit consume datos que los workers calculan
  re-usando funciones del MCP (agentes_estado, sistema_estado).
- Constitución III (Vault SoT): no añade storage; layout en localStorage.
- Constitución V (No regresión): 10 endpoints v2 intactos, Dashboard B+C intacto.
- Constitución VII (Multi-user): JWT exigido en WS; paridad Angel/África.
- Constitución VIII (Stack ligero): sin Next/Remix. Tremor + framer-motion son libs,
  no metaframeworks.
- Constitución X (Security): JWT por query param con expiración corta; nginx redacta
  query strings en logs.

## Constitution Check

| Principio | Estado | Justificación |
|---|---|---|
| I. Soberanía | ✅ | Stripe/Gmail/Calendar opt-in con credenciales locales (.env). Sin Vercel/Supabase. |
| II. MCP-first | ✅ | Workers re-usan funciones MCP existentes (agentes_estado, sistema_estado). |
| III. Vault SoT | ✅ | Layout en localStorage. Vault no toca. |
| IV. Reuse 001 | ✅ | `voz.auth.validar_token` re-usado para JWT WS. |
| V. No regresión | ✅ | 10 endpoints v2 intactos. Dashboard B+C accesible en `/`. |
| VI. Read-only Fase A | ✅ N/A | Fase D abre lecturas tiempo-real, no escribe. |
| VII. Multi-user | ✅ | JWT por query exigido. Paridad. |
| VIII. Stack ligero | ✅ | 6 libs nuevas listadas y justificadas. Sin metaframeworks. |
| IX. Observability | ✅ | Workers loguean en formato `rid=… channel=… delta_bytes=… latency_ms=…`. |
| X. Security | ✅ | JWT por query OK (D-002). Tokens ≤15min. nginx redacta query. |

**Gate**: PASS. Sin Complexity Tracking.

## Project Structure

```text
specs/003-cockpit-redesign/
├── plan.md
├── spec.md
├── decisions.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── ws_main.openapi.yaml
│   └── health.openapi.yaml
└── tasks.md
```

### Source Code

```text
/home/nosvers/
├── tablero/
│   ├── rest.py                  # ← edit: añade rutas /v2/ws y /v2/health
│   ├── v2/
│   │   ├── ws.py                # NUEVO: broker, JWT auth, lifecycle WS
│   │   ├── health.py            # NUEVO: endpoint psutil sync + worker
│   │   ├── workers/
│   │   │   ├── __init__.py      # NUEVO
│   │   │   ├── health.py        # NUEVO: poll psutil cada 2s
│   │   │   ├── claude.py        # NUEVO: poll systemctl + .voz_state
│   │   │   ├── activity.py      # NUEVO: journalctl tail
│   │   │   ├── agentes.py       # NUEVO: poll agentes_estado
│   │   │   ├── revenue.py       # NUEVO: poll Stripe API o stub
│   │   │   ├── aegis.py         # NUEVO: glob knowledge_base/aegis/*.md
│   │   │   └── wake.py          # NUEVO: lee voz state file
│   └── web/
│       ├── package.json         # ← edit: 6 deps nuevas
│       ├── tailwind.config.ts   # ← edit: theme dark + colores cockpit + tailwindcss-animate
│       ├── src/
│       │   ├── App.tsx          # ← edit: ruta /cockpit con React.lazy
│       │   ├── pages/
│       │   │   └── Cockpit.tsx  # NUEVO
│       │   ├── components/cockpit/
│       │   │   ├── CockpitShell.tsx        # NUEVO: grid + header
│       │   │   ├── WidgetCard.tsx          # NUEVO: glass wrapper
│       │   │   ├── ClaudeStatusWidget.tsx
│       │   │   ├── VpsHealthWidget.tsx
│       │   │   ├── ActivityStreamWidget.tsx
│       │   │   ├── AgentesStatusWidget.tsx
│       │   │   ├── RevenueWidget.tsx
│       │   │   ├── AegisBriefingWidget.tsx
│       │   │   ├── VaultStatsWidget.tsx
│       │   │   ├── WakeWordWidget.tsx
│       │   │   ├── GmailMiniWidget.tsx
│       │   │   ├── CalendarWidget.tsx
│       │   │   ├── FreqtradeWidget.tsx
│       │   │   └── StripeToaster.tsx
│       │   ├── hooks/
│       │   │   ├── useWebSocket.ts         # NUEVO
│       │   │   ├── useCockpitLayout.ts     # NUEVO
│       │   │   └── useTokenSparkline.ts    # NUEVO
│       │   └── styles/
│       │       └── cockpit.css             # NUEVO: glassmorphism + fonts
└── voz/
    └── rest.py                  # ← (opcional D-014) endpoint /voz/api/wake_state

tests/
├── tablero/
│   ├── test_ws_handshake.py             # NUEVO: conectar/desconectar
│   ├── test_ws_auth.py                  # NUEVO: 4401 sin token
│   ├── test_ws_broker.py                # NUEVO: subscribe/broadcast
│   ├── test_health_endpoint.py          # NUEVO: psutil sync
│   ├── test_worker_health.py            # NUEVO: delta-only
│   └── test_worker_agentes.py           # NUEVO
└── (frontend) tablero/web/src/tests/
    ├── useWebSocket.test.ts
    └── useCockpitLayout.test.ts
```

## Phase Plan

### Phase 0 — Research (research.md)

Investigaciones:
1. ¿Tremor sirve para el look "command center"? → SÍ (theming Tailwind directo,
   `bg-gray-950` etc.), pero gauges son básicos; sparklines son buenos.
2. ¿WebSocket en Starlette + uvicorn ya está disponible sin extras? → SÍ
   (`from starlette.websockets import WebSocket`).
3. ¿psutil sobre VPS Hostinger funciona? → SÍ, pero `psutil.cpu_percent(interval=1)`
   bloquea 1s. Solución: usar `interval=None` con primer call + segundo call diferido.
4. ¿react-grid-layout pesa demasiado? → 50KB gzipped, aceptable. Tiene CSS propio.
5. ¿Cómo Activity Stream sin Redis? → `journalctl --follow -u ...` en subprocess +
   parse línea por línea. Stream stdout → asyncio.Queue → broadcast.

### Phase 1 — Design (data-model + contracts + quickstart)

- **data-model.md**: define `WSMessage`, `Channel`, `HealthSnapshot`, `ClaudeSnapshot`,
  `AgentNode`, `ActivityLine`, `RevenueSnapshot`, `AegisAlert`.
- **contracts/ws_main.openapi.yaml**: documenta el protocolo WS (no es REST estricto
  pero usamos OpenAPI extensión para el handshake).
- **contracts/health.openapi.yaml**: el endpoint síncrono.
- **quickstart.md**: cómo levantar el cockpit en local + cómo deployar al VPS.

### Phase 2 — Tasks (tasks.md, generado abajo)

Desglose en 18 tareas:
- 3 Setup (deps backend + frontend + estructura).
- 4 Foundational (broker, JWT WS, workers base, lifecycle).
- 3 Workers (health, claude, agentes — son los P1 que aporta datos reales).
- 12 Widgets (1 por widget — uno marcado BLOCKED_OAUTH_HUMAN si Gmail/Calendar no
  tienen credenciales).
- 2 Polish (deploy, smoke, telegram final).

Commits: max 14 (setup, backend WS, backend workers, frontend shell, 1-12 widgets,
deploy). En la práctica se agruparán en `feat(cockpit): backend WS + health endpoint`,
`feat(cockpit): frontend shell + dark theme`, `feat(cockpit): widgets 1-4 (Tier 1)`,
`feat(cockpit): widgets 5-8 (Tier 2)`, `feat(cockpit): widgets 9-12 (Tier 3)`,
`chore(cockpit): deploy + smoke`.
