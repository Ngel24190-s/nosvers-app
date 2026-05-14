# Implementation Plan — Fase 2 + 3 (006)

**Feature**: `006-claudio-voz-cockpit`
**Created**: 2026-05-14
**Status**: Ready for tasks

---

## Decisión central: dos paquetes pequeños y un endpoint

- `voz/intent_router.py` — sync `route_intent` + cache + prompt loader
- `voz/compose_voice_response.py` — pure templates
- `voz/rest.py` — añade un handler `dictado_procesar_handler` (no nuevo módulo)

Nada se mete dentro de `mcp_server.py`. Los 22 tools de Fase 1 ya están
disponibles importando desde `claudio_tools.*`. El router los invoca
directamente; no pasa por MCP RPC (más rápido, menos puntos de fallo).

`dia_capturar` fallback se invoca con `voz.capturar.dia_capturar_impl`.

---

## Stack

| Componente | Tecnología |
|---|---|
| Intent router | Python 3, `requests` (ya presente), `hashlib`, `OrderedDict` LRU |
| Endpoint | Starlette (ya montado), JSON |
| Compose response | stdlib puro |
| Workers | asyncio + `claudio_tools` lectura |
| Widgets | React 18 + framer-motion + tremor + lucide-react (ya presentes) |
| Tests | pytest + monkeypatch (ya configurado) |

Cero deps nuevas Python ni npm.

---

## Estructura de archivos a tocar

### Nuevos

```
voz/
├── intent_router.py
└── compose_voice_response.py

public_html/knowledge_base/prompts/
└── intent_router.md

public_html/knowledge_base/claudio/
├── INTENT_ROUTER.md       ← documentación para futuros tools
└── logs/                  ← ya existe — el endpoint añade dictado-*.jsonl

tablero/v2/workers/
├── recordatorios.py
├── gastos.py
├── compras.py
├── medicacion.py
├── coche.py
├── menu_dia.py
└── bris.py

tablero/web/src/components/cockpit/
├── RecordatoriosWidget.tsx
├── GastosMesWidget.tsx
├── ComprasWidget.tsx
├── MedicacionWidget.tsx
├── CocheStatusWidget.tsx
├── MenuHoyWidget.tsx
└── BrisWidget.tsx

tests/
└── test_intent_router.py
```

### Modificados

```
voz/rest.py                     ← +1 ruta y handler
tablero/v2/ws.py                ← +7 canales en VALID_CHANNELS
tablero/v2/workers/__init__.py  ← register_all() extendido
tablero/web/src/hooks/useWebSocket.ts          ← +7 en CockpitChannel
tablero/web/src/hooks/useCockpitLayout.ts      ← +7 en WidgetId + DEFAULT_LAYOUT
tablero/web/src/pages/Cockpit.tsx              ← +7 <div key=...>
```

---

## Contratos exactos

### `voz/intent_router.py`

```python
from dataclasses import dataclass

@dataclass
class IntentResult:
    tool: str            # "gasto_anotar" | ... | "dia_capturar"
    args: dict           # primitivos
    confidence: float    # 0..1
    fallback: bool       # True si caímos por baja confidence o tool inválido
    razon: str           # debug
    modelo: str          # "claude-haiku-4-5" | "fallback"

# whitelist tools de Fase 1 + dia_capturar
ALLOWED_TOOLS: set[str] = {
    "claudio_recordar", "claudio_contexto",
    "recordatorio_crear", "recordatorios_listar", "recordatorio_completar",
    "familia_cumpleanos_listar",
    "gasto_anotar", "gastos_resumen", "recurrente_alertar",
    "lista_compras_añadir", "lista_compras_ver", "lista_compras_completar",
    "despensa_estado",
    "menu_sugerir", "receta_guardar",
    "coche_estado", "coche_evento",
    "documento_anotar", "documentos_buscar",
    "medicacion_recordar", "cita_medica_anotar",
    "casa_mantenimiento_anotar",
    # fallback
    "dia_capturar",
}

DEFAULT_THRESHOLD: float = 0.6
DEFAULT_TIMEOUT_S: float = 3.0
DEFAULT_MODEL: str = "claude-haiku-4-5"

async def route_intent(text: str, autor: str,
                       threshold: float = DEFAULT_THRESHOLD,
                       timeout: float = DEFAULT_TIMEOUT_S) -> IntentResult: ...
```

Cache: módulo-level `OrderedDict` con `_get_cached`, `_set_cached`,
respectando TTL 5 s y maxsize 64.

### `voz/compose_voice_response.py`

```python
def compose_voice_response(tool: str, args: dict, result: str,
                           autor: str = "") -> str:
    """Templates por tool. Pure. < 5ms."""
```

Catálogo de templates (resumido, completo en código):
| tool | template |
|---|---|
| gasto_anotar | `"Apuntado, {concepto} {monto} euros. Llevas {total} euros este mes."` |
| recordatorio_crear | `"Hecho, {fecha_legible} te aviso de {texto}."` |
| lista_compras_añadir | `"{item} añadido a la lista. Llevas {n} cosas."` |
| lista_compras_completar | `"Marcado: {item}."` |
| coche_evento | `"{tipo} apuntado en el coche, {fecha_legible}."` |
| documento_anotar | `"Documento guardado: {tipo} de {fuente}, {fecha_legible}."` |
| cita_medica_anotar | `"Cita médica anotada: {quien} con {especialista}, {fecha_legible}."` |
| medicacion_recordar | (devuelve el string del tool directamente — ya es legible) |
| dia_capturar | `"Apuntado en notas."` |
| ... | ... |

Fallback genérico: `"Hecho."`

### `voz/rest.py` — nuevo handler

```python
async def dictado_procesar_handler(request: Request) -> JSONResponse:
    payload = await _autenticar(request)
    if not payload:
        return _json({"ok": False, "error": "auth_invalido"}, 401)
    autor_jwt = payload.get("sub") or "angel"
    device = payload.get("device", "desconocido")

    data = await request.json()
    transcript = (data.get("transcript") or "").strip()
    if not transcript:
        return _json({"ok": False, "error": "input_vacio"}, 400)

    t0 = time.monotonic()
    intent = await route_intent(transcript, autor_jwt)
    tool_result = _execute_intent(intent, transcript, autor_jwt)
    voice = compose_voice_response(intent.tool, intent.args, tool_result, autor_jwt)
    latency_ms = int((time.monotonic() - t0) * 1000)

    _log_dictado(autor=autor_jwt, transcript=transcript, intent=intent,
                 tool_result=tool_result, latency_ms=latency_ms, device=device)

    return _json({
        "ok": True,
        "intent": {"tool": intent.tool, "args": intent.args,
                   "confidence": intent.confidence, "fallback": intent.fallback},
        "tool_result": tool_result,
        "voice_response": voice,
        "latency_ms": latency_ms,
    })
```

`_execute_intent` mapa nombre → callable de `claudio_tools` o
`voz.capturar.dia_capturar_impl`. Inyecta `autor=autor_jwt` siempre que el
tool lo acepte.

### Worker pattern (ejemplo `gastos.py`)

```python
"""Worker gastos: lee finanzas/gastos/YYYY-MM.md + mes anterior."""
from __future__ import annotations
from datetime import date, timedelta

from claudio_tools.common import vault
from claudio_tools import finanzas as _fin   # para acceder al parser interno


async def gastos_tick() -> dict | None:
    hoy = date.today()
    mes = hoy.strftime("%Y-%m")
    prev = (hoy.replace(day=1) - timedelta(days=1)).strftime("%Y-%m")

    by_cat, total = _read_mes(mes)
    _, total_prev = _read_mes(prev)

    if total == 0 and total_prev == 0:
        return {"empty": True}
    return {
        "mes": mes,
        "total_mes_eur": round(total, 2),
        "por_categoria": {k: round(v, 2) for k, v in by_cat.items()},
        "delta_vs_anterior_eur": round(total - total_prev, 2),
        "n_apuntes": sum(1 for _ in _iter_lineas(mes)),
    }
```

Cada worker es similar: parsea su área del vault, devuelve dict. El broker
solo broadcasts si el dict cambió.

### Widget pattern (ejemplo `GastosMesWidget.tsx`)

```tsx
import { useEffect, useState } from 'react';
import { Wallet } from 'lucide-react';
import { WidgetCard } from './WidgetCard';
import type { UseWebSocketReturn } from '../../hooks/useWebSocket';

interface GastosPayload {
  mes: string;
  total_mes_eur: number;
  por_categoria: Record<string, number>;
  delta_vs_anterior_eur: number;
  n_apuntes: number;
  empty?: boolean;
}

export function GastosMesWidget({ ws, index }: { ws: UseWebSocketReturn; index: number }) {
  const [data, setData] = useState<GastosPayload | null>(null);
  useEffect(() => ws.subscribe('gastos', (p) => setData(p as GastosPayload)), [ws]);

  return (
    <WidgetCard title="GASTOS MES" icon={<Wallet size={14} />} accent="amber" index={index}>
      {/* render */}
    </WidgetCard>
  );
}
```

---

## WS channel additions

`tablero/v2/ws.py`:

```python
VALID_CHANNELS = {
    "health", "claude", "activity", "agentes", "revenue", "aegis", "wake",
    "automation",
    # 006: familia/admin
    "recordatorios", "gastos", "compras", "medicacion", "coche", "menu_dia", "bris",
}
```

`useWebSocket.ts`:

```ts
export type CockpitChannel =
  | 'health' | 'claude' | 'activity' | 'agentes' | 'revenue' | 'aegis'
  | 'wake' | 'automation'
  | 'recordatorios' | 'gastos' | 'compras' | 'medicacion' | 'coche'
  | 'menu_dia' | 'bris';
```

---

## Prompt del router (vault)

`public_html/knowledge_base/prompts/intent_router.md`:

```markdown
---
nombre: intent_router
modelo: claude-haiku-4-5
version: 1
threshold: 0.6
---

# Prompt: Intent Router de Claudio

Eres el router de intents de Claudio (mayordomo digital familiar).
Recibes un texto dictado por Angel o África y debes elegir UN tool MCP
que ejecute lo que el dictante quiere.

Devuelve EXCLUSIVAMENTE un JSON con esta forma:

{"tool": "<nombre>", "args": {...}, "confidence": <0..1>, "razon": "<<=12 palabras>"}

Tools disponibles:

| tool | qué hace | args clave |
|---|---|---|
| gasto_anotar | apunta un gasto | monto_eur, concepto, categoria |
| recordatorio_crear | crea un recordatorio fechado | texto, fecha, prioridad |
| ... |

Reglas:
- Si el texto menciona pagar/comprar/pedir + cantidad + concepto, usa gasto_anotar
- Si menciona "recuérdame", "no olvides", "apunta para X día", usa recordatorio_crear
- Si menciona "apunta X a la lista" o "compra X", usa lista_compras_añadir
- Si dice "qué hay en X", "busca X", usa documentos_buscar o dia_buscar
- Si es ambiguo (< 0.6 confianza), pon dia_capturar como tool
- NO incluyas el campo `autor`; eso lo inyecta el servidor.
- Categorías válidas para gastos: alimentacion, transporte, coche, hogar, ocio, salud, nosvers, ropa, regalos, viajes, otros
- Fechas: usa "hoy", "mañana" o YYYY-MM-DD; si no se especifica, "hoy"

NO añadas texto antes ni después del JSON. NO uses markdown.
```

---

## Logging

`public_html/knowledge_base/claudio/logs/dictado-YYYY-MM-DD.jsonl`:

```json
{"ts": "...", "autor": "angel", "transcript_len": 27, "intent": {"tool": "gasto_anotar", "confidence": 0.94}, "args": {"monto_eur": 45, "concepto": "gasolina", "categoria": "transporte"}, "ok": true, "latency_ms": 920, "device": "pwa-android"}
```

Transcript completo solo si `CLAUDIO_DICTADO_LOG_FULL=1`.

---

## Restart + verificación

```bash
# 1. Build frontend
cd /home/nosvers/tablero/web && npm run build

# 2. Mata dev_server si existe
pkill -f "tablero/scripts/dev_server" || true

# 3. Arranca con setsid (sobrevive a salir del shell)
cd /home/nosvers
setsid env TABLERO_DEV=1 MCP_TOKEN="$MCP_TOKEN" VOZ_JWT_SECRET="$VOZ_JWT_SECRET" \
    python3 tablero/scripts/dev_server.py \
    > /tmp/dev_server_fase23.log 2>&1 < /dev/null &

# 4. Espera 2s y verifica logs
sleep 2
tail -20 /tmp/dev_server_fase23.log

# 5. Smoke test del endpoint
TOKEN=$(python3 -c "from voz.auth import emitir_token; print(emitir_token('test-fase23','angel')['jwt'])")
curl -s -X POST http://127.0.0.1:8766/voz/api/dictado-procesar \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"transcript":"he pagado 45 de gasolina"}'
```

---

## Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| Anthropic rate-limit o timeout | Timeout 3s + fallback a `dia_capturar` |
| JSON corrupto del modelo | Try/except parse → fallback genérico |
| Tool de Fase 1 lanza excepción | Capturado, `voice_response` = "Hubo un error, lo apunto como nota." + `dia_capturar` |
| WS channel typo | tipo `CockpitChannel` + `VALID_CHANNELS` se validan en build |
| Latencia >1.5s | Logueado por request; si pasa de 3 s, considerar mover a un servicio dedicado |
| Cache idempotente nunca expira (memory leak) | LRU 64 entradas; TTL chequeado en cada get |
| Vault path absoluto en workers | usa `claudio_tools.common.vault()` (env override OK) |

---

## Plan de commits (8)

1. `feat(006-spec): spec + clarify + plan + tasks Fase 2+3`
2. `feat(006-router): voz/intent_router.py + prompt en vault`
3. `feat(006-tts): voz/compose_voice_response.py + templates 22 tools`
4. `feat(006-endpoint): /voz/api/dictado-procesar + logging dictado`
5. `feat(006-workers): 7 workers familia/admin + register_all`
6. `feat(006-widgets): 7 widgets React cockpit + layout extension`
7. `test(006-router): test_intent_router.py 20+ casos`
8. `docs(006): INTENT_ROUTER.md + actualizar MEMORY`
