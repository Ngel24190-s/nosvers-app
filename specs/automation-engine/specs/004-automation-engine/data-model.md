# Data Model — Automation Engine

## Pydantic models (Python 3.11, Pydantic v2)

### `Automation`

```python
from typing import Annotated, Literal, Union
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

Autor = Literal["angel", "africa", "claude"]

class Automation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(pattern=r"^(auto|ejemplo)_\d{4}_\d{2}_\d{2}_[a-z0-9_]{1,60}$")
    nombre: str = Field(min_length=1, max_length=120)
    autor: Autor
    creado: datetime
    modificado: datetime
    activo: bool = False
    trigger: "Trigger"
    acciones: list["Action"] = Field(min_length=1, max_length=20)
    metadatos: dict = Field(default_factory=dict)
```

### Trigger union (sealed)

```python
class CronTrigger(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tipo: Literal["cron"]
    rrule: str  # validado con croniter en validator

class WebhookStripeTrigger(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tipo: Literal["webhook_stripe"]
    evento: str = "payment_intent.succeeded"
    filtros: dict = Field(default_factory=dict)
    # filtros soportados: amount_gte_eur (float), customer_email_regex

class NotaCapturadaTrigger(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tipo: Literal["nota_capturada"]
    filtros: dict = Field(default_factory=dict)
    # filtros: autor, etiqueta, contenido_regex

class AgenteTerminadoTrigger(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tipo: Literal["agente_terminado"]
    filtros: dict = Field(default_factory=dict)
    # filtros: nombre_agente, estado (success|error|*)

class AegisAlertaTrigger(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tipo: Literal["aegis_alerta"]
    filtros: dict = Field(default_factory=dict)
    # filtros: severidad (info|warn|critical)

class EmailMatchTrigger(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tipo: Literal["email_match"]
    filtros: dict = Field(default_factory=dict)
    # filtros: from_regex, subject_regex

class VozKeywordTrigger(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tipo: Literal["voz_keyword"]
    keywords: list[str] = Field(min_length=1)

class VpsThresholdTrigger(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tipo: Literal["vps_threshold"]
    metrica: Literal["cpu", "ram", "disk"]
    umbral_pct: float = Field(ge=0, le=100)
    comparador: Literal["gt", "lt"]

Trigger = Annotated[
    Union[
        CronTrigger, WebhookStripeTrigger, NotaCapturadaTrigger,
        AgenteTerminadoTrigger, AegisAlertaTrigger, EmailMatchTrigger,
        VozKeywordTrigger, VpsThresholdTrigger,
    ],
    Field(discriminator="tipo"),
]
```

### Action union (sealed)

```python
class DiaCapturarAction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tipo: Literal["dia_capturar"]
    texto: str
    etiqueta: str = ""
    autor: Autor | None = None  # default = autor de la automatización

class TelegramAction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tipo: Literal["telegram"]
    mensaje: str
    chat_id: str | None = None  # default = ANGEL_CHAT_ID

class EjecutarAgenteAction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tipo: Literal["ejecutar_agente"]
    agente: str
    params: dict = Field(default_factory=dict)

class ClaudePromptAction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tipo: Literal["claude_prompt"]
    model: Literal["claude-haiku-4-5-20251001", "claude-opus-4-7", "claude-sonnet-4-6"] = "claude-haiku-4-5-20251001"
    system: str = ""
    prompt: str
    max_tokens: int = Field(default=2000, ge=1, le=16000)

class EmailEnviarAction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tipo: Literal["email_enviar"]
    to: str
    subject: str
    body: str

class WebhookCallAction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tipo: Literal["webhook_call"]
    url: str
    method: Literal["GET", "POST", "PUT", "DELETE"] = "POST"
    headers: dict = Field(default_factory=dict)
    body_json: dict | None = None

class CockpitToastAction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tipo: Literal["cockpit_toast"]
    level: Literal["ok", "warn", "error"] = "ok"
    text: str

class WpPostAction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tipo: Literal["wp_post"]
    titulo: str
    contenido_html: str
    status: Literal["draft", "publish"] = "draft"

class DelayAction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tipo: Literal["delay"]
    segundos: float = Field(ge=0.1, le=300)

class CondicionalAction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tipo: Literal["condicional"]
    expresion: str
    acciones_si: list["Action"] = Field(min_length=1)
    acciones_no: list["Action"] = Field(default_factory=list)

Action = Annotated[
    Union[
        DiaCapturarAction, TelegramAction, EjecutarAgenteAction,
        ClaudePromptAction, EmailEnviarAction, WebhookCallAction,
        CockpitToastAction, WpPostAction, DelayAction, CondicionalAction,
    ],
    Field(discriminator="tipo"),
]
```

---

## ExecutionLog (JSONL)

Una línea por ejecución. Append-only.

```json
{
  "automation_id": "auto_2026_05_13_stripe_pago",
  "automation_nombre": "Notificar pagos Stripe grandes",
  "trigger": {"tipo": "webhook_stripe", "payload": {"amount": 150, "customer": "x@y.com"}},
  "autor_trigger": "angel",
  "started_at": "2026-05-13T18:42:11.234Z",
  "ended_at": "2026-05-13T18:42:11.789Z",
  "duration_ms": 555,
  "status": "ok",
  "steps": [
    {"n": 1, "action_tipo": "dia_capturar", "ok": true, "duration_ms": 120, "output": {"slug": "..."}},
    {"n": 2, "action_tipo": "telegram", "ok": true, "duration_ms": 410}
  ]
}
```

`status ∈ ok | partial | error | interrupted`
- `ok`: todos los steps `ok: true`.
- `partial`: ≥1 step falló pero la cadena continuó.
- `error`: cortocircuito por error fatal (ej. condicional malformado).
- `interrupted`: motor reiniciado durante ejecución.

---

## WS messages — canal `automation`

**Update streams** (publicados por el motor):

```json
{"type":"update","channel":"automation","payload":{"event":"started","automation_id":"...","trigger":{...},"ts":...},"ts":...}
{"type":"update","channel":"automation","payload":{"event":"step","automation_id":"...","n":1,"ok":true,"duration_ms":120},"ts":...}
{"type":"update","channel":"automation","payload":{"event":"finished","automation_id":"...","status":"ok","duration_ms":555},"ts":...}
{"type":"update","channel":"automation","payload":{"event":"toast","level":"ok","text":"..."},"ts":...}
```

**Snapshot** (al suscribirse): últimas 10 ejecuciones en RAM del worker.

```json
{"type":"snapshot","channel":"automation","payload":{"recent":[{...}, ...]},"ts":...}
```
