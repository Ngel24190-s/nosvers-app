# BRIEF — Claudio PWA Widgets Ricos (Proyecto 009)

Las 14 tabs de la PWA `web-claudio/` ahora tienen 1 widget cada una (22-41 líneas). El usuario (Angel) pide "one for all" — necesita las tabs **ricas**, con 3-6 widgets cada una al estilo de los mockups, conectadas a datos reales del broker WS del cockpit.

## Por qué AHORA

Pre-requisitos cumplidos:
- 007 PWA Contextos ✓ (estructura, JWT, tabs, BottomTabs)
- 008 voz conversacional ✓ (claudio_conversar + Piper TTS funcionan E2E)
- Broker WS Fase 3 ✓ con canales: recordatorios, gastos_mes, lista_compras, medicacion, coche_status, menu_hoy, bris

## Objetivo

Poblar cada tab con **3-6 widgets independientes** (cards de Tailwind) que muestren información real del broker WS. Mantener la estética del contexto (Casa cálido amber/stone, NosVers emerald/lime, Trabajo bicromático rojo DI #D62828 + blanco + negro + sans MAYÚSCULAS).

## Tabs y widgets esperados

### Contexto CASA (5 tabs)

**Hoy.tsx** — actualmente solo recordatorios. Añadir:
- WidgetSaludo (hora + nombre + clima si disponible)
- WidgetRecordatoriosHoy (que ya está, mantener)
- WidgetMenuHoy (canal `menu_hoy`)
- WidgetMedicacionProxima (canal `medicacion`)
- WidgetBrisResumen (último paseo, próxima vacuna)
- WidgetGastosMesMini (canal `gastos_mes`, total + barra progreso)

**Listas.tsx** — actualmente compras básico. Mantener pero mejorar:
- WidgetListaCompras con checkboxes grandes, marca de urgente
- Botón "+ Añadir" abre input quick-add (no modal)

**Gastar.tsx** — actualmente numpad. Mantener + añadir:
- WidgetUltimosGastos (5 últimos del mes)
- WidgetCategoriaMasUsada (chip que pre-selecciona)

**Recordar.tsx** — actualmente input. Añadir:
- WidgetProximosRecordatorios (lista timeline con fechas relativas)

**Casa.tsx** — actualmente vacía o muy básica. Añadir:
- WidgetCocheEstado (canal `coche_status`: ITV countdown, km, próximo mantenimiento)
- WidgetRecurrentesMes (próximos cargos: internet, seguro, etc.)
- WidgetDocumentosRecientes

### Contexto NOSVERS (5 tabs)

**HoyGranja.tsx** — añadir:
- WidgetHuertoEstado (cultivos activos, ultimos riegos)
- WidgetPedidosPendientes (Stripe: cuántas órdenes hoy)
- WidgetAAPPMAStatus (lombrices Dendrobaena: stock, próxima entrega)
- WidgetClimaNeuvic (si hay API tiempo)
- WidgetIngresosMes

**Huerto.tsx** — añadir:
- WidgetCultivosActivos (lista con próximas tareas)
- WidgetCalendarioSiembra (qué toca plantar este mes)
- WidgetCompostStatus

**Tienda.tsx** — añadir:
- WidgetVentasMes (Stripe MRR + total)
- WidgetClubSolVivantSuscriptores
- WidgetUltimoPedido

**AAPPMA.tsx** — añadir:
- WidgetContactosAAPPMA (Thierry Le Cleach + secretario, con click-to-call)
- WidgetStockLombrices (Dendrobaena disponibles)
- WidgetPedidoActivo

**CockpitMini.tsx** — añadir:
- WidgetServiciosVPS (nosvers-mcp, caddy, dev_server, agentes runner)
- WidgetAgentesEstado (mini: visual, instagram, seo, etc.)
- WidgetNeuralGraphMini (reusar componente existente, 200x200)

### Contexto TRABAJO (4 tabs, estilo DI rojo+blanco+negro)

**Aujourdhui.tsx** — añadir:
- WidgetChantierUrgente (border-2 border-black, header bg-[#D62828])
- WidgetAgendaHoy (con badges hora rojas DI)
- WidgetEstadisticasRapidas (chantiers actifs / total équipe — grid 2x1 bicromático)
- WidgetChipsServicios (DÉSAMIANTAGE, DÉPLOMBAGE, etc. negros con texto blanco)

**Chantiers.tsx** — añadir:
- WidgetListaChantiers (cards con header status URGENT/EN COURS/DÉBUT en colores)
- Cada card muestra: nombre, dirección, équipe, días, devis €

**Equipe.tsx** — añadir:
- WidgetListaOperateurs (avatar inicial negro + nombre MAYÚSCULAS + badge ACTIF/FORM)

**Docs.tsx** — añadir:
- WidgetDocsPorChantier (agrupado: PPSPS, plan retrait, devis, certificats, diag amiante)

## Arquitectura técnica

### Componentes reutilizables

Crear `src/components/widgets/` con componentes base:
- `<Card>` — wrapper con estética por contexto (border, bg, padding)
- `<Stat>` — número grande + label
- `<ListItem>` — fila con icono + texto + chevron
- `<EmptyState>` — placeholder cuando WS no tiene datos

Componentes por contexto: estos detectan el contexto activo y aplican estética automática. Casa: rounded-2xl bg-white shadow-sm border-stone-200. NosVers: rounded-2xl bg-white shadow-sm border-emerald-200/60. Trabajo: rounded-xl bg-white border-2 border-black.

### Canales WS existentes y nuevos

REUSAR los canales que ya publican los workers de Fase 3:
- `recordatorios`, `gastos_mes`, `lista_compras`, `medicacion`, `coche_status`, `menu_hoy`, `bris`

AÑADIR (Fase 9, workers nuevos en `tablero/v2/workers/`):
- `huerto_estado`, `pedidos_stripe`, `aappma_stock`, `clima_neuvic`
- `chantiers_activos`, `chantiers_agenda`, `equipe`, `documentos_trabajo`

Cada worker es un asyncio task que cada 30-60s lee del vault o API y publica al broker WS.

### Datos demo

Si los workers nuevos no tienen datos reales todavía, deben publicar mock data realista (basado en `userMemories`) en lugar de empty state. La app debe verse poblada para validar UX.

## Constraints

- No tocar PTT ni el flow voz (Pieza 1 funciona, no romper)
- No tocar los endpoints /voz/api/* (también funcionan)
- Reusar canales WS existentes donde posible
- Workers nuevos deben fallar gracefully si vault path no existe
- Estética CASA/NOSVERS/TRABAJO diferenciada estrictamente
- Bundle final < 200 KB gzip
- Tests: smoke E2E de cada contexto (renderiza sin crash, recibe snapshot WS)
- Bug telegram_enviar conocido: NO usar telegram_enviar intermedio

## Spec Kit

1. /speckit-specify
2. /speckit-clarify (solo si crítico)
3. /speckit-plan — base widgets/, workers nuevos, mock data
4. /speckit-tasks — agrupado por: widgets base, tab Hoy casa, tab Casa, tab Listas, etc.
5. /speckit-implement — sin parar

## Definition of Done

- 14 tabs cada una con 3-6 widgets visibles
- Tabs CASA usan amber/stone/emerald
- Tabs NOSVERS usan emerald/lime
- Tabs TRABAJO usan rojo DI #D62828 + blanco + negro + sans condensada MAYÚSCULAS
- 8+ workers WS nuevos publicando snapshots (reales o mock)
- Frontend bundle rebuild < 200 KB gzip
- Tests pasando
- Commit + push
- App probada externamente en https://claudio.72.61.160.108.nip.io/ (HTTP 200)

## Estimación

Humano: 2 semanas. Claude Code: 5-7h.

---
*BRIEF preparado por Claude Opus 4.7 móvil 2026-05-14 ~19:15 UTC*
