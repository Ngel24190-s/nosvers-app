# API Contracts — `/tablero/api/v2/automatizaciones/*`

Auth: JWT en header `Authorization: Bearer <token>` (vía `voz.auth.validar_token`).
Lectura: `angel`, `africa`, `claude`. Escritura: `angel`, `africa`. Ejecución: cualquier autenticado.

---

## `GET /tablero/api/v2/automatizaciones`

Lista todas las automatizaciones.

**Response 200**:
```json
{
  "items": [
    {
      "id": "auto_2026_05_13_stripe_pago",
      "nombre": "Notificar pagos Stripe grandes",
      "autor": "angel",
      "activo": true,
      "trigger_tipo": "webhook_stripe",
      "modificado": "2026-05-13T18:00:00Z",
      "last_run": {"ts": "2026-05-13T18:42:11Z", "status": "ok"} | null
    }
  ],
  "corruptos": ["foo.yaml: tipo trigger desconocido"]
}
```

---

## `POST /tablero/api/v2/automatizaciones`

Crea una automatización. Body = `Automation` (sin `id` — generado server-side).

**Body**:
```json
{
  "nombre": "Notificar pagos Stripe grandes",
  "activo": false,
  "trigger": {"tipo": "webhook_stripe", "evento": "payment_intent.succeeded", "filtros": {"amount_gte_eur": 100}},
  "acciones": [
    {"tipo": "dia_capturar", "texto": "Pago Stripe {{trigger.amount}}€"},
    {"tipo": "telegram", "mensaje": "💰 {{trigger.amount}}€"}
  ]
}
```

**Response 201**:
```json
{"id": "auto_2026_05_13_notificar_pagos_stripe_grandes", "ok": true}
```

**Response 422**: error Pydantic con `{"errors": [{"loc": [...], "msg": "..."}]}`

---

## `GET /tablero/api/v2/automatizaciones/{id}`

**Response 200**: `Automation` completo.

**Response 404**: `{"error": "not_found"}`

---

## `PUT /tablero/api/v2/automatizaciones/{id}`

Sobreescribe. Body = `Automation`. Conserva `id`, `creado`, `autor`. Actualiza `modificado`.

**Response 200**: `{"ok": true}`

---

## `DELETE /tablero/api/v2/automatizaciones/{id}`

Mueve YAML a `archivadas/`. No borra logs.

**Response 200**: `{"ok": true, "archived_path": "..."}`

---

## `POST /tablero/api/v2/automatizaciones/{id}/run`

Ejecuta manualmente. Body opcional con payload de trigger.

**Body** (opcional):
```json
{"trigger_payload": {"amount": 150, "customer": "test@x.com"}}
```

**Response 200**:
```json
{
  "ok": true,
  "execution_id": "<uuid>",
  "status": "ok",
  "duration_ms": 555,
  "steps": [...]
}
```

---

## `POST /tablero/api/v2/automatizaciones/{id}/test`

Dry run: ejecuta sin efectos externos (Telegram/HTTP/Vault mockeados; respuestas
simuladas). Devuelve detalles de cada paso.

**Body** (opcional): mismo formato que `/run`.

**Response 200**:
```json
{
  "ok": true,
  "dry_run": true,
  "steps": [
    {"n": 1, "action_tipo": "dia_capturar", "would_do": {"texto_resuelto": "Pago Stripe 150€"}, "ok": true},
    {"n": 2, "action_tipo": "telegram", "would_do": {"mensaje_resuelto": "💰 150€", "chat_id": "5752097691"}, "ok": true}
  ]
}
```

---

## `GET /tablero/api/v2/automatizaciones/{id}/logs?date=YYYY-MM-DD`

Devuelve las ejecuciones de un día. Default = hoy.

**Response 200**:
```json
{
  "date": "2026-05-13",
  "items": [<ExecutionLog>, ...]
}
```

---

## `GET /tablero/api/v2/automatizaciones/catalogo`

JSON Schemas de triggers y actions para alimentar el editor visual.

**Response 200**:
```json
{
  "triggers": {
    "cron": {"schema": {...}, "available": true, "label": "Cron (rrule)", "icon": "clock"},
    "webhook_stripe": {"schema": {...}, "available": true, "label": "Webhook Stripe", "icon": "credit-card"},
    "email_match": {"schema": {...}, "available": false, "label": "Email Match", "icon": "mail", "reason": "IMAP no configurado"}
  },
  "actions": {
    "dia_capturar": {"schema": {...}, "available": true, "label": "Capturar nota", "icon": "edit"},
    ...
  }
}
```

---

## `POST /tablero/api/v2/automatizaciones/reload`

Recarga todos los YAML del disco. Útil después de `git pull` o edición manual.

**Response 200**:
```json
{"ok": true, "loaded": 12, "errors": ["foo.yaml: ..."]}
```

---

## `POST /tablero/api/v2/automatizaciones/webhook/stripe`

**No requiere JWT** (Stripe firma con secret).

Header obligatorio: `Stripe-Signature`.

**Response 200**: `{"received": true}`
**Response 401**: firma inválida.
**Response 503**: Stripe webhook no configurado (no hay secret en env).

---

## WS canal `automation`

Cliente:
```json
{"type":"subscribe","channel":"automation"}
```

Servidor (snapshot inicial):
```json
{"type":"snapshot","channel":"automation","payload":{"recent":[{...últimas 10 ejecuciones...}]},"ts":...}
```

Servidor (updates):
```json
{"type":"update","channel":"automation","payload":{"event":"started","automation_id":"...","trigger":{...}},"ts":...}
{"type":"update","channel":"automation","payload":{"event":"step","automation_id":"...","n":1,"ok":true,"duration_ms":120},"ts":...}
{"type":"update","channel":"automation","payload":{"event":"finished","automation_id":"...","status":"ok","duration_ms":555},"ts":...}
{"type":"update","channel":"automation","payload":{"event":"toast","level":"ok","text":"..."},"ts":...}
```
