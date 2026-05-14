# Feature Specification: Claudio Evolution — Fase 2 + 3 (combinadas)

**Feature Branch**: `006-claudio-voz-cockpit`
**Created**: 2026-05-14
**Status**: Approved — implementation autorisée sin parar
**Input**: `BRIEF_FASE_23.md` + Fase 1 cerrada (005)

---

## Overview

Cierra el ciclo voz → tool → vault → cockpit. Hasta ahora Claudio entendía
hechos por Telegram y por nota dictada (clasificación libre), pero no
*ejecutaba* tools desde voz, y los widgets del cockpit no veían el dominio
familiar. Esta fase une los dos hilos:

- **Fase 2** — Intent router: el dictado de Angel/África entra por
  `/voz/api/dictado-procesar`, un módulo nuevo `voz/intent_router.py`
  decide cuál de los 22 tools MCP de Fase 1 ejecutar, lo invoca
  síncronamente, y devuelve la respuesta hablada lista para TTS local.
- **Fase 3** — Cockpit familiar: 7 workers nuevos publican en canales WS
  dedicados, 7 widgets React los pintan con glassmorphism oscuro. El
  layout default extiende el grid existente (12 widgets) a 19.

Las dos juntas habilitan el **wow loop**: dicto algo → Claudio lo apunta →
medio segundo después el widget refleja el cambio.

---

## Principios no-negociables (heredados del BRIEF y 005)

1. **Latencia primero**: el dictado debe sentirse instantáneo. Objetivo
   ≤ 1.5 s desde fin del dictado hasta inicio del TTS local.
2. **Fallback seguro**: si el router duda (confidence < 0.6) o el tool falla,
   el dictado cae a `dia_capturar` (nota normal). Nunca silencio.
3. **Soberanía**: el modelo Haiku se consulta directamente vía Anthropic
   API; nada se externaliza más allá de eso. Los workers solo leen vault local.
4. **Speaker ID viene del JWT**: el router recibe `autor` desde `sub` del
   token. El cliente no puede inyectarlo.
5. **No romper Fase 1**: los 22 tools, el bot Telegram, los endpoints voz
   existentes (`/voz/api/capturar`, `/voz/api/contexto`, `/voz/api/buscar`)
   siguen funcionando idénticos.
6. **No romper cockpit existente**: los 12 widgets actuales intactos. WS
   broker añade canales nuevos sin tocar los viejos.

---

## User Scenarios

### US-1 — Gasto por voz (P0)

Angel dicta: "He pagado 45 de gasolina."
→ PWA transcribe local (faster-whisper) → POST `/voz/api/dictado-procesar`
con JWT `sub=angel`.
→ Router (Haiku) decide `gasto_anotar(45, "gasolina", "transporte", "angel")`.
→ Tool ejecuta, devuelve string humano.
→ Endpoint compone `voice_response`: "Apuntado, gasolina 45 euros. Llevas
287 euros de transporte este mes."
→ PWA reproduce TTS local con piper-tts.
→ A los 60 s el cockpit refresca el widget `GastosMes` con la categoría
transporte actualizada.

### US-2 — Recordatorio por voz (P0)

África dicta: "Recuérdame mañana a las 6 llevar a Bris al veterinario."
→ Router: `recordatorio_crear("llevar a Bris al veterinario", "mañana",
"africa", 5)`.
→ Tool crea el .md en `familia/recordatorios/`.
→ TTS: "Hecho, mañana 18 horas te aviso de llevar a Bris al veterinario."
→ Widget `Recordatorios` muestra la card en hasta 30 s.

### US-3 — Compras por voz (P0)

Angel dicta: "Apunta leche y huevos a la lista."
→ Router devuelve un único call con item="leche, huevos" o dos calls
encadenados (decisión en clarify.md).
→ TTS: "Añadidos a la lista. Llevas 7 items pendientes."
→ Widget `Compras` refresca a los 30 s.

### US-4 — Consulta dominio (P1)

Angel: "¿Qué hay en el huerto?"
→ Router decide `dia_buscar(query="huerto")` (tool ya existente fuera de
Fase 1 — el router lo conoce).
→ TTS: respuesta con resumen 1 línea.

### US-5 — Captura como nota (fallback, P0)

Angel: "Me ha gustado mucho hablar contigo esta tarde."
→ Router devuelve `confidence < 0.6` → fallback a `dia_capturar(texto)`.
→ TTS: "Apuntado en notas."

### US-6 — Cockpit familia (P0)

Angel abre `/cockpit`. En la pantalla, además de los 12 widgets actuales,
aparecen 7 cards nuevas: Recordatorios, Gastos Mes, Compras, Medicación,
Coche, Menú Hoy, Bris. Cada una muestra datos reales si el vault los tiene,
o un estado vacío elegante si no.

### US-7 — Interacción optimista (P1)

En el cockpit, Angel marca un recordatorio como hecho con un click. La UI
lo tacha inmediatamente; en background llama al tool MCP
`recordatorio_completar(slug)`. Si falla, revierte y muestra toast.

### US-8 — Idempotencia dictado (P1)

Si el mismo transcript (texto + autor) llega 2 veces en menos de 5 s
(red flaky o doble tap), la segunda llamada devuelve el resultado cacheado
y NO ejecuta el tool dos veces.

---

## Functional Requirements

### Intent Router (`voz/intent_router.py`)

**FR-IR-1** Función pública `async route_intent(text, autor) -> IntentResult`.
**FR-IR-2** Usa Claude Haiku (modelo configurable, default
`claude-haiku-4-5`).
**FR-IR-3** El prompt vive en
`public_html/knowledge_base/prompts/intent_router.md` (editable sin
redeploy, igual que `clasificar_nota.md`).
**FR-IR-4** El prompt enumera los 22 tools con descripción 1-línea y
firma de args, indica el formato JSON esperado.
**FR-IR-5** Confidence threshold por defecto **0.6**. Configurable en
módulo. Si confidence < threshold → `IntentResult(fallback=True)`.
**FR-IR-6** Tool name fuera del whitelist → fallback.
**FR-IR-7** Timeout API: 3 s. Si timeout → fallback.
**FR-IR-8** Idempotencia: cache LRU 64 entradas, TTL 5 s, key
`(sha256(text)[:16], autor)`.

### Endpoint `/voz/api/dictado-procesar`

**FR-EP-1** `POST /voz/api/dictado-procesar`, JSON body, JWT obligatorio.
**FR-EP-2** Body válido: `{"transcript": str, "audio_duration_s": float?,
"device": str?}`.
**FR-EP-3** Respuesta exitosa:
```json
{
  "ok": true,
  "intent": {"tool": "...", "args": {...}, "confidence": 0.x,
             "fallback": false},
  "tool_result": "...",        // string crudo del tool
  "voice_response": "...",     // texto humano para TTS
  "latency_ms": 920
}
```
**FR-EP-4** Si JWT inválido → 401 `{"ok":false, "error":"auth_invalido"}`.
**FR-EP-5** Si transcript vacío → 400 `{"ok":false, "error":"input_vacio"}`.
**FR-EP-6** Log por llamada en
`public_html/knowledge_base/claudio/logs/dictado-YYYY-MM-DD.jsonl`:
`{ts, autor, transcript_len, intent, args, ok, latency_ms, device}`. El
transcript completo no se loguea por defecto (privacidad); flag env
`CLAUDIO_DICTADO_LOG_FULL=1` lo habilita.
**FR-EP-7** CORS coherente con los endpoints existentes
(`Access-Control-Allow-Origin: https://voz.nosvers.com`).

### Compose voice response (`voz/compose_voice_response.py`)

**FR-CVR-1** Función pura
`compose_voice_response(tool, args, result, autor) -> str`. Sin LLM.
**FR-CVR-2** Templates por tool, 22 tools cubiertos.
**FR-CVR-3** Si tool no tiene template, fallback genérico tipo "Hecho."
**FR-CVR-4** Latencia objetivo < 5 ms.

### Workers nuevos (`tablero/v2/workers/`)

7 workers nuevos: `recordatorios`, `gastos`, `compras`, `medicacion`,
`coche`, `menu_dia`, `bris`.

**FR-W-1** Cada worker es `async def <name>_tick() -> dict | None`.
**FR-W-2** Lee del vault con paths bajo `claudio_tools.common.vault()`.
**FR-W-3** Devuelve `None` si no hay cambios respecto al último tick
(o un dict si los datos cambiaron — el broker lo decide).
**FR-W-4** Si el directorio del vault está vacío, devuelve dict con
`{"empty": true}` (no error).
**FR-W-5** Intervals:
| worker | intervalo |
|---|---|
| recordatorios | 30 s |
| gastos | 60 s |
| compras | 30 s |
| medicacion | 60 s |
| coche | 300 s |
| menu_dia | 600 s |
| bris | 300 s |
**FR-W-6** Canales WS añadidos a `VALID_CHANNELS`: `recordatorios`,
`gastos`, `compras`, `medicacion`, `coche`, `menu_dia`, `bris`.
**FR-W-7** `register_all()` los registra junto con los 6 actuales.

### Widgets React (`tablero/web/src/components/cockpit/`)

7 widgets nuevos siguiendo el patrón `WidgetCard` + `useWebSocket`:

| componente | canal | tamaño default |
|---|---|---|
| `RecordatoriosWidget` | recordatorios | 6×4 |
| `GastosMesWidget` | gastos | 6×4 |
| `ComprasWidget` | compras | 3×4 |
| `MedicacionWidget` | medicacion | 3×4 |
| `CocheStatusWidget` | coche | 3×4 |
| `MenuHoyWidget` | menu_dia | 3×4 |
| `BrisWidget` | bris | 3×4 |

**FR-WG-1** Cada widget usa `<WidgetCard>` con accent del color de NosVers.
**FR-WG-2** Cada uno se suscribe al canal vía `ws.subscribe(...)`.
**FR-WG-3** Estado vacío elegante (no error) si payload llega
`{"empty": true}`.
**FR-WG-4** Interacciones de marcado optimistas (FR-IO-1, abajo).

### Interacciones optimistas (cockpit → MCP)

**FR-IO-1** Marcar recordatorio o item compras llama a un endpoint REST
ligero (ya cubierto por MCP — el cliente llama un nuevo
`/tablero/api/v2/action` que internamente delega al tool MCP). UI revierte
con toast si la acción falla.

> **Nota implementación**: este endpoint quedará como TODO blando para
> esta fase si rompe el budget de tiempo. La UI puede empezar siendo
> read-only y añadir interacciones en una iteración siguiente. Documentar
> en INTENT_ROUTER.md.

### Frontend voz (PWA + Linux dictado)

**FR-PWA-1** El dictado existente, tras transcripción local, llama a
`/voz/api/dictado-procesar` en lugar de (o además de) `/voz/api/capturar`.
**FR-PWA-2** Si la respuesta trae `voice_response`, se reproduce con TTS
local (piper-tts ya disponible).
**FR-PWA-3** Si el endpoint falla, fallback a `/voz/api/capturar` (flujo
actual). Cero pérdida.

### Layout cockpit

**FR-LAY-1** `useCockpitLayout.ts` añade los 7 widgets nuevos al
`DEFAULT_LAYOUT` y al type `WidgetId`.
**FR-LAY-2** Las filas familia/admin se insertan después de los 12
widgets actuales (no se mueven los existentes — preserva layouts
guardados en localStorage).
**FR-LAY-3** Layout default:
- Fila 5 (familia): Recordatorios(6) | Compras(3) | MenuHoy(3)
- Fila 6 (admin): GastosMes(6) | Coche(3) | Medicación(3)
- Fila 7: Bris(3) [flotante en esquina inferior derecha]

---

## Non-functional Requirements

- **NFR-1** Cero deps Python nuevas. `requests` + `anthropic` (vía REST,
  igual que clasificar.py) bastan.
- **NFR-2** Cero deps npm nuevas. Reutiliza `framer-motion`, `lucide-react`,
  `@tremor/react` ya presentes.
- **NFR-3** Latencia objetivo end-to-end: 1.5 s (transcript → TTS).
  Router puro: 800 ms p50 con Haiku.
- **NFR-4** Tests del router: 20+ casos cubriendo gastos, recordatorios,
  compras, salud, coche, menú, fallback de baja confidence, fallback por
  tool fuera de whitelist, parsing JSON corrupto. Usan
  `monkeypatch` para no llamar a Anthropic real (mock de la respuesta).
- **NFR-5** Logs del dictado privacy-aware: por defecto solo metadata.
- **NFR-6** Bug telegram_enviar conocido: ningún componente de esta fase
  llama a `telegram_enviar` durante el trabajo. Telegram solo al final
  (regla memoria).
- **NFR-7** WS workers cumplen patrón "broadcast sólo si cambia" para
  no saturar conexiones.

---

## Out of Scope (Fase 4+)

- OCR de PDFs/fotos de facturas
- Integraciones externas (weather, mapas, Spotify, Home Assistant)
- Pro-actividad / supervisor autónomo
- Modo niños
- Comando complejo multi-tool en un dictado (ej. "apunta el gasto Y
  recuérdame mañana") — esta fase soporta 1 tool por turno

---

## Definition of Done

- [ ] `voz/intent_router.py` con `route_intent(text, autor)` + 22 tools en prompt
- [ ] `public_html/knowledge_base/prompts/intent_router.md` editable
- [ ] `voz/compose_voice_response.py` con templates 22 tools
- [ ] `voz/rest.py` extendido con `/voz/api/dictado-procesar`
- [ ] 7 workers nuevos en `tablero/v2/workers/` publicando en sus canales
- [ ] `VALID_CHANNELS` en `tablero/v2/ws.py` extendido con 7 canales
- [ ] `register_all()` registra los 13 workers (6 + 7)
- [ ] 7 widgets React en `tablero/web/src/components/cockpit/`
- [ ] `Cockpit.tsx` monta los 7 widgets nuevos
- [ ] `useCockpitLayout.ts` actualiza tipo + DEFAULT_LAYOUT
- [ ] `useWebSocket.ts` extiende `CockpitChannel`
- [ ] `tests/test_intent_router.py` con 20+ casos verde
- [ ] Build frontend (`npm run build`) verde
- [ ] Restart dev_server con `setsid` y verificación end-to-end
- [ ] `claudio/INTENT_ROUTER.md` documentando cómo añadir tools
- [ ] Commits agrupados conventional (~8 commits)
