# Tasks — Claudio PWA Widgets Ricos (009)

> /speckit-tasks · 2026-05-14

## Grupo A · Tipos + librería base

- [ ] A1 — Extender `src/lib/api-types.ts` con: `CocheSnapshot`, `MedicacionSnapshot`, `MenuHoySnapshot`, `BrisSnapshot`, `ComprasSnapshot`, `HuertoSnapshot`, `PedidosStripeSnapshot`, `AappmaStockSnapshot`, `ClimaSnapshot`, `ChantierItem`, `ChantiersActivosSnapshot`, `ChantiersAgendaSnapshot`, `EquipeSnapshot`, `DocumentosTrabajoSnapshot`
- [ ] A2 — `src/components/widgets/Card.tsx` con prop `variant?: 'casa'|'nosvers'|'trabajo'|'auto'`
- [ ] A3 — `src/components/widgets/Stat.tsx` props `label`, `value`, `sub?`, `accent?`
- [ ] A4 — `src/components/widgets/ListItem.tsx` props `icon?`, `title`, `meta?`, `onClick?`
- [ ] A5 — `src/components/widgets/EmptyState.tsx` props `icon?`, `text`
- [ ] A6 — `src/components/widgets/Sparkbar.tsx` props `value`, `max`, `accent?`
- [ ] A7 — `src/components/widgets/index.ts` barrel export

## Grupo B · Workers backend

- [ ] B1 — `huerto_estado.py` — cultivos activos + último riego + compost status (vault `nosvers/huerto/` o mock)
- [ ] B2 — `pedidos_stripe.py` — total mes + n pedidos + último + club_subs (vault `nosvers/ventas/` o mock)
- [ ] B3 — `aappma_stock.py` — stock Dendrobaena + pedido activo + contactos (vault `nosvers/aappma/` o mock)
- [ ] B4 — `clima_neuvic.py` — open-meteo Neuvic (45.10, 0.46) o mock
- [ ] B5 — `chantiers_activos.py` — leer `trabajo/chantiers/*/INDEX.md` o mock (3 chantiers)
- [ ] B6 — `chantiers_agenda.py` — eventos del día desde journals o mock
- [ ] B7 — `equipe_status.py` — leer `trabajo/equipe/*.md` o mock (3 operateurs)
- [ ] B8 — `documentos_trabajo.py` — listar docs por tipo o mock
- [ ] B9 — Registrar 8 workers en `tablero/v2/workers/__init__.py`

## Grupo C · Tabs CASA

- [ ] C1 — `Hoy.tsx` — 6 widgets (Saludo, RecordatoriosHoy, MenuHoy, MedicacionProxima, BrisResumen, GastosMesMini)
- [ ] C2 — `Listas.tsx` — Lista con checkboxes + QuickAdd
- [ ] C3 — `Gastar.tsx` — Numpad + UltimosGastos + CategoriaMasUsada + PorCategoria
- [ ] C4 — `Recordar.tsx` — ProximosRecordatorios + Stats + QuickAdd
- [ ] C5 — `Casa.tsx` — CocheEstado + RecurrentesMes + DocumentosRecientes + Sesion

## Grupo D · Tabs NOSVERS

- [ ] D1 — `HoyGranja.tsx` — IngresosMes + HuertoEstado + PedidosStripe + AAPPMAStatus + ClimaNeuvic
- [ ] D2 — `Huerto.tsx` — CultivosActivos + CalendarioSiembra + CompostStatus
- [ ] D3 — `Tienda.tsx` — VentasMes + ClubSolVivantSuscriptores + UltimoPedido
- [ ] D4 — `AAPPMA.tsx` — ContactosAAPPMA + StockLombrices + PedidoActivo
- [ ] D5 — `CockpitMini.tsx` — ServiciosVPS + AgentesEstado + NeuralGraphMini

## Grupo E · Tabs TRABAJO

- [ ] E1 — `Aujourdhui.tsx` — ChantierUrgente + AgendaHoy + EstadisticasRapidas + ChipsServicios
- [ ] E2 — `Chantiers.tsx` — ListaChantiers (cards estado URGENT/EN COURS/DÉBUT)
- [ ] E3 — `Equipe.tsx` — ListaOperateurs (avatar inicial + chip ACTIF/FORM)
- [ ] E4 — `Docs.tsx` — DocsPorChantier agrupado (PPSPS, plan retrait, devis, certificats, diag amiante)

## Grupo F · Tests + Deploy

- [ ] F1 — `src/tests/shells.test.tsx` — smoke render para CasaShell, NosVersShell, TrabajoShell
- [ ] F2 — Verificar `npm run test` verde
- [ ] F3 — `npm run build` y verificar bundle < 200 KB gzip
- [ ] F4 — Verificar `python -c "from tablero.v2.workers import register_all; register_all()"`
- [ ] F5 — Commit + push
- [ ] F6 — Reiniciar dev_server + `curl -I https://claudio.72.61.160.108.nip.io/` HTTP 200
