# Implementation Plan — Claudio Jarvis · Fase 1

**Feature**: `005-claudio-jarvis`
**Created**: 2026-05-14
**Status**: Ready for tasks

---

## Decisión central: subpackage `claudio_tools/`

En vez de meter 22 funciones en `mcp_server.py` (ya 693 líneas), creamos un
subpackage en `/home/nosvers/claudio_tools/` con un módulo por dominio:

```
/home/nosvers/claudio_tools/
├── __init__.py        ← expone helpers comunes + version
├── common.py          ← VAULT_PATH, ts_iso(), log_jsonl(), atomic_append(),
│                       parse_frontmatter(), slugify(), Author validator
├── identidad.py       ← claudio_recordar, claudio_contexto
├── familia.py         ← recordatorio_*, familia_cumpleanos_listar
├── finanzas.py        ← gasto_anotar, gastos_resumen, recurrente_alertar
├── compras.py         ← lista_compras_*, despensa_estado
├── menus.py           ← menu_sugerir, receta_guardar
├── coche.py           ← coche_estado, coche_evento
├── documentos.py      ← documento_anotar, documentos_buscar
├── salud.py           ← medicacion_recordar, cita_medica_anotar
└── casa.py            ← casa_mantenimiento_anotar
```

Y en `mcp_server.py`, una sola sección nueva con `@mcp.tool()` wrappers que
delegan a estas funciones. Mismo patrón que ya usa `voz.capturar`, `voz.contexto`,
`voz.buscar` (ver mcp_server.py:360-455).

**Por qué subpackage**:
- `mcp_server.py` queda legible
- Tests unitarios independientes del runtime MCP (FastMCP es asyncio)
- El bot Telegram puede importar directamente `from claudio_tools.finanzas import gasto_anotar`
  sin pasar por MCP — más rápido y no toca el bug `telegram_enviar`
- Re-uso futuro desde voice assistant, automations runner, cockpit

---

## Stack

Cero deps nuevas. Solo Python stdlib + lo ya instalado:

| Componente | Tecnología |
|---|---|
| Vault I/O | `pathlib`, `tempfile` (atomic write) |
| Frontmatter | parser propio mínimo (YAML opcional vía `yaml` ya presente) |
| Búsqueda | `re` + walk recursivo |
| Logs | `json` JSONL |
| Fechas | `datetime` + parser permisivo |
| Slug | `re` + `unicodedata` |

YAML files (`recurrentes.yaml`, `medicacion.yaml`) usan `PyYAML` ya instalado
(vimos `import yaml` en otros módulos del repo).

---

## Convenciones compartidas (`common.py`)

```python
VAULT      = Path('/home/nosvers/public_html/knowledge_base')
CLAUDIO    = VAULT / 'claudio'
LOGS       = CLAUDIO / 'logs'
AUTORES    = {'angel', 'africa', 'compartido', 'bris'}

def ts_iso() -> str: ...                           # 2026-05-14T15:32:00+02:00
def ts_human() -> str: ...                         # 14/05/2026 15:32
def slugify(text, max_len=50) -> str: ...
def normalize_author(a) -> str: ...                # raise ValueError si no en AUTORES
def atomic_append(path, content) -> None: ...      # tempfile + os.replace
def atomic_write(path, content) -> None: ...
def log_call(tool: str, autor: str, args: dict, ok: bool, extra=None) -> None:
    LOGS.mkdir(parents=True, exist_ok=True)
    day = LOGS / f"{date.today().isoformat()}.jsonl"
    line = {'ts': ts_iso(), 'tool': tool, 'autor': autor, 'args': args, 'ok': ok}
    if extra: line.update(extra)
    with open(day, 'a', encoding='utf-8') as f:
        f.write(json.dumps(line, ensure_ascii=False) + '\n')

def parse_frontmatter(text: str) -> tuple[dict, str]: ...
def dump_frontmatter(meta: dict, body: str) -> str: ...
```

---

## Formato de archivos

### Gastos (`finanzas/gastos/2026-05.md`)

Append-only markdown estructurado, parseable con regex:

```markdown
# Gastos · 2026-05

- 2026-05-14 14:32 · 45.00€ · gasolina · transporte · angel
- 2026-05-14 16:10 · 12.50€ · pan + verduras · alimentacion · africa
- ...
```

`gastos_resumen` agrega por categoría haciendo regex sobre las líneas.

### Recordatorios (`familia/recordatorios/2026-06-12-cumpleanos-lucia.md`)

```markdown
---
fecha: 2026-06-12
autor: africa
prioridad: 5
hecho: false
creado: 2026-05-14T15:32:00+02:00
---
Cumpleaños Lucía
```

`recordatorios_listar` parsea frontmatter y filtra. `recordatorio_completar`
mueve el archivo a `familia/recordatorios/completados/` y actualiza
`hecho: true`.

### Lista de compras (`compras/lista_actual.md`)

Markdown con checkbox, append-only mientras vive:

```markdown
# Lista de la compra

- [ ] leche · angel · 2026-05-14
- [ ] tomates (1kg) · africa · 2026-05-14
- [x] pan · angel · 2026-05-13   ← se queda hasta el fin de día, luego "completar" la mueve
```

### Memorias (`claudio/memorias/angel/2026-05.md`)

Append por mes, con timestamp + importancia:

```markdown
# Memorias · angel · 2026-05

- 2026-05-14 15:32 · [imp:3] prefiere café sin azúcar por la mañana
- 2026-05-14 15:40 · [imp:5] su madre se llama Carmen
```

`claudio_contexto` hace grep insensitive + ordena por importancia desc.

### Recurrentes (`finanzas/recurrentes.yaml`)

```yaml
# Cargos recurrentes — alimenta recurrente_alertar()
items:
  - nombre: Netflix
    monto_eur: 17.99
    dia_mes: 5
    categoria: ocio
    autor: angel
  - nombre: Seguro coche AXA
    monto_eur: 612.00
    dia_mes: 22
    cada_n_meses: 12
    categoria: coche
    autor: angel
```

`recurrente_alertar(dias=7)` calcula próximos cargos.

### Medicación (`salud/medicacion.yaml`)

```yaml
# Pautas activas — alimenta medicacion_recordar()
items:
  - quien: bris
    medicamento: Antiparasitario Milbemax
    dosis: 1 comprimido
    horas: ['08:00']
    cada_n_dias: 30
    desde: 2026-04-01
```

### Coche (`coche/INDEX.md`)

```markdown
---
matricula: AB-123-CD
modelo: Citroën Berlingo 2018
kilometros: 142500
itv_proxima: 2026-08-12
seguro_renovacion: 2026-11-22
ultimo_mantenimiento: 2026-02-10
---

# Coche

Última actualización: 2026-05-14
```

`coche_evento(tipo, fecha, monto, notas)` añade entrada en
`coche/gastos/2026-05.md` y, si tipo == 'mantenimiento' o 'itv', actualiza
frontmatter de `INDEX.md`.

### Documentos (`documentos/facturas/2026/2026-05-10-edf.md`)

```markdown
---
tipo: factura
fecha: 2026-05-10
fuente: EDF
autor: angel
creado: 2026-05-14T...
---

Factura EDF mayo 2026 — 87.32€. Periodo 2026-04-10 a 2026-05-09.
```

`documentos/INDEX.md` se actualiza al final de `documento_anotar` con una línea
por documento (`- factura · 2026-05-10 · EDF · facturas/2026/2026-05-10-edf.md`).

---

## Tools — firma exacta

```python
# familia.py
def recordatorio_crear(texto: str, fecha: str, autor: str,
                       prioridad: int = 3) -> str: ...
def recordatorios_listar(periodo: str = 'proximos_7_dias',
                         autor: str = '') -> str: ...
def recordatorio_completar(id_o_slug: str) -> str: ...
def familia_cumpleanos_listar(meses: int = 12) -> str: ...

# finanzas.py
def gasto_anotar(monto_eur: float, concepto: str, categoria: str,
                 autor: str) -> str: ...
def gastos_resumen(periodo: str = 'mes_actual', categoria: str = '') -> str: ...
def recurrente_alertar(dias: int = 7) -> str: ...

# compras.py
def lista_compras_añadir(item: str, autor: str,
                         cantidad: str = '', urgente: bool = False) -> str: ...
def lista_compras_ver() -> str: ...
def lista_compras_completar(item: str) -> str: ...
def despensa_estado() -> str: ...

# menus.py
def menu_sugerir(dia: str = '', ingredientes_disponibles: str = '') -> str: ...
def receta_guardar(nombre: str, ingredientes: str, pasos: str,
                   fuente: str = '') -> str: ...

# coche.py
def coche_estado() -> str: ...
def coche_evento(tipo: str, fecha: str, monto_eur: float = 0.0,
                 notas: str = '', autor: str = 'angel') -> str: ...

# documentos.py
def documento_anotar(tipo: str, contenido_texto: str, fecha: str,
                     fuente: str, autor: str) -> str: ...
def documentos_buscar(query: str, limite: int = 20) -> str: ...

# salud.py
def medicacion_recordar() -> str: ...
def cita_medica_anotar(quien: str, especialista: str, fecha: str,
                       notas: str = '', autor: str = 'angel') -> str: ...

# identidad.py
def claudio_recordar(autor: str, hecho: str, importancia: int = 5) -> str: ...
def claudio_contexto(autor: str, query: str, limite: int = 10) -> str: ...

# casa.py
def casa_mantenimiento_anotar(tarea: str, fecha: str = '',
                              proximo: str = '', autor: str = 'angel') -> str: ...
```

**Nota MCP**: FastMCP no acepta caracteres no-ASCII en nombres de tool. Se
expone `lista_compras_anadir` (sin tilde) en MCP, pero el módulo Python
conserva `añadir` para no perder semántica en código. Wrapper resuelve la
diferencia.

---

## Bot Telegram — hooks

En `bot/bot_v2.py`, justo después de `vault_read_cmd` (línea ~417):

```python
from claudio_tools.finanzas import gasto_anotar as _gasto_anotar
from claudio_tools.compras  import lista_compras_añadir as _lista_compras_anadir
from claudio_tools.familia  import recordatorio_crear as _recordatorio_crear

def _autor_from_user(user_id: int) -> str:
    if user_id == AFRICA_CHAT_ID: return 'africa'
    return 'angel'   # ANGEL_ID, ANGEL_PROXY_ID

async def gasto_cmd(update, context):
    if not is_authorized(...): return
    if not context.args or len(context.args) < 2:
        return await update.message.reply_text("Uso: /gasto <monto> <concepto> [categoria]")
    try:
        monto = float(context.args[0].replace(',', '.'))
    except ValueError:
        return await update.message.reply_text("Monto inválido.")
    resto = context.args[1:]
    # último token = categoría si está en {alimentacion, transporte, hogar, ocio, salud, otros}
    CATS = {'alimentacion','transporte','hogar','ocio','salud','otros','coche'}
    if len(resto) > 1 and resto[-1].lower() in CATS:
        categoria = resto[-1].lower(); concepto = ' '.join(resto[:-1])
    else:
        categoria = 'otros'; concepto = ' '.join(resto)
    autor = _autor_from_user(update.effective_user.id)
    out = _gasto_anotar(monto, concepto, categoria, autor)
    await update.message.reply_text(out)
```

Similar para `/compra` y `/recordar`. `/recordar` acepta:
- `/recordar 2026-06-12 cumpleaños Lucía` → fecha + texto
- `/recordar mañana llamar fontanero` → "mañana" → today+1
- `/recordar llamar fontanero` → fecha = hoy

Parser de fecha en `common.parse_date_natural(text) -> (date|None, resto:str)`.

---

## Automatizaciones

Mismo schema que el Automation Engine v1 ya desplegado
(ver `specs/automation-engine/.../spec.md`). Cada YAML tiene:

```yaml
id: <slug>
nombre: <legible>
autor: angel
creado: 2026-05-14T...
modificado: 2026-05-14T...
activo: false
trigger: { tipo: cron, rrule: '30 7 * * *' }
acciones:
  - tipo: mcp_tool
    tool: recordatorios_listar
    params: { periodo: 'hoy' }
    output_var: lista
  - tipo: condicional
    si: '{{lista}} != "(sin recordatorios)"'
    entonces:
      - tipo: telegram_directo
        chat_id: '{{ANGEL_CHAT_ID}}'
        text: |
          🌅 Buenos días.
          Hoy:
          {{lista}}
metadatos:
  descripcion: Resumen matinal de recordatorios.
  tags: [familia, claudio, daily]
```

Los 3 YAML se guardan en
`public_html/knowledge_base/automatizaciones/`. **Todos con `activo:false`** —
Angel decide.

---

## Logging y privacidad

- Cada llamada a tool → línea JSONL en `claudio/logs/YYYY-MM-DD.jsonl`
- En log NUNCA va contenido sensible (no se loguea el texto del hecho médico,
  solo metadata: `{tool, autor, ok, len_input}`)
- `salud/*` y `claudio/memorias/*` no son indexados por `documentos_buscar`

---

## Tests

`tests/test_claudio_tools.py`:
- Cada tool tiene 1-3 cases: happy path + edge case (vault vacío, autor inválido)
- Fixture `tmp_vault` que crea estructura mínima en `tmp_path` y monkeypatches `common.VAULT`
- ~30 tests totales, < 5s de runtime

---

## Restart MCP y verificación

```bash
systemctl restart nosvers-mcp
sleep 2
tail -30 /home/nosvers/logs/mcp.log
# Verificación: el log muestra "FastMCP" arrancando sin errores;
# alternativamente curl al endpoint MCP para listar tools.
```

Si falla la importación de `claudio_tools` desde `mcp_server.py`, el
servidor MCP cae completo — riesgo aceptado. Mitigación: `try/except` alrededor
del bloque de imports nuevos, log de warning, MCP arranca con tools antiguos
intactos.

---

## Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| Caracteres no-ASCII en nombre de tool MCP rompen FastMCP | Wrapper renombra `lista_compras_añadir` → `lista_compras_anadir` solo en el decorator |
| Import cíclico bot ↔ claudio_tools | `claudio_tools` no importa nada de `bot/` |
| Race condition en append concurrente | `os.replace` atomic + retry si IOError |
| Telegram_enviar MCP bug | Estos tools no llaman Telegram. El bot responde sincrónicamente al usuario |
| Vault path hardcoded | Override por env `VAULT_PATH` opcional en `common.py` (para tests sin monkeypatch) |
| YAML schema drift | El parser de `recurrentes.yaml` ignora claves desconocidas (forward compat) |

---

## Plan de commits (8 commits aprox)

1. `feat(005): specs (BRIEF + spec + plan + tasks)`
2. `feat(005-vault): scaffolding 11 dirs + READMEs + seed YAMLs`
3. `feat(005-claudio): personalidad.md + claudio_tools/common + identidad`
4. `feat(005-familia): recordatorios + cumpleaños tools`
5. `feat(005-finanzas): gastos + recurrentes tools`
6. `feat(005-compras-menus): lista compras + recetas + despensa + casa`
7. `feat(005-coche-doc-salud): coche + documentos + salud tools`
8. `feat(005-mcp): wire 22 tools en mcp_server.py + automations YAML`
9. `feat(005-bot): hooks /gasto /compra /recordar`
10. `test(005): smoke tests claudio_tools`

(9-10 commits, agrupables si conviene.)
