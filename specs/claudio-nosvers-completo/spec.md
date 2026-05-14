# Spec — Claudio PWA NosVers Completo (010)

> /speckit-specify · 2026-05-14

## 1. Problema

El contexto NosVers de la PWA Claudio (`tablero/web-claudio/`) muestra 5 tabs heredadas de la app granja vieja: HoyGranja, Huerto, Tienda, AAPPMA, CockpitMini. Tras 009 estas tabs ya tienen widgets reales, pero **no cubren toda la operativa NosVers**: faltan acceso a agentes, mails, panel fotos, tráfico web, comentarios WP, AEGIS y agt_eisenia. Angel pide consolidar en NosVers **toda la operación de la ferme** ("one for all") porque África también lo usará y necesita un sólo punto de entrada.

## 2. Restricciones intocables

| Pieza | Estado | Acción |
|-------|--------|--------|
| Contextos Casa y Trabajo (007) | ✓ Funciona | **No tocar** |
| PTT + voz E2E (007 + 008) | ✓ Funciona | **No tocar** |
| Endpoints `/voz/api/*` | ✓ Funciona | **No tocar** |
| Workers existentes (huerto_estado, pedidos_stripe, agentes, clima_neuvic, aegis, revenue, recordatorios) | ✓ Publican | **Reusar canales** |
| `useChannel<T>(name)` hook | ✓ Funciona | Sólo consumir |
| Endpoint existente `/tablero/api/v2/agentes/ejecutar` | ✓ Bloqueante (espera resultado) | Conservar; añadir endpoint **nuevo** no-bloqueante |
| Bug `telegram_enviar` MCP | Conocido | No usar telegram_enviar intermedio |
| Bundle final | < 250 KB gzip | Reusar librería widgets/, lazy donde aplique |

## 3. Estructura nueva contexto NosVers — 5 tabs

REEMPLAZAR las 5 tabs actuales por:

### Tab 1 — Hoy
- **WidgetBriefingAfrica** — última run de agt05_africa (vault `agentes/agt05_africa/_resultado.md`)
- **WidgetPedidosHoy** — pedidos del día (canal `pedidos_stripe` existente, sección "hoy")
- **WidgetProximaPublicacion** — qué tiene agt02_instagram en cola (vault `agentes/agt02_instagram/_aprobados.md`)
- **WidgetRecordatoriosNosVers** — items canal `recordatorios` filtrados por etiqueta=nosvers
- **WidgetVentasMes** — MRR + total mes (canal `pedidos_stripe` + `revenue`)

### Tab 2 — Granja
- **WidgetHuertoActivo** — canal `huerto_estado` (cultivos, riegos, cosechas)
- **WidgetVermicultura** — Dendrobaena stock + AAPPMA pedidos + Thierry contact (canal nuevo `vermicultura`, reusa parcialmente `aappma_stock`)
- **WidgetComposteur** — agt_composteur status (canal nuevo `composteur`)
- **WidgetTareasDia** — qué hacer hoy (canal nuevo `tareas_dia` desde vault `nosvers/tareas/` o `granja/tareas/`)
- **WidgetEiseniaUltimaRun** — agt_eisenia output reciente (canal nuevo `eisenia_run`)

### Tab 3 — Web
- **WidgetVisitasNosVers** — chart 30 días (canal nuevo `web_traffic`, mock realista)
- **WidgetSearchConsole** — impresiones / clicks / queries top (canal nuevo `search_console`, mock)
- **WidgetAhrefs** — DR / backlinks / domains (canal nuevo `ahrefs`, mock)
- **WidgetEngagementRedes** — IG/YT/FB last 7 days (canal nuevo `engagement_redes`)
- **WidgetEnlacesExternos** — 3 botones externos: Panel Fotos, WP Admin, Stripe Dashboard

### Tab 4 — Mails
- **WidgetGmailEnlaces** — 4 botones por label (NosVers/Infraestructura, NosVers/SEO, NosVers/Facturas, Lectura/Tech) → `mail.google.com/mail/u/0/#label/...`
- **WidgetTelegramResumen** — últimos N mensajes (canal nuevo `telegram_resumen`)
- **WidgetComentariosWP** — comentarios pendientes moderar (canal nuevo `comentarios_wp` via WP REST `/comments?status=hold`)

### Tab 5 — Agentes
- **WidgetListaAgentes** — 14 agentes con avatar + nombre + estado + última run + botón `▶ Ejecutar`
  Lista canónica: `orchestrator, agt01_visual, agt02_instagram, agt04_seo, agt05_africa, agt06_infoproduct, agt07_diario, agt07_youtube, agt08_facebook, agt00_intelligence, agt_infra, agt_eisenia, agt_analyste, agt_directeur`
- **WidgetAEGISAlerts** — últimas alertas seguridad (canal `aegis` existente)
- **WidgetServiciosVPS** — Caddy/MCP/dev_server/agents-runner estado (canal `health` existente)
- **WidgetNeuralGraphMini** — componente existente NeuralGraph en 200×200
- **WidgetLogsErrores** — errores últimas 24h agrupados por agente (canal nuevo `logs_errores`)

## 4. Backend — workers WS nuevos

13 nuevos workers en `tablero/v2/workers/`. Convención idéntica a 009: función `<name>_tick()` async, devuelve `dict | None`, registrada en `__init__.py`.

| Worker | Canal | Intervalo | Fuente |
|--------|-------|-----------|--------|
| briefing_africa.py | `briefing_africa` | 600s | vault `agentes/agt05_africa/_resultado.md` |
| proxima_publicacion.py | `proxima_publicacion` | 300s | vault `agentes/agt02_instagram/_aprobados.md` |
| vermicultura.py | `vermicultura` | 600s | vault `nosvers/vermicultura/` o reusa `aappma_stock` |
| composteur.py | `composteur` | 600s | vault `agentes/agt_composteur/_resultado.md` o mock |
| tareas_dia.py | `tareas_dia` | 600s | vault `nosvers/tareas/YYYY-MM-DD.md` o mock |
| eisenia_run.py | `eisenia_run` | 600s | vault `agentes/agt_eisenia/_resultado.md` |
| web_traffic.py | `web_traffic` | 1800s | mock realista (30 días series) |
| search_console.py | `search_console` | 3600s | mock realista (top queries + KPIs) |
| ahrefs.py | `ahrefs` | 3600s | mock realista (DR, backlinks, domains) |
| engagement_redes.py | `engagement_redes` | 1800s | logs agt02/agt07_youtube/agt08 o mock |
| comentarios_wp.py | `comentarios_wp` | 600s | WP REST `/comments?status=hold` o mock |
| telegram_resumen.py | `telegram_resumen` | 300s | DB bot o vault `claudio/telegram/` o mock |
| logs_errores.py | `logs_errores` | 300s | grep `/home/nosvers/logs/*.log` últimos errores |

Reusados (sin cambios): `huerto_estado`, `pedidos_stripe`, `agentes`, `aegis`, `health`, `revenue`, `recordatorios`, `clima_neuvic`.

Todos los nuevos canales se añaden a `VALID_CHANNELS` en `tablero/v2/ws.py`. Ninguno requiere scope JWT (NosVers es contexto base).

## 5. Backend — endpoint nuevo

`POST /tablero/api/v2/agente_ejecutar`

- **Body**: `{"nombre": "agt05_africa"}` (`nombre`, no `slug`, según BRIEF).
- **Auth**: JWT Bearer obligatorio (mismo flujo que el resto).
- **Whitelist**: los 14 nombres de la spec §3 tab 5.
- **Implementación**: `subprocess.Popen` **no-bloqueante** (fire-and-forget). Devuelve inmediatamente `{"ok": true, "nombre": "...", "pid": 1234, "started_at": "ISO8601"}`. NO espera al subprocess; el cliente refresca el estado vía canal `agentes` WS.
- **Diferencia con endpoint existente**: el endpoint `/tablero/api/v2/agentes/ejecutar` (US11) es bloqueante y solo expone 4 slugs. El nuevo es fire-and-forget y expone los 14 agentes operativos.
- **stdout/stderr**: redirigidos a `/home/nosvers/logs/<nombre>.log` (append). Esto permite al worker `agentes_tick` detectar `running` por mtime.
- **Error codes**: `auth_invalido` 401 · `nombre_invalido` 400 · `not_in_whitelist` 404 · `script_missing` 500.

## 6. Frontend — componentes nuevos

```
src/components/nosvers/widgets/
  ├── BotonEnlaceExterno.tsx
  ├── WidgetAgenteCard.tsx       # avatar + nombre + estado + última run + botón ▶
  └── (los widgets de Tab1–Tab5 viven dentro de cada tab .tsx)
```

`api-types.ts` se extiende con: `BriefingAfricaSnapshot`, `ProximaPublicacionSnapshot`, `VermiculturaSnapshot`, `ComposteurSnapshot`, `TareasDiaSnapshot`, `EiseniaRunSnapshot`, `WebTrafficSnapshot`, `SearchConsoleSnapshot`, `AhrefsSnapshot`, `EngagementRedesSnapshot`, `ComentariosWpSnapshot`, `TelegramResumenSnapshot`, `LogsErroresSnapshot`.

Tabs nuevas:
```
src/components/nosvers/tabs/
  ├── Hoy.tsx       (nuevo — reemplaza HoyGranja.tsx)
  ├── Granja.tsx    (nuevo — reemplaza Huerto.tsx)
  ├── Web.tsx       (nuevo — reemplaza Tienda.tsx)
  ├── Mails.tsx     (nuevo — reemplaza AAPPMA.tsx)
  └── Agentes.tsx   (nuevo — reemplaza CockpitMini.tsx)
```

`NosVersShell.tsx` actualizado: nuevo `TABS` array y switch.

## 7. Definition of Done

1. Las 5 tabs nuevas renderizan sin crash en local y prod.
2. Botones enlace externo abren `target="_blank" rel="noopener"`.
3. Los 14 agentes listados con avatar/estado/última run. Botón ▶ dispara el endpoint nuevo y refresca el estado en <5s vía canal `agentes`.
4. Los 13 workers nuevos publican snapshot ≥1 vez tras arrancar el server.
5. Casa y Trabajo siguen intactos (smoke).
6. PTT/voz sigue funcionando (smoke).
7. `npm run build` OK, bundle JS principal gzip < 250 KB.
8. HTTP 200 en `https://claudio.72.61.160.108.nip.io`.
9. Commit + push a `main`. Notas de commit: prefijo `feat(010-nosvers-completo):`.

## 8. Out of scope

- OAuth Gmail real (solo enlaces deep-link a labels).
- Integración Stripe API real (mock + canal existente).
- Integración Plausible / Ahrefs / Search Console reales (mocks coherentes).
- Componente Panel Fotos in-app (solo botón externo a `https://nosvers.com/panel-fotos/`).
- WP REST API real para comentarios (mock realista; quedará TODO en el código).
