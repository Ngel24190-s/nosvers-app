# Implementation Plan — Automation Engine (n8n light)

**Feature**: 004-automation-engine
**Created**: 2026-05-13
**Status**: Ready for tasks

---

## Stack

### Backend (Python 3.11, asyncio)

| Componente | Tecnología | Justificación |
|---|---|---|
| HTTP layer | Starlette (existente, montado en uvicorn MCP) | Mismo proceso, sin sidecar |
| Validación | Pydantic v2 | Schemas → JSON Schema vía `model_json_schema()` para alimentar el editor |
| Cron | `croniter` (nueva dep) | Estándar para rrule; ya mencionada en BRIEF |
| YAML | `PyYAML` (ya presente, `safe_load`) | — |
| WS | `tablero/v2/ws.py` (broker existente) | Añadir canal `automation` |
| HTTP cliente | `httpx` async (ya disponible) | Para `webhook_call`, `wp_post` |
| Auth | `voz.auth.validar_token` (existente) | JWT compartido con resto del tablero |
| Telegram | `bot.bot.send_message_direct` (helper Python en `/home/nosvers/bot/`) | Bypass del bug MCP stall (D-008) |
| Anthropic | `anthropic` SDK (ya en requirements unified-agent) | `claude_prompt` action |

### Frontend (React 18 + TypeScript + Vite)

| Componente | Tecnología | Justificación |
|---|---|---|
| Editor visual | `reactflow` (nueva dep frontend) | Best-in-class para canvas nodos drag-drop |
| Forms | Componente custom `<JsonSchemaForm>` simple | Evitar añadir librería pesada; el catálogo viene del backend |
| YAML preview | `@monaco-editor/react` (nueva dep) | Read-only, syntax highlighting |
| Routing | Hash routing existente (sin `react-router`) | Adoptamos `#cockpit/automatizaciones` para no introducir un router |
| Toast | `sonner` (ya presente) | Reutilizado |

### Persistencia

- **Source of truth**: ficheros YAML en `knowledge_base/automatizaciones/`.
- **Capa atómica**: `tablero.v2.atomic_write.atomic_write_text` (existente).
- **Logs**: JSONL en `automatizaciones/logs/YYYY-MM-DD.jsonl` con `aiofiles` para
  append no bloqueante (o synchronous + asyncio.to_thread si simple).

---

## Layout de ficheros

### Backend (raíz: `/home/nosvers/`)

```
tablero/v2/automatizaciones/
├── __init__.py
├── models.py              # Pydantic: Automation, Trigger union, Action union
├── storage.py             # Read/write YAML + listado + atomic
├── catalogo.py            # Genera JSON Schema desde Pydantic models
├── motor.py               # Loop principal asyncio: cron + WS subscriber
├── actions.py             # Implementación de cada action (dia_capturar, telegram, ...)
├── triggers.py            # Adaptadores de cada trigger (filtros + matching)
├── interpolation.py       # Resolver {{vars}}
├── condicional.py         # DSL evaluador seguro (D-003)
├── runner.py              # Ejecutor de una cadena: state machine
├── logs.py                # Append JSONL + lectura por fecha
├── webhooks.py            # Handlers HTTP de Stripe + genérico
├── rest.py                # Handlers REST: GET/POST/PUT/DELETE/run/test/logs/catalogo
└── tests_examples.py      # Helpers para tests
```

### Routes nuevas (montadas en `tablero/rest.py`)

```
GET    /tablero/api/v2/automatizaciones                      → list_handler
POST   /tablero/api/v2/automatizaciones                      → create_handler
GET    /tablero/api/v2/automatizaciones/catalogo             → catalogo_handler
POST   /tablero/api/v2/automatizaciones/reload               → reload_handler
GET    /tablero/api/v2/automatizaciones/{id}                 → get_handler
PUT    /tablero/api/v2/automatizaciones/{id}                 → update_handler
DELETE /tablero/api/v2/automatizaciones/{id}                 → delete_handler
POST   /tablero/api/v2/automatizaciones/{id}/run             → run_handler
POST   /tablero/api/v2/automatizaciones/{id}/test            → test_handler
GET    /tablero/api/v2/automatizaciones/{id}/logs            → logs_handler
POST   /tablero/api/v2/automatizaciones/webhook/stripe       → webhook_stripe_handler
```

### Frontend (raíz: `/home/nosvers/tablero/web/src/`)

```
components/automatizaciones/
├── AutomationListPage.tsx        # Página /cockpit/automatizaciones
├── AutomationEditor.tsx          # Canvas React Flow
├── NodePalette.tsx               # Panel lateral derecho
├── NodeTrigger.tsx
├── NodeAction.tsx
├── JsonSchemaForm.tsx            # Form genérico desde schema
├── YamlPreview.tsx               # Monaco read-only
├── TestRunModal.tsx
├── ExecutionHistoryModal.tsx
└── lib/
    ├── apiAutomations.ts          # Llamadas REST
    ├── yamlExport.ts              # Serialización nodos → YAML
    └── schemas.ts                  # TypeScript types desde catálogo

components/cockpit/AutomationsWidget.tsx     # Widget #13
hooks/useAutomationStream.ts                  # WS canal automation
```

### Logs y ejemplos (vault)

```
public_html/knowledge_base/automatizaciones/
├── ejemplo_stripe_pago_grande.yaml
├── ejemplo_lunes_agt05.yaml
├── ejemplo_voz_urgente.yaml
├── archivadas/
└── logs/
```

### Documentación

```
tablero/AUTOMATIZACIONES.md
```

---

## Integración con el WS broker existente

**Patch minimal en `tablero/v2/ws.py`**:

```python
VALID_CHANNELS = {"health", "claude", "activity", "agentes", "revenue", "aegis", "wake", "automation"}
```

El motor se suscribe al broker como **listener interno** (no como WebSocket
cliente). Usa el patrón:

```python
# En motor.py
from tablero.v2.ws import broker

class InternalSubscriber:
    """Suscriptor interno que recibe broadcasts sin pasar por WS."""
    def __init__(self):
        self.queue = asyncio.Queue()

    async def send(self, payload):  # interfaz duck-typed compatible con Broker
        await self.queue.put(payload)
```

Para v1, en lugar de hookear `broker.broadcast`, el motor **publica al broker**
los eventos de ejecución, y **lee directamente** los datos publicados por los
workers a través de un sidecar `subscribe_hook` que añadiremos al `Broker`
(o más simple: cada worker invoca al motor vía un `event_bus.publish_event`).

**Decisión final**: añadir un hook `Broker.add_internal_subscriber(callable)` que
los workers de cockpit invocarán también, sin romper el flujo WS existente.
Patch < 20 líneas.

---

## Integración con unified-agent

La action `ejecutar_agente` invoca el agente como subprocess (no in-process)
para aislar:

```bash
python /home/nosvers/unified-agent/nosvers_agent.py --agente <name> --params <json>
```

Captura stdout/stderr con timeout (default 60s para esta action, más alto que
el default 30s).

---

## Webhook Stripe — seguridad

Header `Stripe-Signature` verificado con secret `STRIPE_WEBHOOK_SECRET` de
`.env.local`. Si secret no existe, el endpoint responde 503 con mensaje claro.

```python
stripe_signature = request.headers.get("stripe-signature")
event = stripe.Webhook.construct_event(payload, stripe_signature, secret)
```

Si `stripe` SDK no está instalado o secret missing → 503. No bloqueamos el resto
del sistema.

---

## Motor — loop principal

```python
async def motor_loop():
    automations = load_all_from_vault()
    cron_task = asyncio.create_task(cron_tick_loop(automations))   # cada 30s
    ws_task = asyncio.create_task(ws_event_loop(automations))      # bucle eventos
    while True:
        await asyncio.sleep(3600)   # heartbeat; reloads via SIGHUP/endpoint
```

`cron_tick_loop` evalúa cada minuto si alguna automatización cron debe ejecutarse
en la ventana `[now-30s, now]`.

`ws_event_loop` lee de la queue interna donde los workers publican eventos.

---

## Idempotencia

`dict[tuple[str,str], float]` en memoria con TTL 5s, garbage collected en cada
nueva inserción.

---

## Performance budget

| Operación | Budget |
|---|---|
| `GET /automatizaciones` (100 items) | < 200ms |
| Test-run cadena 5 acciones (mock) | < 2s |
| Trigger WS → primera acción | < 1s |
| Tick cron | < 50ms (sin disparo) |
| Listar logs día actual | < 100ms para 1000 líneas |

---

## Testing strategy

- **Unit**:
  - `test_v2_automatizaciones_models.py` — Pydantic round-trip de cada Trigger/Action.
  - `test_v2_automatizaciones_storage.py` — write/read/list YAML, id duplicados, atomicidad.
  - `test_v2_automatizaciones_actions.py` — cada action mockeada (HTTP, Telegram, Anthropic).
  - `test_v2_automatizaciones_triggers.py` — matching de filtros.
  - `test_v2_automatizaciones_interpolation.py` — `{{...}}` resolver.
  - `test_v2_automatizaciones_condicional.py` — DSL evaluador (incluye intentos de eval injection).
  - `test_v2_automatizaciones_motor.py` — cron tick + WS event dispatch.

- **Integration**:
  - `test_v2_automatizaciones_api.py` — CRUD + run + test + logs (Starlette TestClient).
  - `test_v2_automatizaciones_e2e.py` — cadena completa con trigger cron mock → 3 acciones → log assertion.

- **No regresión**:
  - Run `pytest tablero/tests/` completo. Cero fallos respecto a baseline.

---

## Riesgos

| Riesgo | Mitigación |
|---|---|
| `reactflow` pesa ~500KB minified | Code splitting; cargar lazy en la ruta `automatizaciones` |
| Bug MCP stall reaparece en runtime al llamar Telegram | D-008: bypass directo `bot.send_message_direct` |
| Cron tick muy frecuente acumula carga | 30s tick + croniter es O(N); 100 automatizaciones = <10ms |
| Acción `claude_prompt` puede ser cara | Default `model: haiku`, max_tokens 2000, timeout 30s |
| YAML corruptos rompen reload completo | try/except por fichero; corruptos quedan listados, no abortan reload |

---

## Compatibilidad con releases

- Cero cambios breaking en 002 (`/tablero/api/v2/*` existentes intactos).
- WS broker: añadir canal `automation` a `VALID_CHANNELS` — los clientes
  existentes nunca se suscriben a un canal nuevo, así que cero impacto.
- Tests existentes (`test_v2_cockpit_ws.py` etc.) actualizar para reflejar
  nuevo canal en `VALID_CHANNELS` si fuese necesario (espera explícita).

---

## Definition of Done (cross-check con BRIEF)

| BRIEF requirement | Plan resolution |
|---|---|
| 8+ tipos de triggers | FR-020 a FR-027 = 8 ✓ |
| 10+ tipos de actions | FR-030 a FR-039 = 10 ✓ |
| Editor visual drag-drop | React Flow + NodePalette + JsonSchemaForm ✓ |
| 3 automatizaciones de ejemplo | `ejemplo_*.yaml` × 3 ✓ |
| Widget visibilidad cockpit | `AutomationsWidget.tsx` + grid #13 ✓ |
| Unit + integration tests | Sección "Testing strategy" ✓ |
| Doc `AUTOMATIZACIONES.md` | Listado en layout ✓ |
| Pulido del cockpit | Tarea separada T-070+ en tasks.md |
