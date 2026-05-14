# Feature Specification: Claudio Jarvis Evolution — Fase 1

**Feature Branch**: `005-claudio-jarvis`
**Created**: 2026-05-14
**Status**: Approved — implementation autorisée sin parar
**Input**: `BRIEF.md` (proyecto 005) + `public_html/knowledge_base/claudio/IDENTIDAD.md`

---

## Overview

Claudio evoluciona de "Director Ejecutivo de NosVers" a **mayordomo digital familiar
completo** para Angel + África + Bris. Esta Fase 1 es el **foundation domestic**:
amplía el vault con 11 dominios nuevos, añade ~22 tools MCP que cubren recordatorios,
gastos, compras, menús, coche, documentos, salud y memorias personales, prepara
3 automatizaciones de ejemplo (`activo:false`) y expone 3 hooks rápidos en el bot
Telegram (`/gasto`, `/compra`, `/recordar`).

**Cero impacto** en NosVers existente: no se mueve ni se borra nada de la vault actual,
los 15+ tools MCP previos siguen intactos, el bot conserva sus comandos y conversación
natural.

---

## Principios no-negociables (heredados del BRIEF)

1. **Soberanía**: vault local, todo markdown, sin cloud propietario.
2. **Vault es la memoria**: cualquier hecho queda como `.md` legible sin Claudio.
3. **Speaker ID**: cada tool recibe `autor` explícito (`angel` | `africa`); nunca
   acción anónima en dominios sensibles (salud, finanzas).
4. **Modo doméstico vs negocio**: Claudio infiere modo por el dominio del tool.
5. **Pro-actividad CON consentimiento**: Claudio puede *sugerir*; nunca
   reservar/comprar/contratar sin OK humano. Esta Fase 1 no añade acción autónoma.
6. **Familia simétrica**: África = Angel en rango. Bris tiene su espacio.

---

## User Scenarios

### US-1 — Anotar gasto por Telegram (P0)

Angel escribe a @nosvers_hq_bot: `/gasto 45 gasolina coche`
→ Claudio añade entrada en `finanzas/gastos/2026-05.md` con `autor: angel`,
responde "Apuntado: 45€ gasolina (coche). Total mes: 312€".

### US-2 — Crear recordatorio (P0)

África dice por bot: `/recordar 2026-06-12 cumpleaños Lucía`
→ entrada en `familia/recordatorios/2026-06-12-cumpleanos-lucia.md`
con frontmatter `{autor: africa, fecha: 2026-06-12, prioridad: 5, hecho: false}`.

### US-3 — Lista de la compra (P0)

`/compra leche` → añade `- [ ] leche` a `compras/lista_actual.md`.
Otra app/bot puede llamar `lista_compras_completar("leche")` → mueve a
`compras/historico/2026-05.md`.

### US-4 — Sugerir menú (P1)

`menu_sugerir(dia="2026-05-14", ingredientes_disponibles=["tomate","calabacín"])`
devuelve recetas de `menus/recetas/` que matchean los ingredientes.

### US-5 — Estado coche (P1)

`coche_estado()` → leemos `coche/INDEX.md`, devolvemos próxima ITV, último
mantenimiento, kilometraje conocido.

### US-6 — Documentos: anotar y buscar (P1)

`documento_anotar(tipo="factura", contenido_texto="...", fecha="2026-05-10", fuente="EDF", autor="angel")`
→ guarda `documentos/facturas/2026/2026-05-10-edf.md`.
`documentos_buscar("EDF")` → grep sobre `documentos/`.

### US-7 — Memoria personal (P1)

`claudio_recordar(autor="angel", hecho="prefiere café sin azúcar por la mañana", importancia=3)`
→ append a `claudio/memorias/angel/2026-05.md`.
`claudio_contexto(autor="angel", query="café")` → busca y devuelve hechos relevantes.

### US-8 — Recurrentes (P1)

`recurrente_alertar()` lee `finanzas/recurrentes.yaml`, devuelve lista de
cargos que se aproximan en los próximos N días.

### US-9 — Salud (P1)

`medicacion_recordar()` lee `salud/medicacion.yaml`, devuelve qué toca hoy.
`cita_medica_anotar(quien="bris", especialista="veterinario", fecha="2026-06-03", notas="vacuna anual")` → `salud/citas/2026-06-03-bris-veterinario.md`.

### US-10 — Automatizaciones precargadas (P2)

3 YAMLs (`activo:false`) listos para activar:
- `recordatorio_diario_morning.yaml`: cron 7:30 → `recordatorios_listar(periodo='hoy')` → Telegram
- `itv_coche_3_meses.yaml`: cron diario → si ITV < 90 días → Telegram
- `recurrente_alerta_dia_anterior.yaml`: cron diario → cargos en t+1 día → Telegram

---

## Functional Requirements

### Vault scaffolding

**FR-VAULT-1** Crear 11 directorios nuevos sin tocar los existentes:
`claudio/`, `familia/`, `finanzas/`, `salud/`, `documentos/`, `casa/`, `coche/`,
`viajes/`, `lectura/`, `compras/`, `menus/`.

**FR-VAULT-2** Cada directorio tiene un `README.md` que explica qué guarda y
qué tools MCP lo leen/escriben.

**FR-VAULT-3** Seed files vacíos pero útiles:
- `finanzas/recurrentes.yaml` (esquema documentado, lista vacía)
- `salud/medicacion.yaml` (esquema documentado, lista vacía)
- `casa/electrodomesticos.yaml`, `compras/despensa.yaml` (idem)
- `coche/INDEX.md`, `documentos/INDEX.md` (placeholders auto-mantenidos)

**FR-VAULT-4** `claudio/IDENTIDAD.md` ya existe — **no se toca**.
**FR-VAULT-5** `claudio/personalidad.md` se crea con 5 modos diferenciados.

### Tools MCP (~22)

Todos los tools cumplen:

1. Reciben `autor: str` explícito (default `"angel"` solo donde no es sensible).
2. Devuelven `str` con resumen humano para Claudio + datos clave embebidos.
3. Loguean cada llamada como línea JSONL en `claudio/logs/YYYY-MM-DD.jsonl`
   con `{ts, tool, autor, args, ok}`.
4. Tests unitarios con vault temporal (tmp_path).

| Dominio | Tool | Vault target |
|---|---|---|
| familia | `recordatorio_crear` | `familia/recordatorios/<slug>.md` |
| familia | `recordatorios_listar` | lee dir |
| familia | `recordatorio_completar` | mueve a `completados/` |
| finanzas | `gasto_anotar` | append `finanzas/gastos/YYYY-MM.md` |
| finanzas | `gastos_resumen` | parsea y agrega |
| finanzas | `recurrente_alertar` | lee `recurrentes.yaml` |
| compras | `lista_compras_añadir` | append `compras/lista_actual.md` |
| compras | `lista_compras_ver` | lee y formatea |
| compras | `lista_compras_completar` | mueve a histórico |
| menus | `menu_sugerir` | filtra `menus/recetas/` |
| menus | `receta_guardar` | nuevo `.md` |
| coche | `coche_estado` | lee `coche/INDEX.md` |
| coche | `coche_evento` | append + actualiza INDEX |
| documentos | `documento_anotar` | nuevo `.md` con frontmatter |
| documentos | `documentos_buscar` | grep recursivo |
| salud | `medicacion_recordar` | lee `medicacion.yaml` + hora |
| salud | `cita_medica_anotar` | nuevo `.md` |
| claudio | `claudio_recordar` | append `memorias/{autor}/YYYY-MM.md` |
| claudio | `claudio_contexto` | grep `memorias/{autor}/` |
| familia | `familia_cumpleanos_listar` | lee `familia/cumpleanos.md` |
| compras | `despensa_estado` | lee `compras/despensa.yaml` |
| casa | `casa_mantenimiento_anotar` | append `casa/mantenimiento.md` |

**Total: 22 tools nuevos** (15 existentes + 22 = 37 + 8 voz + 5 drive/hostinger ≈ 50).

### Bot Telegram hooks

**FR-BOT-1** `/gasto <monto> <concepto...>` → `gasto_anotar` con autor inferido del chat_id.
**FR-BOT-2** `/compra <item>` → `lista_compras_añadir`.
**FR-BOT-3** `/recordar <fecha> <texto...>` o `/recordar <texto...>` (sin fecha = hoy).
**FR-BOT-4** Respuesta del bot = el `str` que devuelve la tool, sin transformación.

### Automatizaciones (ejemplos)

3 YAML compatibles con el Automation Engine v1 ya desplegado, todos con
`activo: false` para que Angel los revise antes de activar.

---

## Non-functional Requirements

- **NFR-1** Cero deps Python nuevas (todo stdlib + lo ya instalado).
- **NFR-2** Cada tool < 200ms en hardware del VPS para vault < 1k archivos.
- **NFR-3** Concurrencia segura: `gasto_anotar` simultáneos de Angel + África no se pisan (append con file-lock simple por mtime).
- **NFR-4** Privacidad: tools de `salud` requieren `autor` (no default).
- **NFR-5** Bug `telegram_enviar` MCP conocido: estos tools NO llaman Telegram. Solo el bot envía.
- **NFR-6** Logueo estructurado JSONL — auditable post-incidente.

---

## Out of Scope (Fase 2+)

- Widgets cockpit familiares
- Voice intent router (PWA + Linux dictado)
- OCR de facturas
- Integraciones externas (weather, Booking, Spotify, HA)
- Modo niños
- Pro-actividad sin trigger explícito

---

## Definition of Done

- [x] 11 directorios vault con README cada uno
- [x] `claudio/personalidad.md` con 5 modos
- [x] 22 tools MCP nuevos implementados, testeados, registrados en `mcp_server.py`
- [x] 3 automations YAML ejemplo (`activo:false`)
- [x] Bot acepta `/gasto`, `/compra`, `/recordar`
- [x] Smoke tests pasan (`pytest tests/test_claudio_tools.py`)
- [x] MCP reiniciado, tools nuevos cargados (verificar en `mcp.log`)
- [x] ~8 commits conventional agrupados por dominio
- [x] Telegram final único al cerrar trabajo 100% (regla memoria existente)
