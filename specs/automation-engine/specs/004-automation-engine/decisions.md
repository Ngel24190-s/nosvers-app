# Clarifications & Decisions

**Mode**: Decisiones autónomas (sin parar para preguntar a Angel — instrucción "sin parar")

Las siguientes ambigüedades del BRIEF se resuelven con defaults pragmáticos. Si Angel
quiere cambiarlas más tarde, son ajustes locales (no afectan arquitectura).

---

## D-001 · Deployment del motor

**Pregunta**: ¿Motor como systemd separado o embebido en uvicorn MCP?

**Decisión**: **Embebido en uvicorn MCP** (mismo proceso que sirve `/tablero/api/v2/*`)
con tarea asyncio arrancada en `startup` hook (mismo patrón que cockpit workers).

**Por qué**:
- Acceso directo al `broker` in-process sin atravesar WS.
- Una unidad systemd menos que mantener (`linger=yes` ya activado).
- Reduce 100ms+ de latencia comparado con WS cliente.
- Cero impacto en uptime: ya hay 7 workers viviendo así.

**Trade-off**: si el MCP se reinicia, todas las ejecuciones in-flight se pierden.
Mitigado por el log JSONL marcando `interrupted` al arrancar de nuevo (FR-046, NFR-002).

---

## D-002 · Identidad del autor en ejecuciones manuales

**Pregunta**: cuando se hace `POST /run` manual, ¿qué `autor` se registra en log?

**Decisión**: `autor_trigger: <sub del JWT que llamó al endpoint>`, `autor_automation:
<autor original del YAML>`. Ambos en el log.

**Por qué**: separar quién diseñó la automatización vs. quién la disparó. Auditoría
limpia.

---

## D-003 · Schema de validación condicional

**Pregunta**: ¿cómo se evalúa la `expresion` del nodo `condicional` sin abrir un eval
inseguro?

**Decisión**: subset DSL muy limitado: `{{var}} <comparador> <literal>` donde
comparador ∈ `>, <, >=, <=, ==, !=, contains, matches`. Parsing con regex; sin AST
arbitrario.

**Ejemplos válidos**: `{{trigger.amount}} > 100`, `{{paso_1.respuesta}} contains "OK"`.
**Inválidos**: `import os`, `exec(...)`, `__import__`.

**Por qué**: cubre el 95% de casos sin abrir CVE.

---

## D-004 · Interpolación de variables

**Pregunta**: ¿qué variables están disponibles dentro de `{{...}}`?

**Decisión**:
- `{{trigger.X}}` — campos del payload del trigger
- `{{paso_<n>.X}}` — output del paso n (1-indexed)
- `{{env.X}}` — variables de entorno permitidas (whitelist: `ANGEL_CHAT_ID`,
  `WP_API`, etc.)
- `{{now}}`, `{{today}}` — timestamp / fecha actual ISO

**Implementación**: regex `\{\{([\w.]+)\}\}` + lookup en dict; valor faltante = `""`
con warning en log.

---

## D-005 · Canal WS `automation`

**Pregunta**: ¿se añade un nuevo canal o se reutiliza uno existente?

**Decisión**: nuevo canal `automation` añadido a `VALID_CHANNELS` en
`tablero/v2/ws.py`. Patch minimal, una línea.

**Por qué**: mantener namespaces semánticos. El cockpit widget filtra por canal.

---

## D-006 · Estructura del directorio vault

**Pregunta**: layout exacto bajo `knowledge_base/automatizaciones/`.

**Decisión**:
```
knowledge_base/automatizaciones/
├── auto_2026_05_13_stripe_pago.yaml      (activos + pausados)
├── ejemplo_*.yaml                        (3 ejemplos pre-cargados)
├── archivadas/
│   └── auto_*_deleted_<timestamp>.yaml   (DELETE las mueve aquí)
└── logs/
    └── 2026-05-13.jsonl                  (rotación diaria)
```

---

## D-007 · Frontend routing

**Pregunta**: ¿la página `/cockpit/automatizaciones` es ruta independiente o overlay?

**Decisión**: **ruta nueva** `/cockpit/automatizaciones` con `react-router` (ya
disponible en el proyecto). Header del cockpit ya tiene espacio para un link nuevo.
Botón "Editor" en el widget #13 abre esta ruta.

---

## D-008 · Telegram en motor — bug stall MCP

**Pregunta**: la memoria `project_telegram_enviar_stall.md` dice que `telegram_enviar`
MCP se cuelga. ¿Cómo enviar Telegram desde el motor sin colgarlo?

**Decisión**: el motor llama a la función Python subyacente del bot
(`/home/nosvers/bot/bot.py::send_message` o equivalente) **directamente, no via
MCP**. Timeout 10s. Si falla, log `ok: false` y continúa.

**Por qué**: el bug está en la capa MCP, no en el SDK Telegram. Bypass.

---

## D-009 · Catálogo dinámico para editor visual

**Pregunta**: ¿el editor visual conoce los campos de cada trigger/action a priori, o
los pide al backend?

**Decisión**: backend expone `GET /catalogo` con JSON Schema generado a partir de
los modelos Pydantic (`model_json_schema()`). El frontend renderiza formularios con
un componente genérico tipo `<JsonSchemaForm>` (custom, simple, no librería pesada).

**Por qué**: una sola fuente de verdad. Añadir un trigger nuevo en backend lo hace
aparecer automáticamente en el editor.

---

## D-010 · Idempotencia v1

**Pregunta**: ¿qué evita ejecuciones duplicadas si llega el mismo evento dos veces?

**Decisión**: clave `(automation_id, trigger_hash)` con TTL 5s en memoria. Si llega
otro evento idéntico dentro de 5s, se descarta. **No persistente** entre reinicios
(simple v1).

**Por qué**: persistencia robusta de idempotencia (Redis/SQLite) es over-engineering
para v1. El BRIEF lo menciona como "simple v1" implícito.
