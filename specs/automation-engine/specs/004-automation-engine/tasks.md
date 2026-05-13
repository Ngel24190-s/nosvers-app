# Tasks — Automation Engine (004)

**Estado global**: pending hasta `/speckit-implement`.

Marcadores:
- `[ ]` pending · `[~]` in progress · `[x]` done · `[!]` blocker

Cada tarea ID = `T0NN`. Bloques: Storage (T010), Motor (T020), Actions/Triggers (T030),
API REST (T040), Editor visual (T050), Widget cockpit (T060), Pulido cockpit (T070),
Ejemplos + tests + docs (T080).

---

## Bloque 0 — Setup (T000)

- [ ] **T001** Añadir deps backend a `unified-agent/requirements.txt` y al
  entorno venv del MCP: `croniter>=2.0`, `aiofiles`, `stripe` (opcional).
- [ ] **T002** Añadir deps frontend en `tablero/web/package.json`:
  `reactflow`, `@monaco-editor/react`. `npm install`.
- [ ] **T003** Crear directorio `knowledge_base/automatizaciones/` con
  subdirs `archivadas/` y `logs/`. `chmod 755`.

---

## Bloque 1 — Storage + Models (T010)

- [ ] **T011** Crear `tablero/v2/automatizaciones/__init__.py`.
- [ ] **T012** Crear `tablero/v2/automatizaciones/models.py` con `Automation`,
  Trigger union (8 tipos), Action union (10 tipos). Validators con `croniter`
  para `CronTrigger.rrule`. Forward-refs resueltas para `CondicionalAction`.
- [ ] **T013** Crear `tablero/v2/automatizaciones/storage.py`:
  `load_all()`, `load_one(id)`, `save(automation)`, `delete(id)`,
  `archive(id)`. Atomic write con `tablero.v2.atomic_write`.
- [ ] **T014** Crear `tablero/v2/automatizaciones/catalogo.py`: función
  `build_catalog()` que genera `{triggers, actions}` con `model_json_schema()`
  + `available` flag por env (STRIPE_WEBHOOK_SECRET, SMTP_HOST, IMAP_HOST).
- [ ] **T015** Test unit `tests/test_v2_automatizaciones_models.py`:
  round-trip YAML para cada tipo, rechazo de campos extras, validación cron.
- [ ] **T016** Test unit `tests/test_v2_automatizaciones_storage.py`: write/read/
  list/archive, ids duplicados rechazados.

---

## Bloque 2 — Interpolación + DSL condicional (T020)

- [ ] **T021** Crear `tablero/v2/automatizaciones/interpolation.py`:
  `resolve(template: str, ctx: dict) -> str` con `\{\{([\w.]+)\}\}`.
  Lookup dotted-path; faltante = "" + warning callable.
- [ ] **T022** Crear `tablero/v2/automatizaciones/condicional.py`:
  evaluador DSL `{{var}} <op> <literal>`. Soporta `>, <, >=, <=, ==, !=,
  contains, matches`. Rechaza cualquier cosa fuera del patrón.
- [ ] **T023** Test unit `tests/test_v2_automatizaciones_interpolation.py`.
- [ ] **T024** Test unit `tests/test_v2_automatizaciones_condicional.py`
  incluye intentos de injection (`__import__`, `os.system`, etc.).

---

## Bloque 3 — Actions (T030)

- [ ] **T031** Crear `tablero/v2/automatizaciones/actions.py` con dispatcher
  `async def execute_action(action, ctx, dry_run=False) -> dict`.
- [ ] **T032** Implementar `dia_capturar` — invoca
  `tablero.v2.capturar.capturar_handler` internamente o reusa el helper.
- [ ] **T033** Implementar `telegram` — llamada directa a
  `/home/nosvers/bot/bot.py` función `send_message_direct` (o adaptador si
  no existe). Bypass MCP. Crear helper `bot/sender.py` si necesario.
- [ ] **T034** Implementar `ejecutar_agente` — subprocess
  `python /home/nosvers/unified-agent/nosvers_agent.py --agente X --params <json>`
  con timeout 60s.
- [ ] **T035** Implementar `claude_prompt` — `anthropic.Anthropic().messages.
  create()` async via `asyncio.to_thread`. Default Haiku.
- [ ] **T036** Implementar `email_enviar` — `aiosmtplib` o stub si no hay
  SMTP config (marca `available: false` en catálogo).
- [ ] **T037** Implementar `webhook_call` — `httpx.AsyncClient`. Headers
  + body_json. Timeout 30s.
- [ ] **T038** Implementar `cockpit_toast` — publica al broker canal
  `automation` evento `toast`.
- [ ] **T039** Implementar `wp_post` — POST a `WP_API/posts` con basic auth.
- [ ] **T03A** Implementar `delay` — `asyncio.sleep(segundos)`.
- [ ] **T03B** Implementar `condicional` — evalúa expresión y dispatch
  a `acciones_si` o `acciones_no`. Recursivo.
- [ ] **T03C** Test unit `tests/test_v2_automatizaciones_actions.py` con
  mocks de cada dependencia externa.

---

## Bloque 4 — Triggers (T040)

- [ ] **T041** Crear `tablero/v2/automatizaciones/triggers.py` con
  `matches(trigger, event_payload) -> bool` por tipo.
- [ ] **T042** `cron_should_fire(rrule, now, last_fire) -> bool` con croniter.
- [ ] **T043** `nota_capturada` matcher — filtros sobre WS payload del canal
  `activity`.
- [ ] **T044** `agente_terminado` matcher — sobre canal `agentes`.
- [ ] **T045** `aegis_alerta` matcher — sobre canal `aegis`.
- [ ] **T046** `voz_keyword` matcher — sobre canal `activity` con
  `origen=voz` + sustring/regex match en `texto`.
- [ ] **T047** `vps_threshold` matcher — sobre canal `health`.
- [ ] **T048** Test unit `tests/test_v2_automatizaciones_triggers.py`.

---

## Bloque 5 — Motor + Runner (T050)

- [ ] **T051** Crear `tablero/v2/automatizaciones/runner.py`:
  `async def run_chain(automation, trigger_payload, dry_run=False) -> ExecutionLog`.
  State machine: paso N → resolver vars → ejecutar → guardar output → siguiente.
- [ ] **T052** Crear `tablero/v2/automatizaciones/motor.py`:
  - `start_motor(broker)` arrancado desde el hook startup de tablero.
  - `cron_loop` tick cada 30s.
  - `event_loop` que recibe eventos del broker via internal subscriber.
  - Idempotencia in-memory con TTL 5s.
- [ ] **T053** Patch `tablero/v2/ws.py`: añadir `"automation"` a
  `VALID_CHANNELS`. Añadir `Broker.add_internal_subscriber(callback)`.
- [ ] **T054** Patch hook startup en `tablero/rest.py::montar_en_fastmcp`
  para arrancar `motor` después de los workers.
- [ ] **T055** Crear `tablero/v2/automatizaciones/logs.py`:
  `append_log(execution_log)` JSONL diario, `read_logs(date, automation_id?)`.
- [ ] **T056** Test unit `tests/test_v2_automatizaciones_motor.py` — cron tick
  y event dispatch con broker mock.

---

## Bloque 6 — REST API (T060)

- [ ] **T061** Crear `tablero/v2/automatizaciones/rest.py` con todos los
  handlers del contrato (`contracts/api.md`).
- [ ] **T062** Patch `tablero/rest.py` para añadir 11 rutas nuevas
  (`/automatizaciones`, `/automatizaciones/{id}`, `/run`, `/test`, `/logs`,
  `/catalogo`, `/reload`, `/webhook/stripe`).
- [ ] **T063** Crear `tablero/v2/automatizaciones/webhooks.py` —
  validación firma Stripe (si `stripe` SDK + secret presentes; else 503).
- [ ] **T064** Integration test `tests/test_v2_automatizaciones_api.py`
  con Starlette TestClient — CRUD + run + test + logs + catalogo.
- [ ] **T065** Integration test `tests/test_v2_automatizaciones_e2e.py` —
  cron trigger mockeado → cadena 3 acciones → assertions sobre log.

---

## Bloque 7 — Editor visual + Widget cockpit (T070)

- [ ] **T071** Instalar `reactflow` y `@monaco-editor/react`. Verificar build.
- [ ] **T072** Crear `tablero/web/src/components/automatizaciones/lib/
  apiAutomations.ts` — wrapper `fetch` para los endpoints.
- [ ] **T073** Crear `AutomationListPage.tsx` — lista con toggle, botones.
- [ ] **T074** Crear `AutomationEditor.tsx` — canvas React Flow con un nodo
  Trigger + cadena Actions. Drag-drop desde palette.
- [ ] **T075** Crear `NodePalette.tsx` — panel lateral con triggers + actions
  (icons, labels desde `/catalogo`).
- [ ] **T076** Crear `JsonSchemaForm.tsx` — renderiza form desde JSON Schema
  (string/number/bool/enum/array/object recursivo simple).
- [ ] **T077** Crear `YamlPreview.tsx` — Monaco read-only con YAML generado
  desde el state del editor.
- [ ] **T078** Crear `TestRunModal.tsx` — modal con payload mock + display
  paso a paso del resultado.
- [ ] **T079** Crear `ExecutionHistoryModal.tsx` — tabla logs del día con
  selector de fecha.
- [ ] **T07A** Hash routing: `App.tsx` detecta `#cockpit/automatizaciones`
  → renderiza `AutomationListPage`. Botón en header del cockpit.
- [ ] **T07B** Crear `hooks/useAutomationStream.ts` — subscribe canal
  `automation` y mantiene buffer 10.
- [ ] **T07C** Crear `components/cockpit/AutomationsWidget.tsx` (widget #13).
- [ ] **T07D** Patch `useCockpitLayout.ts` para añadir widget #13 al grid.
- [ ] **T07E** Patch `pages/Cockpit.tsx` para renderizar el nuevo widget.

---

## Bloque 8 — Ejemplos + Docs (T080)

- [ ] **T081** Crear `knowledge_base/automatizaciones/ejemplo_stripe_pago_grande.yaml`
  con `activo: false`.
- [ ] **T082** Crear `knowledge_base/automatizaciones/ejemplo_lunes_agt05.yaml`.
- [ ] **T083** Crear `knowledge_base/automatizaciones/ejemplo_voz_urgente.yaml`.
- [ ] **T084** Crear `tablero/AUTOMATIZACIONES.md` con arquitectura, catálogo,
  formato YAML, troubleshooting, recipes.

---

## Bloque 9 — Cockpit Polish (T090) — side-task del BRIEF

- [ ] **T091** Verificar que los 7 workers publican datos (smoke test).
  Si alguno falla, fixearlo.
- [ ] **T092** Reconexión WS con backoff exponencial en `useWebSocket.ts`
  (1s, 2s, 4s, 8s, 16s max).
- [ ] **T093** Loading skeletons para los widgets antes del primer tick
  (cualquier widget que aún no recibió snapshot WS).
- [ ] **T094** Tooltips en gauges/sparklines (CPU, RAM, revenue spark).
- [ ] **T095** Sound opcional cuando aparece toast Stripe — `/public/sounds/
  cha-ching.mp3` + flag user pref.
- [ ] **T096** Atajos de teclado: `?` muestra modal de shortcuts.
  `g h` → scroll al widget health. `g a` → automatizaciones. Implementar
  con `useKeyboardShortcut` existente.

---

## Bloque 10 — Verificación final (T0A0)

- [ ] **T0A1** `pytest tablero/tests/` — todo verde, cero regresiones.
- [ ] **T0A2** `npm run build` — typecheck verde.
- [ ] **T0A3** Smoke E2E manual: arrancar MCP, abrir cockpit, crear
  automatización, test run, ver widget #13 actualizar.
- [ ] **T0A4** Marcar tareas completed + dejar instrucciones a Angel
  (push, OAuth STRIPE_WEBHOOK_SECRET si quiere ese trigger en producción).
