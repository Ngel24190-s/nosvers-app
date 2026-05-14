# Tasks — Claudio Jarvis · Fase 1 (005)

Marcadores: `[ ]` pending · `[~]` in progress · `[x]` done · `[!]` blocker

---

## Bloque 0 — Vault scaffolding (T010)

- [x] **T011** Crear 11 directorios bajo `public_html/knowledge_base/`:
  `familia/{recordatorios,decisiones,conversaciones}`, `finanzas/{gastos,ingresos}`,
  `salud/{citas,sintomas}`, `documentos/{facturas,contratos,seguros,impuestos}`,
  `casa/reformas`, `coche/{mantenimiento,gastos}`, `viajes/{planificacion,recuerdos}`,
  `lectura/{notas,highlights}`, `compras/historico`, `menus/recetas`,
  `claudio/{memorias/{angel,africa,compartido},conocimiento,logs}`.
- [x] **T012** README.md en cada dominio raíz (11 archivos) — explica contenido + tools.
- [x] **T013** Seed: `finanzas/recurrentes.yaml`, `salud/medicacion.yaml`,
  `casa/electrodomesticos.yaml`, `compras/despensa.yaml`, `coche/INDEX.md`,
  `documentos/INDEX.md`, `familia/cumpleanos.md`, `menus/semana_actual.md`,
  `menus/favoritos.md`, `lectura/cola.md`, `compras/lista_actual.md`,
  `finanzas/presupuesto-mes.md`, `finanzas/alertas.md`.

## Bloque 1 — Claudio identity package (T020)

- [x] **T021** `claudio_tools/__init__.py` con version + re-exports.
- [x] **T022** `claudio_tools/common.py` (helpers).
- [x] **T023** `claudio_tools/identidad.py` (`claudio_recordar`, `claudio_contexto`).
- [x] **T024** `public_html/knowledge_base/claudio/personalidad.md` (5 modos).

## Bloque 2 — Familia + finanzas (T030)

- [x] **T031** `claudio_tools/familia.py`.
- [x] **T032** `claudio_tools/finanzas.py`.

## Bloque 3 — Compras + menús + casa (T040)

- [x] **T041** `claudio_tools/compras.py`.
- [x] **T042** `claudio_tools/menus.py`.
- [x] **T043** `claudio_tools/casa.py`.

## Bloque 4 — Coche + documentos + salud (T050)

- [x] **T051** `claudio_tools/coche.py`.
- [x] **T052** `claudio_tools/documentos.py`.
- [x] **T053** `claudio_tools/salud.py`.

## Bloque 5 — MCP wiring (T060)

- [x] **T061** Sección nueva en `mcp_server.py` con 22 `@mcp.tool()` wrappers
  protegida por `try/except` para no romper MCP si claudio_tools falla.
- [x] **T062** Smoke `python3 -c "import claudio_tools"` desde el venv.

## Bloque 6 — Automatizaciones (T070)

- [x] **T071** `automatizaciones/recordatorio_diario_morning.yaml` (activo:false).
- [x] **T072** `automatizaciones/itv_coche_3_meses.yaml` (activo:false).
- [x] **T073** `automatizaciones/recurrente_alerta_dia_anterior.yaml` (activo:false).

## Bloque 7 — Bot hooks (T080)

- [x] **T081** `bot/bot_v2.py`: imports + `_autor_from_user`.
- [x] **T082** `/gasto` command handler.
- [x] **T083** `/compra` command handler.
- [x] **T084** `/recordar` command handler.

## Bloque 8 — Tests + commits + restart (T090)

- [x] **T091** `tests/test_claudio_tools.py` con fixture `tmp_vault`.
- [x] **T092** Commits conventional agrupados (~8-10 commits).
- [x] **T093** `systemctl restart nosvers-mcp`.
- [x] **T094** Verificar carga en `/home/nosvers/logs/mcp.log` y bot reload.
