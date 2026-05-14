# BRIEF — Claudio PWA NosVers Completo (Proyecto 010)

Angel pide que el contexto NosVers de la PWA sea la **app granja COMPLETA**
(todo lo de /granja + agentes + huerto + vermicultura) + acceso a fotos/mails/
analytics web. "One for all", facilita uso para Angel y África.

## Estado previo

- 007 PWA Contextos ✓ (3 contextos isolated)
- 008 Voz conversacional ✓ (Claudio conversa por voz)
- 009 Widgets ricos Fase 1 ✓ (`3539f97` — base de widgets + workers WS)
- Contexto NosVers actual: 5 tabs (HoyGranja, Huerto, Tienda, AAPPMA, CockpitMini)
  con widgets básicos pero NO incluye agentes, mails, panel fotos ni tráfico web.

## Decisión Angel 2026-05-14

- **Panel Fotos**: ya existe en `https://nosvers.com/panel-fotos/` (WP page 802).
  En la PWA solo enlazamos con botón "Abrir Panel Fotos" — NO duplicamos.
- **Mails**: solo Gmail NosVers (no Trabajo todavía). Botón "Abrir Gmail
  filtrado" por label hasta que se reconecte OAuth Gmail connector.
- **Vermicultura** (Dendrobaena para AAPPMA) va en Granja, no en una tab aparte.

## Estructura nueva contexto NosVers

REEMPLAZAR las 5 tabs actuales (HoyGranja, Huerto, Tienda, AAPPMA, CockpitMini)
por estas 5 nuevas:

### Tab 1: Hoy
Widgets:
- WidgetBriefingAfrica — lee última run de agt05_africa briefing del vault
- WidgetPedidosHoy — Stripe pedidos del día
- WidgetProximaPublicacion — qué tiene agt02_instagram en cola
- WidgetRecordatoriosNosVers — recordatorios con etiqueta nosvers
- WidgetVentasMes — Stripe MRR + total mes

### Tab 2: Granja
Widgets:
- WidgetHuertoActivo — cultivos en marcha, próximos riegos, cosechas
- WidgetVermicultura — Dendrobaena stock, AAPPMA pedidos pendientes,
  Thierry contact card
- WidgetComposteur — agt_composteur status (si activado)
- WidgetTareasDia — qué hay que hacer hoy (regar, plantar, cosechar)
- WidgetEiseniaUltimaRun — agt_eisenia output reciente

### Tab 3: Web
Widgets:
- WidgetVisitasNosVers — chart 30 días (datos vault o mock realista)
- WidgetSearchConsole — impresiones / clicks / queries top
- WidgetAhrefs — DR / backlinks / domains
- WidgetEngagementRedes — IG/YT/FB last 7 days (de los logs de los agentes)
- WidgetEnlacesExternos:
  * "Abrir Panel Fotos" → https://nosvers.com/panel-fotos/
  * "WP Admin" → https://nosvers.com/wp-admin/
  * "Stripe Dashboard" → https://dashboard.stripe.com/

### Tab 4: Mails
Widgets:
- WidgetGmailEnlaces — botones por label:
  * NosVers/Infraestructura → https://mail.google.com/mail/u/0/#label/NosVers%2FInfraestructura
  * NosVers/SEO → https://mail.google.com/mail/u/0/#label/NosVers%2FSEO
  * NosVers/Facturas → ditto
  * Lectura/Tech → ditto
- WidgetTelegramResumen — últimos N mensajes de Angel
- WidgetComentariosWP — comentarios pendientes moderar (via WP REST API)

### Tab 5: Agentes
Widgets:
- WidgetListaAgentes — 14 agentes con avatar + nombre + estado + última run
  * orchestrator, agt01_visual, agt02_instagram, agt04_seo, agt05_africa,
    agt06_infoproduct, agt07_diario, agt07_youtube, agt08_facebook,
    agt00_intelligence, agt_infra, agt_eisenia, agt_analyste, agt_directeur
  * Botón "▶ Ejecutar" por agente (POST /tablero/api/v2/agente_ejecutar)
- WidgetAEGISAlerts — últimas alertas seguridad
- WidgetServiciosVPS — Caddy/MCP/dev_server/agents-runner estado
- WidgetNeuralGraphMini — reusar el componente (200x200)
- WidgetLogsErrores — últimos errores agrupados por agente

## Backend cambios

### Workers WS nuevos en tablero/v2/workers/

- `briefing_africa.py` — lee `agentes/agt05_africa/_resultado.md` cada 30min
- `pedidos_stripe.py` — query Stripe API (key en .env) cada 5min, devuelve hoy/mes
- `proxima_publicacion.py` — lee `agentes/agt02_instagram/_aprobados.md`
- `huerto_estado.py` — lee `huerto/INDEX.md` y `huerto/cultivos/*.md`
- `vermicultura.py` — lee `granja/vermicultura/` + AAPPMA pedidos
- `tareas_dia.py` — calendario de tareas granja del día (lee `granja/tareas/`)
- `eisenia_run.py` — lee `agentes/agt_eisenia/_resultado.md`
- `web_traffic.py` — mock o Plausible API si configurado
- `search_console.py` — mock o Google Search Console API
- `ahrefs.py` — mock o Ahrefs API si configurado
- `agentes_estado.py` — lee logs de los 14 agentes, devuelve estado + última run
- `comentarios_wp.py` — WP REST API `/comments?status=hold`
- `telegram_resumen.py` — últimos mensajes de bot DB

Si datos reales no disponibles → mock realista basado en userMemories.

### Endpoint nuevo
- `POST /tablero/api/v2/agente_ejecutar`
  Body: `{nombre: "agt05_africa"}`
  Whitelist: solo los 14 agentes conocidos.
  Implementación: subprocess.Popen de `agents/<nombre>.py`.

## Frontend cambios

### Componentes nuevos
- `BotonEnlaceExterno` — wrapper para abrir URLs externas con icono
- `WidgetAgente` — card de un agente con avatar, estado, última run, botón ▶
- Resto: widgets nuevos por cada bloque

### Re-estructura nosvers/

- Renombrar carpeta `nosvers/tabs/` para reflejar nuevas tabs
- Actualizar `NosVersShell.tsx` con nuevos imports y bottom nav

## Constraints

- NO romper Casa, Trabajo, ni Hoy del contexto Casa
- NO romper PTT ni voz (ambos están perfectos, no tocar)
- Mantener estética NosVers (emerald/lime + ocres)
- Reusar workers existentes donde sea posible
- Bug telegram_enviar: NO usar telegram_enviar intermedio
- Bundle final < 250 KB gzip
- Test smoke: cada tab renderiza sin crash + recibe snapshot WS

## Spec Kit

1. /speckit-specify
2. /speckit-plan
3. /speckit-tasks
4. /speckit-implement — sin parar

## Definition of Done

- Las 5 tabs nuevas de NosVers visibles y pobladas
- Botones enlace externo abren en nueva pestaña (target="_blank")
- 14 agentes listados con su estado + botón ejecutar funciona
- Workers nuevos publican snapshots (mock o reales)
- Build OK, bundle < 250 KB gzip
- HTTP 200 en claudio.72.61.160.108.nip.io
- Commit + push

## Estimación

Code: 5-7h.

---
*BRIEF preparado por Claude Opus 4.7 móvil 2026-05-14 ~20:00 UTC*
