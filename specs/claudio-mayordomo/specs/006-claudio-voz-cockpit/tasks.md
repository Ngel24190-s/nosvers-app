# Tasks — Claudio Fase 2+3 (006)

Marcadores: `[ ]` pending · `[~]` in progress · `[x]` done · `[!]` blocker

---

## Bloque A — Intent Router (T100)

- [ ] **T101** Crear `public_html/knowledge_base/prompts/intent_router.md`
  con frontmatter + cuerpo (22 tools + reglas).
- [ ] **T102** `voz/intent_router.py`:
  - `IntentResult` dataclass
  - `ALLOWED_TOOLS` whitelist
  - `_load_prompt()` con fallback hardcoded
  - `_post_haiku()` (igual patrón clasificar.py)
  - `_cache_lookup` / `_cache_set` LRU 64 / TTL 5s
  - `route_intent(text, autor, threshold, timeout) -> IntentResult` (async)

## Bloque B — Compose voice response (T110)

- [ ] **T111** `voz/compose_voice_response.py`:
  - Templates por tool (22 entries + dia_capturar + genérico)
  - Helper `_fecha_legible(s)` (hoy/mañana/DD de mes)
  - Función `compose_voice_response(tool, args, result, autor)`

## Bloque C — Endpoint (T120)

- [ ] **T121** Extender `voz/rest.py`:
  - Importar `route_intent`, `compose_voice_response`, `dia_capturar_impl`,
    + claudio_tools por dominio
  - `_execute_intent(intent, transcript, autor) -> str`
  - `_log_dictado(...)`
  - Handler `dictado_procesar_handler`
  - Añadir Route `/voz/api/dictado-procesar` (POST + OPTIONS)

## Bloque D — Workers (T130)

- [ ] **T131** `tablero/v2/workers/recordatorios.py` (30 s)
- [ ] **T132** `tablero/v2/workers/gastos.py` (60 s)
- [ ] **T133** `tablero/v2/workers/compras.py` (30 s)
- [ ] **T134** `tablero/v2/workers/medicacion.py` (60 s)
- [ ] **T135** `tablero/v2/workers/coche.py` (300 s)
- [ ] **T136** `tablero/v2/workers/menu_dia.py` (600 s)
- [ ] **T137** `tablero/v2/workers/bris.py` (300 s)
- [ ] **T138** Extender `VALID_CHANNELS` en `tablero/v2/ws.py`.
- [ ] **T139** Extender `register_all()` en `tablero/v2/workers/__init__.py`.

## Bloque E — Widgets React (T140)

- [ ] **T141** `RecordatoriosWidget.tsx`
- [ ] **T142** `GastosMesWidget.tsx`
- [ ] **T143** `ComprasWidget.tsx`
- [ ] **T144** `MedicacionWidget.tsx`
- [ ] **T145** `CocheStatusWidget.tsx`
- [ ] **T146** `MenuHoyWidget.tsx`
- [ ] **T147** `BrisWidget.tsx`
- [ ] **T148** Extender `CockpitChannel` en `useWebSocket.ts`.
- [ ] **T149** Extender `WidgetId` + `DEFAULT_LAYOUT` en `useCockpitLayout.ts`.
- [ ] **T14A** Importar y montar los 7 widgets en `Cockpit.tsx`.

## Bloque F — Tests (T150)

- [ ] **T151** `tests/test_intent_router.py` con monkeypatch de `requests.post`
  cubriendo:
  - gastos básico
  - gastos sin categoría → default `otros`
  - recordatorio relativo "mañana"
  - lista compras
  - busca documento
  - cita médica
  - coche evento
  - menú sugerir
  - confidence baja → fallback
  - tool fuera whitelist → fallback
  - JSON corrupto → fallback
  - timeout → fallback
  - texto vacío → fallback
  - dictado idempotente (mismo text + autor en 5s)
  - autor africa propagado
  - misc 5+ casos

## Bloque G — Build + restart + verify (T160)

- [ ] **T161** `cd tablero/web && npm run build`
- [ ] **T162** Restart dev_server con `setsid`, log a
  `/tmp/dev_server_fase23.log`
- [ ] **T163** Curl smoke al endpoint con un transcript de prueba

## Bloque H — Docs + commits (T170)

- [ ] **T171** `public_html/knowledge_base/claudio/INTENT_ROUTER.md` con
  pasos para añadir un tool al router.
- [ ] **T172** Commits agrupados (~8) conventional.
