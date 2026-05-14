# Spec — Claudio PWA Widgets Ricos (009)

> /speckit-specify · 2026-05-14

## 1. Problema

Las 14 tabs de `tablero/web-claudio/` muestran **1 widget cada una** (22–41 líneas TSX). Angel pide tabs ricas: 3–6 widgets por tab, cards Tailwind con estética del contexto, conectadas al broker WS real del cockpit.

## 2. Restricciones intocables

| Pieza | Estado | Acción |
|-------|--------|--------|
| PTT + voz E2E (007 + 008) | ✓ Funciona | **No tocar** |
| Endpoints `/voz/api/*` | ✓ Funciona | **No tocar** |
| Auth JWT + ContextSwitcher + BottomTabs | ✓ Funciona | **No tocar** |
| Workers existentes (recordatorios, gastos, compras, medicacion, coche, menu_dia, bris, revenue, trabajo) | ✓ Publican | **Reusar canales** |
| `useChannel<T>(name)` hook | ✓ Funciona | Sólo consumir |
| Bug `telegram_enviar` MCP | Conocido | No usar telegram_enviar intermedio |

## 3. Estética obligatoria por contexto

### CASA — cálido editorial
- Fondo: `bg-[#FEFAF4]` (var bg)
- Cards: `rounded-2xl bg-white border border-stone-200 shadow-sm`
- Acentos: `text-amber-700`, `bg-amber-100`, verde `#5A7A2E` para CTAs
- Tipografía: Playfair Display (títulos) + DM Sans (cuerpo)
- Energía: serena, doméstica, ligeramente artesanal

### NOSVERS — granja verde
- Fondo: `bg-[#FEFAF4]` (mismo bg, distinta personalidad)
- Cards: `rounded-2xl bg-white border border-emerald-200/60 shadow-sm`
- Acentos: `text-emerald-700`, `bg-emerald-50`, `bg-lime-50`
- Tipografía: DM Serif Display + DM Sans
- Energía: orgánica, vital, productiva

### TRABAJO — DI Environnement bicromático
- Fondo: `bg-white` puro
- Cards: `di-card` (border-2 black, sin radio, sombra dura opcional)
- Acentos: `bg-[#D62828]` (DI red), `bg-black`, `text-white`
- Tipografía: Inter MAYÚSCULAS con `letter-spacing: -0.04em` (clase `di-title`)
- Energía: industrial, severa, segura

Las clases ya están en `src/styles/index.css` y `themes.css`. Reusar `di-card`, `di-chip`, `di-title`.

## 4. Tabs y widgets (por contexto)

### CASA (5 tabs)

**Hoy.tsx** — 6 widgets:
1. `WidgetSaludo` — hora + saludo según franja + Angel/Vera
2. `WidgetRecordatoriosHoy` (existente, mantener) — recordatorios fecha=hoy
3. `WidgetMenuHoy` — canal `menu_dia`
4. `WidgetMedicacionProxima` — canal `medicacion`, próxima toma
5. `WidgetBrisResumen` — canal `bris`, último paseo + próxima vacuna
6. `WidgetGastosMesMini` — canal `gastos`, total + barra progreso vs presupuesto

**Listas.tsx** — 2 widgets:
1. `WidgetListaCompras` — canal `compras`, checkboxes grandes, urgente destacado
2. `WidgetQuickAdd` — input inline con submit POST (no modal)

**Gastar.tsx** — 4 widgets:
1. `WidgetNumpad` (existente reorganizado en componente)
2. `WidgetUltimosGastos` — canal `gastos`, últimos 5 apuntes
3. `WidgetCategoriaMasUsada` — categoría top del mes, chip que pre-selecciona
4. `WidgetGastosPorCategoria` (existente reorganizado)

**Recordar.tsx** — 3 widgets:
1. `WidgetProximosRecordatorios` — timeline con fechas relativas (mañana, en 3 días…)
2. `WidgetStatsRecordatorios` — total semana / total
3. `WidgetQuickAddRecordatorio` — input inline

**Casa.tsx** — 4 widgets:
1. `WidgetCocheEstado` — canal `coche`, ITV countdown, km, próximo mantenimiento
2. `WidgetRecurrentesMes` — próximos cargos (mock al inicio)
3. `WidgetDocumentosRecientes` — mock o vault `documentos/`
4. `WidgetSesion` — quién + cerrar sesión (existente)

### NOSVERS (5 tabs)

**HoyGranja.tsx** — 5 widgets:
1. `WidgetIngresosMes` — canal `revenue`, mes actual + delta (existente refinado)
2. `WidgetHuertoEstado` — canal `huerto_estado` (nuevo worker)
3. `WidgetPedidosStripe` — canal `pedidos_stripe` (nuevo worker, derivado de Stripe API)
4. `WidgetAAPPMAStatus` — canal `aappma_stock` (nuevo worker)
5. `WidgetClimaNeuvic` — canal `clima_neuvic` (nuevo worker)

**Huerto.tsx** — 3 widgets:
1. `WidgetCultivosActivos` — canal `huerto_estado`, lista cultivos
2. `WidgetCalendarioSiembra` — qué toca este mes (mock estacional)
3. `WidgetCompostStatus` — canal `huerto_estado` field `compost`

**Tienda.tsx** — 3 widgets:
1. `WidgetVentasMes` — canal `revenue`, total + n pedidos
2. `WidgetClubSolVivantSuscriptores` — canal `pedidos_stripe` field `club_subs`
3. `WidgetUltimoPedido` — canal `pedidos_stripe` field `ultimo`

**AAPPMA.tsx** — 3 widgets:
1. `WidgetContactosAAPPMA` — Thierry Le Cleach + secretario (mock data del CLAUDE.md)
2. `WidgetStockLombrices` — canal `aappma_stock`
3. `WidgetPedidoActivo` — canal `aappma_stock` field `pedido_activo`

**CockpitMini.tsx** — 3 widgets:
1. `WidgetServiciosVPS` — canal `health` (existente)
2. `WidgetAgentesEstado` — canal `agentes` (existente)
3. `WidgetNeuralGraphMini` — reusar `NeuralGraph` 200×200

### TRABAJO (4 tabs)

**Aujourdhui.tsx** — 4 widgets:
1. `WidgetChantierUrgente` — canal `chantiers_activos` (nuevo), filtra urgente
2. `WidgetAgendaHoy` — canal `chantiers_agenda` (nuevo), eventos del día
3. `WidgetEstadisticasRapidas` — canal `chantiers_activos`, grid 2×1
4. `WidgetChipsServicios` — chips estáticos (4 servicios DI)

**Chantiers.tsx** — 1 widget complejo:
1. `WidgetListaChantiers` — canal `chantiers_activos`, cards con header status

**Equipe.tsx** — 1 widget:
1. `WidgetListaOperateurs` — canal `equipe` (nuevo worker), avatar inicial + chip estado

**Docs.tsx** — 1 widget:
1. `WidgetDocsPorChantier` — canal `documentos_trabajo` (nuevo), agrupado por tipo

## 5. Componentes reutilizables

Crear `src/components/widgets/`:
- `Card.tsx` — wrapper auto-estilo por contexto (lee `<html data-context>`)
- `Stat.tsx` — número grande + label, variante mini/full
- `ListItem.tsx` — fila icono + texto + meta + chevron opcional
- `EmptyState.tsx` — placeholder cuando WS no tiene datos
- `Sparkbar.tsx` — barra progreso simple horizontal
- `index.ts` — barrel export

## 6. Workers nuevos (`tablero/v2/workers/`)

| Worker | Canal WS | Intervalo | Fuente |
|--------|----------|-----------|--------|
| `huerto_estado.py` | `huerto_estado` | 300s | vault `nosvers/huerto/` + mock |
| `pedidos_stripe.py` | `pedidos_stripe` | 120s | vault `nosvers/ventas/` + mock |
| `aappma_stock.py` | `aappma_stock` | 600s | vault `nosvers/aappma/stock.md` + mock |
| `clima_neuvic.py` | `clima_neuvic` | 1800s | open-meteo API (gratis, no key) o mock |
| `chantiers_activos.py` | `chantiers_activos` | 60s | reusar `agt_trabajo` o vault `trabajo/chantiers/` |
| `chantiers_agenda.py` | `chantiers_agenda` | 60s | vault `trabajo/chantiers/*/journal.md` |
| `equipe_status.py` | `equipe` | 60s | vault `trabajo/equipe/` |
| `documentos_trabajo.py` | `documentos_trabajo` | 300s | vault `trabajo/chantiers/*/docs/` |

Registrar todos en `workers/__init__.py::register_all`.

## 7. Mock data

Si `vault path` no existe, los workers nuevos publican mock realista basado en CLAUDE.md (ej. Bris, Dordogne, lombrices Dendrobaena, chantier "Bordeaux Nord", operadores DI). NO `empty: true`. La app debe verse poblada para validar UX.

## 8. Definition of Done

- [x] 14 tabs cada una con 3–6 widgets visibles
- [x] CASA usa amber/stone, NOSVERS emerald/lime, TRABAJO rojo DI + blanco + negro + MAYÚSCULAS
- [x] 8 workers WS nuevos publicando snapshots (reales o mock)
- [x] Frontend `vite build` produce bundle gzip < 200 KB
- [x] Tests: smoke render de cada shell (CasaShell, NosVersShell, TrabajoShell) sin crash
- [x] Commit + push
- [x] `dev_server` reiniciado, https://claudio.72.61.160.108.nip.io/ HTTP 200

## 9. Fuera de alcance

- Cambios en la voz/PTT/tools
- Persistencia de checkboxes lista compras (sólo lectura WS)
- Acciones admin (alta chantier, alta operador) — sólo lectura
- Animaciones complejas más allá de transiciones tailwind básicas

## 10. Riesgos

| Riesgo | Mitigación |
|--------|------------|
| Bundle > 200 KB | No añadir libs. Reusar lucide-react ya presente |
| Canal WS no publica → tab vacía | EmptyState + mock data en workers nuevos |
| Romper PTT por refactor de shells | NO tocar PTTOverlay, NO tocar shells: añadir tabs sin modificar BottomTabs/Switcher |
| TypeScript types descuadrados | Añadir tipos nuevos en `api-types.ts` antes de consumir |

## 11. Clarify

No se requiere `/speckit-clarify`. El BRIEF.md de Angel especifica widgets, estética y canales con suficiente detalle. Decisiones tácticas (mock vs vault, ordenación widgets) las toma el ejecutor.
