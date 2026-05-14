# Tasks — Claudio PWA NosVers Completo (010)

> /speckit-tasks · 2026-05-14

## Grupo A · Backend workers WS

- [ ] A1 — `tablero/v2/workers/briefing_africa.py` — vault `agentes/agt05_africa/_resultado.md` o mock
- [ ] A2 — `tablero/v2/workers/proxima_publicacion.py` — vault `agentes/agt02_instagram/_aprobados.md` o mock
- [ ] A3 — `tablero/v2/workers/vermicultura.py` — Dendrobaena stock + AAPPMA + Thierry
- [ ] A4 — `tablero/v2/workers/composteur.py` — agt_composteur status o mock
- [ ] A5 — `tablero/v2/workers/tareas_dia.py` — tareas día granja
- [ ] A6 — `tablero/v2/workers/eisenia_run.py` — vault `agentes/agt_eisenia/_resultado.md` o mock
- [ ] A7 — `tablero/v2/workers/web_traffic.py` — mock realista 30 días
- [ ] A8 — `tablero/v2/workers/search_console.py` — mock impresiones/clicks/queries
- [ ] A9 — `tablero/v2/workers/ahrefs.py` — mock DR/backlinks/domains
- [ ] A10 — `tablero/v2/workers/engagement_redes.py` — IG/YT/FB últimos 7 días
- [ ] A11 — `tablero/v2/workers/comentarios_wp.py` — WP REST `/comments?status=hold` o mock
- [ ] A12 — `tablero/v2/workers/telegram_resumen.py` — últimos N mensajes
- [ ] A13 — `tablero/v2/workers/logs_errores.py` — grep `/home/nosvers/logs/*.log`
- [ ] A14 — Registrar 13 workers en `tablero/v2/workers/__init__.py`

## Grupo B · Canales WS

- [ ] B1 — Añadir 13 canales a `VALID_CHANNELS` en `tablero/v2/ws.py`

## Grupo C · Endpoint agente_ejecutar

- [ ] C1 — `tablero/v2/agente_ejecutar.py` con whitelist 14 agentes
- [ ] C2 — Registrar ruta `POST /tablero/api/v2/agente_ejecutar` en `tablero/rest.py`
- [ ] C3 — Smoke: `curl` POST con un nombre válido → 200 + pid

## Grupo D · Frontend tipos & componentes

- [ ] D1 — Extender `src/lib/api-types.ts` con 13 interfaces
- [ ] D2 — `src/components/nosvers/widgets/BotonEnlaceExterno.tsx`
- [ ] D3 — `src/components/nosvers/widgets/WidgetAgenteCard.tsx`
- [ ] D4 — `src/components/nosvers/widgets/index.ts` barrel

## Grupo E · Tabs

- [ ] E1 — `tabs/Hoy.tsx` (5 widgets)
- [ ] E2 — `tabs/Granja.tsx` (5 widgets)
- [ ] E3 — `tabs/Web.tsx` (5 widgets)
- [ ] E4 — `tabs/Mails.tsx` (3 widgets)
- [ ] E5 — `tabs/Agentes.tsx` (5 widgets)
- [ ] E6 — Borrar `tabs/HoyGranja.tsx`, `Huerto.tsx`, `Tienda.tsx`, `AAPPMA.tsx`, `CockpitMini.tsx`

## Grupo F · Shell

- [ ] F1 — Reescribir `NosVersShell.tsx` con nuevos imports + nuevo TABS

## Grupo G · Build & deploy

- [ ] G1 — `npm run build` desde `tablero/web-claudio/`
- [ ] G2 — Verificar bundle gzip < 250 KB
- [ ] G3 — Restart `dev_server.py` (kill pid actual, relanzar con env)
- [ ] G4 — Smoke `curl -sI https://claudio.72.61.160.108.nip.io` → 200
- [ ] G5 — `git add -A && git commit -m "feat(010-nosvers-completo): ..."`
- [ ] G6 — `git push origin main`

## Smoke tests obligatorios antes de cerrar

- [ ] Cada tab nueva renderiza sin error en consola (manual: abrir DevTools en navegador)
- [ ] Casa y Trabajo siguen funcionando (smoke por curl + DevTools)
- [ ] PTT abre overlay y graba (smoke por DevTools)
- [ ] Botón ▶ en un agente devuelve 200 y `agentes` WS refleja `running` en <5s
- [ ] Enlaces externos (Panel Fotos / WP Admin / Stripe / Gmail labels) abren nueva pestaña
