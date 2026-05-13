# Automation Engine — NosVers · Proyecto 004

Editor visual de automatizaciones tipo *n8n light* sobre la infraestructura
soberana del VPS. Sin Zapier/IFTTT/n8n cloud. Todo local. Vault = source of truth.

> Fase D del roadmap. Spec Kit completo en `specs/automation-engine/specs/004-automation-engine/`.

---

## Arquitectura en una página

```
   ┌──────────────────────────────────────────────────────────────────┐
   │  knowledge_base/automatizaciones/*.yaml  ← source of truth        │
   └─────────────────────────────┬────────────────────────────────────┘
                                 │ load_all() / save() (YAML atómico)
                                 ▼
   ┌──────────────────────────────────────────────────────────────────┐
   │  tablero/v2/automatizaciones/                                    │
   │    motor.py      ← cron_loop 30s + listeners WS                   │
   │    runner.py     ← cadena trigger → acciones (state machine)      │
   │    actions.py    ← 10 actions (telegram, dia_capturar, claude...) │
   │    triggers.py   ← 8 matchers                                     │
   │    rest.py       ← 11 endpoints /tablero/api/v2/automatizaciones/ │
   └─────────────────────────────┬────────────────────────────────────┘
                                 │
                 ┌───────────────┴───────────────┐
                 ▼                               ▼
   ┌─────────────────────┐         ┌──────────────────────────┐
   │ WS broker existente │         │  Cockpit (React)         │
   │ canal "automation"  │ ◄──────►│   Widget #13             │
   │   (nuevo)           │  events │   /cockpit/automatizaciones│
   └─────────────────────┘         └──────────────────────────┘
```

---

## Formato YAML

```yaml
id: auto_2026_05_13_stripe_pago
nombre: Notificar pagos Stripe grandes
autor: angel
creado: 2026-05-13T18:00:00Z
modificado: 2026-05-13T18:00:00Z
activo: true
trigger:
  tipo: webhook_stripe
  evento: payment_intent.succeeded
  filtros:
    amount_gte_eur: 100
acciones:
  - tipo: dia_capturar
    texto: 'Pago Stripe {{trigger.amount}}€ de {{trigger.customer}}'
    etiqueta: auto
  - tipo: telegram
    mensaje: '💰 {{trigger.amount}}€ — {{trigger.customer}} acaba de comprar'
```

- `id`: `auto_<YYYY>_<MM>_<DD>_<slug>` (o `ejemplo_*`).
- `autor`: `angel` | `africa` | `claude`.
- Interpolación: `{{trigger.X}}`, `{{paso_<n>.X}}`, `{{env.VAR}}` (whitelist),
  `{{now}}`, `{{today}}`.

---

## Catálogo

### Triggers (8)

| Tipo | Campos | Notas |
|---|---|---|
| `cron` | `rrule` (croniter) | Tick 30s |
| `webhook_stripe` | `evento`, `filtros.amount_gte_eur` | Requiere `STRIPE_WEBHOOK_SECRET` |
| `nota_capturada` | `filtros.{autor, etiqueta, contenido_regex}` | Vía canal WS `activity` |
| `agente_terminado` | `filtros.{nombre_agente, estado}` | Vía canal WS `agentes` |
| `aegis_alerta` | `filtros.severidad` | Vía canal WS `aegis` |
| `email_match` | `filtros.{from_regex, subject_regex}` | Requiere IMAP (no v1) |
| `voz_keyword` | `keywords[]` | Vía canal WS `activity` (origen=voz) |
| `vps_threshold` | `metrica`, `umbral_pct`, `comparador` | Vía canal WS `health` |

### Actions (10)

| Tipo | Campos clave |
|---|---|
| `dia_capturar` | `texto`, `etiqueta?`, `autor?` |
| `telegram` | `mensaje`, `chat_id?` |
| `ejecutar_agente` | `agente`, `params?` |
| `claude_prompt` | `model`, `system?`, `prompt`, `max_tokens?` |
| `email_enviar` | `to`, `subject`, `body` (requiere SMTP) |
| `webhook_call` | `url`, `method`, `headers?`, `body_json?` |
| `cockpit_toast` | `level`, `text` |
| `wp_post` | `titulo`, `contenido_html`, `status?` |
| `delay` | `segundos` (0.1–300) |
| `condicional` | `expresion`, `acciones_si[]`, `acciones_no[]?` |

Expresiones del nodo `condicional` (parsing seguro sin `eval`):

```
{{trigger.amount}} > 100
{{paso_1.respuesta}} contains "OK"
{{trigger.customer}} matches "@stripe\.com$"
```

Operadores: `> < >= <= == != contains matches`.

---

## Endpoints

```
GET    /tablero/api/v2/automatizaciones                — lista
POST   /tablero/api/v2/automatizaciones                — crear (angel/africa)
GET    /tablero/api/v2/automatizaciones/catalogo       — JSON Schemas
POST   /tablero/api/v2/automatizaciones/reload         — recargar disco
POST   /tablero/api/v2/automatizaciones/webhook/stripe — webhook entrante (firma)
GET    /tablero/api/v2/automatizaciones/{id}           — detalle
PUT    /tablero/api/v2/automatizaciones/{id}           — update
DELETE /tablero/api/v2/automatizaciones/{id}           — archivar
POST   /tablero/api/v2/automatizaciones/{id}/run       — ejecutar manual
POST   /tablero/api/v2/automatizaciones/{id}/test      — dry-run
GET    /tablero/api/v2/automatizaciones/{id}/logs?date= — historial
```

WS canal `automation` (events `started | step | finished | toast`).

---

## Logs

JSONL diario en `knowledge_base/automatizaciones/logs/YYYY-MM-DD.jsonl`.

Una línea por ejecución:

```json
{
  "execution_id": "...", "automation_id": "...",
  "trigger": {"tipo": "cron", "payload": {...}},
  "autor_trigger": "angel", "autor_automation": "angel",
  "started_at": "...", "ended_at": "...", "duration_ms": 555,
  "status": "ok",
  "steps": [{"n": 1, "action_tipo": "dia_capturar", "ok": true, "duration_ms": 120}]
}
```

`status ∈ ok | partial | error | interrupted`.

---

## Operación

**Crear una automatización**:
1. Cockpit → widget #13 → botón `EDITOR`.
2. `+ NUEVA` → arrastrar trigger + acciones → conectar.
3. Click en nodo → form lateral con campos según el JSON Schema.
4. `TEST RUN` con payload mock → ver paso a paso.
5. `GUARDAR`. Toggle `ACTIVO` ON.

**Recargar tras editar a mano un YAML**:
```bash
curl -s -X POST http://localhost:9000/tablero/api/v2/automatizaciones/reload \
  -H "Authorization: Bearer $TOKEN"
```

**Ver logs de hoy**:
```bash
curl -s "http://localhost:9000/tablero/api/v2/automatizaciones/<id>/logs" \
  -H "Authorization: Bearer $TOKEN" | jq
```

---

## Troubleshooting

| Síntoma | Causa probable | Fix |
|---|---|---|
| YAML aparece como "corrupto" | tipo trigger/action desconocido, campos extras | Validar contra `/catalogo` |
| Telegram no dispara | `TELEGRAM_TOKEN` o `chat_id` faltante | Comprobar `.env`; default ANGEL_CHAT_ID |
| Stripe webhook 401 | Firma inválida | Comprobar `STRIPE_WEBHOOK_SECRET` y reloj sincronizado |
| Cron no se dispara | `activo: false` o rrule mal | Validar con croniter; activar |
| `ejecutar_agente` timeout | Agente tarda más de 60s | Ajustar `AGENTE_TIMEOUT_S` o dividir tarea |
| Acción individual falla | Ver log JSONL; sigue la cadena salvo condicional | Inspeccionar `step.error` |

---

## Ejemplos pre-cargados (todos con `activo: false`)

- `ejemplo_stripe_pago_grande.yaml` — webhook Stripe ≥100€ → captura + telegram + toast.
- `ejemplo_lunes_agt05.yaml` — cron lunes 9h → `ejecutar_agente agt05_africa`.
- `ejemplo_voz_urgente.yaml` — dictado contiene `urgente` → telegram + nota etiqueta `urgente`.

Para activar: editor → click toggle → confirmar.

---

## Pulido del cockpit (T091–T096)

- ✓ 7 workers verificados publican datos (health, claude, agentes, revenue, aegis, wake, activity).
- ✓ Reconexión WS con backoff exponencial 1s→30s (`useWebSocket.ts`).
- ✓ Loading skeletons en widgets antes del primer tick (VpsHealth, Revenue, Automations).
- ✓ Tooltips en gauges/sparklines mostrando valor exacto.
- ✓ Sonido opcional toast Stripe: `/public/sounds/cha-ching.mp3` con fallback WebAudio beep.
- ✓ Atajos teclado: `?` modal, `g h/r/c` scroll a widget, `g a` automatizaciones.

---

## Dev / tests

```bash
# backend
cd /home/nosvers && pytest tablero/tests/ -q

# frontend
cd /home/nosvers/tablero/web && npm run build
```

Tests del proyecto 004: 57 (models + storage + interp + cond + actions + triggers + runner + webhooks).
Total tablero: 196 — zero regresiones.
