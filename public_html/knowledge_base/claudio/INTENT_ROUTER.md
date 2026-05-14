# Intent Router — Cómo añadir tools al routing por voz

El intent router es el módulo que decide qué tool MCP ejecutar para un
texto dictado. Vive en `voz/intent_router.py` y se alimenta de un prompt
editable en `public_html/knowledge_base/prompts/intent_router.md`.

Esta guía es para añadir un tool nuevo al router con cero downtime.

## Anatomía

```
[transcripción local] → POST /voz/api/dictado-procesar
                          │
                          ├─ voz.intent_router.route_intent(text, autor)
                          │     ├─ carga prompt del vault
                          │     ├─ POST Anthropic Haiku
                          │     └─ parse JSON → IntentResult
                          ├─ voz.rest._execute_intent(intent, ...)
                          │     └─ delega al callable del tool
                          ├─ voz.compose_voice_response(...)
                          │     └─ templates por tool
                          └─ JSON { intent, tool_result, voice_response }
```

## Pasos para añadir un tool nuevo (ej. `regar_huerto`)

### 1. Crea el tool en `claudio_tools/` (o donde corresponda)

```python
# claudio_tools/huerto.py
def regar_huerto(zona: str, autor: str) -> str:
    ...
```

Y exponlo en `mcp_server.py` con `@mcp.tool()`.

### 2. Whitelist en el router

`voz/intent_router.py`:
```python
ALLOWED_TOOLS = {
    ...,
    "regar_huerto",
}
```

### 3. Documenta el tool en el prompt

`public_html/knowledge_base/prompts/intent_router.md` — añade una entrada
en la tabla con la firma de args y una regla:

```markdown
- `regar_huerto(zona: str)` — apunta riego del huerto. Zonas: tomates|judías|...
```

Y en las reglas de routing:

```markdown
- "he regado X" o "riega X" → regar_huerto
```

### 4. Despacha en `voz/rest.py::_execute_intent`

```python
from claudio_tools import huerto as _huer
...
if tool == "regar_huerto":
    return _huer.regar_huerto(args.get("zona", ""), autor)
```

### 5. Template de voz en `voz/compose_voice_response.py`

```python
def _t_regar_huerto(args, result, autor):
    return f"Regado en {args.get('zona', '')}."

_TEMPLATES["regar_huerto"] = _t_regar_huerto
```

### 6. Test en `tests/test_intent_router.py`

```python
def test_regar_huerto(monkeypatch):
    _patch_post(monkeypatch, _mk_anthropic_response({
        "tool": "regar_huerto",
        "args": {"zona": "tomates"},
        "confidence": 0.9,
    }))
    res = _run(router.route_intent("he regado los tomates", "angel"))
    assert res.tool == "regar_huerto"
```

### 7. Reinicia el dev server (o el proceso MCP en prod)

```bash
pkill -f tablero/scripts/dev_server || true
setsid env TABLERO_DEV=1 MCP_TOKEN="$MCP_TOKEN" python3 \
  tablero/scripts/dev_server.py > /tmp/dev_server.log 2>&1 < /dev/null &
```

## Reglas de seguridad

- **NUNCA** acepta `autor` desde `args`: el router lo borra
  (`args.pop("autor", None)`). El autor real viene del JWT (`sub`).
- Tools de salud (`cita_medica_anotar`, `medicacion_recordar`) reciben
  el autor inyectado server-side y nunca uno del modelo.
- Si añades un tool con efectos destructivos (borrar, mover, mandar
  email), revisa que el endpoint lo expone solo a JWTs válidos. Considera
  pedir confirmación previa (futuro: `voice_response` con prompt y un
  segundo POST de confirmación).

## Confidence threshold

Default: 0.6. Configurable en `voz/intent_router.DEFAULT_THRESHOLD`. Si
quieres un tool más estricto (ej. acciones destructivas), considera un
threshold local en `_execute_intent` antes de invocar.

## Cache idempotente

Por defecto el router cachea `(sha256(text), autor)` durante 5 s. Esto
evita ejecuciones dobles por doble-tap. Si tu tool nuevo no es
idempotente y debe ejecutar siempre, **NO** lo bypasses aquí — añade
control de versión en el tool (`coche_evento` ya lo hace con timestamp
en el slug).

## Editar el prompt sin redeploy

El archivo `prompts/intent_router.md` se recarga **en cada llamada**
(`_load_prompt()` lee del disco). Puedes editar las reglas en caliente
desde la PWA de notas, Obsidian o ssh — el siguiente dictado usará el
prompt nuevo. Si el archivo se borra o queda vacío, el router usa el
fallback hardcoded de `_FALLBACK_PROMPT`.

## Logs

Cada llamada deja una línea JSONL en
`public_html/knowledge_base/claudio/logs/dictado-YYYY-MM-DD.jsonl`:

```json
{"ts":"...","autor":"angel","transcript_len":27,"intent":{"tool":"gasto_anotar","confidence":0.94,"fallback":false},"args":{...},"ok":true,"latency_ms":920,"device":"pwa-android"}
```

Por privacidad, el transcript completo NO se loguea. Habilitar con
`CLAUDIO_DICTADO_LOG_FULL=1` solo para debugging puntual.

## TODOs blandos (Fase 4+)

- `POST /tablero/api/v2/action` para que widgets marquen items como
  hechos (interacciones optimistas). Hoy los widgets son read-only.
- Multi-tool en un único dictado ("apunta leche Y recuérdame mañana").
- Confirmación previa para destructivos.
