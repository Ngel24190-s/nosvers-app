# Feature Specification: Automation Engine (n8n light)

**Feature Branch**: `004-automation-engine`

**Created**: 2026-05-13

**Status**: Draft

**Input**: BRIEF.md (Proyecto 004 — Fase D del roadmap original)

---

## Overview

Un editor visual de automatizaciones tipo **n8n light** sobre la infraestructura ya
desplegada (vault multi-usuario, MCP tools, unified-agent, cockpit WS broker). Permite
a Angel y África definir cadenas `trigger → action(s)` SIN CÓDIGO, almacenadas como
YAML soberano en `knowledge_base/automatizaciones/`, ejecutadas por un motor asyncio
que se suscribe al broker WS existente y al cron interno.

Es un **proyecto Spec Kit propio** (no parche del 002). Añade endpoints REST nuevos
bajo `/tablero/api/v2/automatizaciones/*`, un widget #13 en el cockpit, una página
editor visual con React Flow, y un agente runner `unified-agent/automation_runner.py`.
Cero impacto en 001/002/cockpit existente — sólo añade.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Crear automatización via editor visual (Priority: P1)

Angel abre el cockpit, va a `/cockpit/automatizaciones`, pulsa "Nueva", arrastra un
nodo Trigger (`webhook_stripe` con `amount_gte_eur: 100`), arrastra dos nodos Action
en cadena (`dia_capturar` con texto interpolado + `telegram` con confeti), conecta
las flechas, ve el YAML preview a la derecha, pulsa "Test run" con un payload
falseado, comprueba que ambas acciones se ejecutan, y guarda. La automatización
queda en estado **activa** en la lista.

**Why this priority**: Es el corazón del producto. Sin esto el editor visual no
existe. Es la diferencia entre "Angel escribe YAML a mano" (que ya podría hacer hoy
con cualquier editor) y "Angel define automatizaciones desde el cockpit".

**Independent Test**: Servir `/cockpit/automatizaciones`, crear una automatización
de ejemplo con un trigger + dos acciones, hacer Test run con datos mock y
comprobar que aparece tanto la entrada en `dia/` como un toast (mock Telegram) sin
necesidad de tener un evento Stripe real.

**Acceptance Scenarios**:

1. **Given** la página `/cockpit/automatizaciones` abierta sin automatizaciones,
   **When** Angel pulsa "Nueva", arrastra trigger `webhook_stripe`, dos acciones
   (`dia_capturar`, `telegram`), conecta y guarda, **Then** aparece en la lista con
   toggle activo, y se ha escrito un YAML válido en
   `knowledge_base/automatizaciones/auto_<timestamp>_<slug>.yaml` con `autor: angel`.
2. **Given** una automatización con dos acciones,
   **When** Angel pulsa "Test run" con payload `{amount: 150, customer: "Test"}`,
   **Then** las dos acciones se ejecutan secuencialmente en modo dry-run y devuelven
   `{ok: true, steps: [...]}` con los detalles, sin tocar Telegram real ni el vault
   (excepto si la acción `dia_capturar` viene marcada `--no-dry-run`).
3. **Given** una automatización activa con trigger `webhook_stripe`,
   **When** llega un POST real a `/tablero/api/v2/automatizaciones/webhook/stripe`
   con `amount: 200`, **Then** las acciones se ejecutan, se escribe log en
   `automatizaciones/logs/YYYY-MM-DD.jsonl`, y se publica un mensaje por WS canal
   `automation` con el resultado.

---

### User Story 2 — Listar, activar/pausar, ejecutar manualmente (Priority: P1)

Angel ve la lista de automatizaciones en `/cockpit/automatizaciones` con su toggle
**activo/pausado**. Pulsa el toggle de una y queda pausada (no se dispara con
triggers). Pulsa "Ejecutar ahora" en otra y se lanza manualmente. La lista
refresca con el último resultado de cada una (verde/rojo/ámbar).

**Why this priority**: Imprescindible para operar día a día sin tener que tocar
YAML. Si una automatización está rota o Angel está de viaje, pausarla debe ser un
clic. Sin esto el sistema queda rígido.

**Independent Test**: Crear dos automatizaciones (una con trigger cron, otra con
webhook), pulsar toggle de una para pausarla, esperar al siguiente tick cron,
comprobar que SÓLO se ejecutó la no pausada. Luego pulsar "Ejecutar ahora" en la
pausada y comprobar que sí se ejecuta una vez.

**Acceptance Scenarios**:

1. **Given** automatización `auto_X` activa,
   **When** Angel pulsa el toggle, **Then** queda persistida como `activo: false`
   en el YAML y el motor ya no la dispara en el siguiente tick.
2. **Given** automatización `auto_Y` pausada,
   **When** Angel pulsa "Ejecutar ahora", **Then** se ejecuta una vez con `trigger:
   manual` registrado en el log, sin cambiar `activo`.

---

### User Story 3 — Visibilidad en cockpit (widget #13) (Priority: P1)

Angel ve en el cockpit (sin abrir la página dedicada) un widget pequeño "Automatizaciones"
con las últimas 10 ejecuciones (timestamp + nombre + estado). Verde si OK, rojo si
error, ámbar si en curso. En vivo via WS canal `automation`. Esto le da pulso
inmediato sin tener que cambiar de pantalla.

**Why this priority**: La filosofía del cockpit es "todo en una pantalla". Si las
automatizaciones quedan invisibles desde el grid principal, Angel no sabrá cuándo
fallan y la herramienta pierde valor.

**Independent Test**: Disparar manualmente 3 automatizaciones distintas (una OK,
una en curso simulada, una con error simulado). El widget #13 muestra las tres
con sus colores correctos. Recargar la página y siguen ahí (último estado en RAM
del worker `automation`).

**Acceptance Scenarios**:

1. **Given** el cockpit abierto con widget #13 visible,
   **When** se ejecuta una automatización OK, **Then** aparece una nueva fila al
   tope con tick verde dentro de 1 segundo.
2. **Given** una automatización en curso (acción `delay 30s`),
   **When** llega el primer tick, **Then** el widget la marca ámbar; al terminar,
   pasa a verde.

---

### User Story 4 — Catálogo amplio de triggers y actions (Priority: P2)

Angel y África pueden elegir entre **8+ triggers** y **10+ actions** desde el panel
lateral del editor. Cada uno tiene un formulario con sus campos validados por
Pydantic en el backend (errores vienen marcados en rojo en el formulario).

**Why this priority**: Sin variedad de tipos, la herramienta queda como demo. Un
mínimo de 8 triggers + 10 actions cubre los casos del BRIEF (Stripe, voz, agentes,
AEGIS, cron, email, webhook genérico, threshold VPS · captura, telegram, agente,
Claude prompt, email, webhook, toast, WP post, delay, condicional).

**Independent Test**: Para cada tipo de trigger/action en el catálogo, crear una
automatización trivial que lo use, intentar guardar, comprobar que el YAML
generado pasa la validación Pydantic en el backend.

**Acceptance Scenarios**:

1. **Given** el panel lateral del editor,
   **When** Angel abre el dropdown de triggers, **Then** ve al menos 8 tipos
   (`cron`, `webhook_stripe`, `nota_capturada`, `agente_terminado`, `aegis_alerta`,
   `email_match`, `voz_keyword`, `vps_threshold`).
2. **Given** el panel lateral,
   **When** Angel abre el dropdown de actions, **Then** ve al menos 10 tipos
   (`dia_capturar`, `telegram`, `ejecutar_agente`, `claude_prompt`, `email_enviar`,
   `webhook_call`, `cockpit_toast`, `wp_post`, `delay`, `condicional`).
3. **Given** una automatización con campos inválidos (ej. `cron: "no-rrule-válida"`),
   **When** se intenta guardar, **Then** la respuesta es 422 con el campo concreto
   marcado y el editor muestra el error en rojo.

---

### User Story 5 — Logs estructurados y reproducibilidad (Priority: P2)

Cada ejecución (real o manual) deja un registro JSONL con timestamp, automatización,
trigger payload, resultado de cada acción y duración. Angel puede filtrar logs por
fecha y por automatización desde el editor (botón "Ver historial").

**Why this priority**: Sin logs auditables no se puede depurar. El BRIEF lo exige
explícitamente y la regla de soberanía (todo en vault) lo refuerza.

**Independent Test**: Lanzar 3 ejecuciones, comprobar que `logs/<fecha>.jsonl`
contiene 3 líneas con los campos requeridos, y que el endpoint GET
`/tablero/api/v2/automatizaciones/<id>/logs` las devuelve.

**Acceptance Scenarios**:

1. **Given** una ejecución completada,
   **When** se inspecciona `logs/2026-05-13.jsonl`, **Then** hay una línea JSON con
   `{automation_id, trigger, started_at, ended_at, status, steps: [{action_type,
   ok, duration_ms, error?}]}`.
2. **Given** se reinicia el motor mientras una ejecución estaba en curso,
   **When** arranca de nuevo, **Then** las ejecuciones in-flight quedan marcadas
   como `status: interrupted` en el log y no se duplican (idempotencia por
   trigger_id + timestamp).

---

### User Story 6 — Ejemplos cargados y operativos (Priority: P3)

El sistema arranca con **3 automatizaciones de ejemplo** desactivadas por defecto
pero listas para activarse:
- `ejemplo_stripe_pago_grande.yaml` — pago Stripe > 100€ → captura + telegram
- `ejemplo_lunes_agt05.yaml` — cron lunes 9h → ejecuta agt05_africa
- `ejemplo_voz_urgente.yaml` — voz contiene "urgente" → telegram + dia_capturar

**Why this priority**: Reduce la curva de aprendizaje. Angel puede activar uno
y ver inmediatamente cómo se comporta, en vez de tener que diseñar desde cero.

**Independent Test**: Arrancar el sistema limpio. Comprobar que los 3 YAML están
en `knowledge_base/automatizaciones/`, con `activo: false`. Activar uno desde el
editor y comprobar que se dispara correctamente.

**Acceptance Scenarios**:

1. **Given** instalación fresca,
   **When** se lista `knowledge_base/automatizaciones/*.yaml`, **Then** existen al
   menos 3 ficheros con prefijo `ejemplo_`.
2. **Given** ejemplo `ejemplo_voz_urgente` activado,
   **When** llega un dictado con palabra "urgente", **Then** se envía Telegram (vía
   el bot existente) y se crea entrada en `dia/` con etiqueta `urgente`.

---

### Edge Cases

- **Acción individual falla** (ej. Telegram timeout): la cadena continúa con la
  siguiente acción salvo que el nodo `condicional` lo bloquee. El paso queda
  marcado `ok: false` en el log.
- **YAML inválido en disco**: el motor lo salta al arrancar, lo lista como
  "corrupto" en el endpoint `/list`, y publica un toast rojo en el cockpit.
- **Trigger se dispara mientras automatización está pausada**: se descarta sin log.
- **Mismo trigger en <1s** (debounce): si `trigger_id+timestamp` coincide con
  ejecución reciente (<5s), se descarta como duplicado.
- **Webhook Stripe sin firma válida**: 401 sin ejecutar acciones.
- **Acción `delay 30s` se reinicia el motor**: la ejecución queda como
  `interrupted` y no se reanuda (idempotencia simple v1).
- **2 personas editan la misma automatización a la vez**: last-write-wins (vault
  source of truth, sin locks; auditable vía git).
- **Cron rrule mal formada**: 422 al guardar; no se persiste.
- **Acción `ejecutar_agente` con agente desconocido**: 422 al guardar (validar
  contra catálogo agentes existente en `/tablero/api/v2/agentes/catalogo`).
- **Acción `claude_prompt` excede límite de tokens**: timeout 30s default; queda
  marcada `ok: false` con error específico.

---

## Requirements *(mandatory)*

### Functional Requirements

**Storage**
- **FR-001**: Cada automatización se persiste como fichero YAML en
  `knowledge_base/automatizaciones/<id>.yaml` con campos:
  `id, nombre, autor (angel|africa|claude), creado, modificado, activo, trigger,
  acciones`. Frontmatter YAML; texto humano-editable.
- **FR-002**: El `id` se genera con formato `auto_YYYY_MM_DD_<slug>` y debe ser
  único. El motor rechaza ficheros con id duplicado al arrancar (warn + skip).
- **FR-003**: Lecturas y escrituras pasan por la capa atómica existente
  (`tablero/v2/atomic_write.py`). Cero ficheros corruptos por crash a media
  escritura.

**API REST (CRUD)**
- **FR-010**: `GET /tablero/api/v2/automatizaciones` lista todas las
  automatizaciones con `{id, nombre, autor, activo, trigger_tipo, last_run}`.
- **FR-011**: `GET /tablero/api/v2/automatizaciones/{id}` devuelve la
  automatización completa incluyendo `acciones` parseadas.
- **FR-012**: `POST /tablero/api/v2/automatizaciones` crea (autor = sub del JWT).
- **FR-013**: `PUT /tablero/api/v2/automatizaciones/{id}` actualiza
  (incluyendo toggle `activo`).
- **FR-014**: `DELETE /tablero/api/v2/automatizaciones/{id}` mueve a
  `automatizaciones/archivadas/`.
- **FR-015**: `POST /tablero/api/v2/automatizaciones/{id}/run` ejecuta
  manualmente. Acepta body opcional con payload de test.
- **FR-016**: `POST /tablero/api/v2/automatizaciones/{id}/test` ejecuta
  dry-run sin tocar efectos externos.
- **FR-017**: `GET /tablero/api/v2/automatizaciones/{id}/logs?date=YYYY-MM-DD`
  devuelve las ejecuciones del día.
- **FR-018**: `GET /tablero/api/v2/automatizaciones/catalogo` devuelve los
  schemas JSON de triggers + actions disponibles, para que el editor visual
  pueda generar formularios.
- **FR-019**: Todos los endpoints validan JWT vía `voz.auth.validar_token`.
  Sólo `angel` y `africa` pueden crear/editar/borrar; `claude` (agente) puede
  ejecutar pero no editar.

**Triggers (≥8 tipos)**
- **FR-020** `cron`: rrule estilo iCal evaluada con `croniter`. Tick interno
  cada 30s; precisión a minuto.
- **FR-021** `webhook_stripe`: endpoint `POST /tablero/api/v2/automatizaciones/
  webhook/stripe` con validación de firma `Stripe-Signature`. Filtros:
  `evento` (string), `amount_gte_eur` (float).
- **FR-022** `nota_capturada`: suscripción al WS canal `activity` del cockpit;
  filtros `autor`, `etiqueta`, `contenido_regex`.
- **FR-023** `agente_terminado`: suscripción al WS canal `agentes`; filtros
  `nombre_agente`, `estado` (success|error).
- **FR-024** `aegis_alerta`: suscripción al WS canal `aegis`; filtros
  `severidad` (info|warn|critical).
- **FR-025** `email_match`: poll IMAP cada 5 min (si SMTP/IMAP config existe);
  filtros `from_regex`, `subject_regex`. Si no hay config IMAP, el tipo queda
  marcado "no disponible" en el catálogo (`available: false`).
- **FR-026** `voz_keyword`: suscripción al WS canal `activity` filtrando por
  `origen: voz`; campos `keywords` (lista).
- **FR-027** `vps_threshold`: suscripción al WS canal `health`; campos `metrica`
  (cpu|ram|disk), `umbral_pct`, `comparador` (gt|lt).

**Actions (≥10 tipos)**
- **FR-030** `dia_capturar`: invoca handler interno
  `tablero.v2.capturar.capturar_handler`. Acepta `texto` (con interpolación
  `{{trigger.X}}`), `etiqueta`, `autor` (default = autor de la automatización).
- **FR-031** `telegram`: usa el bot existente
  (`mcp__claude_ai_nosvers-mcp-2026__telegram_enviar`), pero llamado
  directamente vía la función Python subyacente para evitar latencia/cuelgue
  de la capa MCP. Acepta `mensaje`, `chat_id` (default = ANGEL_CHAT_ID).
- **FR-032** `ejecutar_agente`: ejecuta un agente del unified-agent
  (`unified-agent/nosvers_agent.py` con flag `--agente`). Acepta `agente`,
  `params`.
- **FR-033** `claude_prompt`: llama Anthropic API con `model` (haiku-4-5 o
  opus-4-7), `system`, `prompt`, `max_tokens` (default 2000). Guarda respuesta
  en variable de cadena `{{paso_<n>.respuesta}}`.
- **FR-034** `email_enviar`: SMTP via config en `.env.local` (SMTP_HOST,
  SMTP_USER, SMTP_PASS). Si no hay config, marcado `available: false`.
  Acepta `to`, `subject`, `body`.
- **FR-035** `webhook_call`: HTTP POST genérico. Acepta `url`, `method`
  (POST/GET/PUT/DELETE), `headers`, `body_json`.
- **FR-036** `cockpit_toast`: publica en WS canal `automation` un mensaje
  `{type: "toast", level: ok|warn|error, text}` que el cockpit muestra.
- **FR-037** `wp_post`: crea draft en WordPress vía REST API existente.
  Acepta `titulo`, `contenido_html`, `status` (default `draft`).
- **FR-038** `delay`: pausa N segundos (max 300s, default 5s). No bloquea
  otras automatizaciones (asyncio.sleep).
- **FR-039** `condicional`: rama if/else. Acepta `expresion`
  (ej. `{{trigger.amount}} > 100`), `acciones_si`, `acciones_no`.
  Evaluador simple Python ast (sin eval).

**Motor de ejecución**
- **FR-040**: Servicio asyncio standalone `unified-agent/automation_runner.py`.
  Arranca con systemd (`nosvers-automation.service`) o como tarea asyncio
  embebida en el proceso uvicorn del MCP (decisión de plan).
- **FR-041**: Lee todos los YAML al arrancar. Reload con SIGHUP o endpoint
  `POST /tablero/api/v2/automatizaciones/reload`.
- **FR-042**: Suscriptor al WS broker como cliente interno (no via WebSocket
  real — `broker.subscribe` directo en el proceso si es embebido).
- **FR-043**: Cron interno cada 30s comprueba qué automatizaciones cron deben
  dispararse en la ventana actual (idempotencia por minuto).
- **FR-044**: Cada acción tiene timeout default 30s. Excepción se captura, se
  loguea con `ok: false`, y la cadena sigue salvo `condicional` lo decida.
- **FR-045**: Cada ejecución publica eventos por WS canal `automation`:
  `{type: started}` → `{type: step, n, ok}` (x N) → `{type: finished, status}`.
- **FR-046**: Logs en JSONL en `automatizaciones/logs/YYYY-MM-DD.jsonl`,
  rotación diaria. Una línea por ejecución, en cierre.

**Editor visual**
- **FR-050**: Página nueva en el cockpit `/cockpit/automatizaciones` (ruta
  React nueva, navegación desde el header).
- **FR-051**: Lista de automatizaciones con toggle activo/pausado, botones
  `Editar`, `Ejecutar ahora`, `Ver historial`, `Borrar`.
- **FR-052**: Botón `Nueva` → editor canvas (React Flow). Canvas inicial con
  un nodo `+ Trigger` vacío.
- **FR-053**: Drag-and-drop de nodos desde el panel lateral derecho (lista de
  triggers + actions con icono).
- **FR-054**: Click en un nodo → panel lateral con form generado dinámicamente
  según el schema devuelto por `/catalogo`.
- **FR-055**: Conectores entre nodos con flechas. Sólo trigger único →
  acciones en cadena (sin branching aún v1 salvo via `condicional`).
- **FR-056**: Panel `YAML preview` debajo del canvas (Monaco editor, read-only).
- **FR-057**: Botón `Test run` con un modal donde se introduce el payload mock
  del trigger; muestra resultado paso a paso.
- **FR-058**: Botón `Guardar` valida en backend; muestra errores Pydantic
  inline en los nodos correspondientes.

**Widget cockpit #13**
- **FR-060**: Componente nuevo `AutomationsWidget.tsx` en
  `tablero/web/src/components/cockpit/`. Suscribe al canal WS `automation`.
- **FR-061**: Muestra últimas 10 ejecuciones (timestamp + nombre + estado
  con color). Buffer en memoria del cliente.
- **FR-062**: Click en una fila → modal con el log JSON formateado.
- **FR-063**: Se añade al grid del cockpit en `useCockpitLayout.ts` con
  tamaño 6 cols (medio).

**Ejemplos**
- **FR-070**: Cargar 3 ejemplos a `knowledge_base/automatizaciones/` con
  `activo: false`: `ejemplo_stripe_pago_grande.yaml`,
  `ejemplo_lunes_agt05.yaml`, `ejemplo_voz_urgente.yaml`.

**Tests**
- **FR-080**: Unit tests del motor con triggers + actions mockeados.
- **FR-081**: Integration test de una cadena completa (trigger cron mock →
  3 acciones → log final).
- **FR-082**: Tests de validación Pydantic para cada tipo de trigger/action.

**Documentación**
- **FR-090**: `tablero/AUTOMATIZACIONES.md` con: arquitectura, catálogo
  trigger/action, formato YAML, troubleshooting, ejemplos.

### Non-Functional Requirements

- **NFR-001 Soberanía**: Cero dependencias de Zapier/IFTTT/n8n cloud. Todo
  local en VPS.
- **NFR-002 Vault as source of truth**: Cualquier `.yaml` que aparezca en el
  directorio se recoge en el próximo reload. Permite editar con Obsidian/Syncthing.
- **NFR-003 Auditoría**: Todo log incluye `autor`. Cero automatizaciones
  anónimas. `claude` puede ejecutar pero no crear.
- **NFR-004 No regresión**: Tests existentes del 002 (`tablero/tests/*`) siguen
  pasando al 100%.
- **NFR-005 Sandboxing**: Timeout default 30s por acción. Excepciones contenidas.
- **NFR-006 Performance**: Listar 100 automatizaciones < 200ms. Test-run de
  cadena de 5 acciones < 2s. Latencia de trigger WS → primera acción < 1s.
- **NFR-007 Privacidad**: Como con notas, `autor` visible. Compartido por
  defecto (decisión sesión 14.3 vault multi-usuario).

---

## Key Entities

### Automation (entidad principal)
```
id: string (formato auto_YYYY_MM_DD_<slug>)
nombre: string (libre)
autor: enum [angel, africa, claude]
creado: ISO datetime
modificado: ISO datetime
activo: bool
trigger: Trigger
acciones: list[Action]
metadatos: dict (free-form, ej. tags, descripcion)
```

### Trigger (sealed union)
- `CronTrigger { tipo: "cron", rrule: string }`
- `WebhookStripeTrigger { tipo: "webhook_stripe", evento: string, filtros: {amount_gte_eur?: float} }`
- `NotaCapturadaTrigger { tipo: "nota_capturada", filtros: {autor?, etiqueta?, contenido_regex?} }`
- `AgenteTerminadoTrigger { tipo: "agente_terminado", filtros: {nombre_agente?, estado?} }`
- `AegisAlertaTrigger { tipo: "aegis_alerta", filtros: {severidad?} }`
- `EmailMatchTrigger { tipo: "email_match", filtros: {from_regex?, subject_regex?} }`
- `VozKeywordTrigger { tipo: "voz_keyword", keywords: [string] }`
- `VpsThresholdTrigger { tipo: "vps_threshold", metrica: enum, umbral_pct: float, comparador: enum }`

### Action (sealed union)
- `DiaCapturarAction { tipo, texto, etiqueta?, autor? }`
- `TelegramAction { tipo, mensaje, chat_id? }`
- `EjecutarAgenteAction { tipo, agente, params? }`
- `ClaudePromptAction { tipo, model, system?, prompt, max_tokens? }`
- `EmailEnviarAction { tipo, to, subject, body }`
- `WebhookCallAction { tipo, url, method?, headers?, body_json? }`
- `CockpitToastAction { tipo, level, text }`
- `WpPostAction { tipo, titulo, contenido_html, status? }`
- `DelayAction { tipo, segundos }`
- `CondicionalAction { tipo, expresion, acciones_si: [Action], acciones_no?: [Action] }`

### ExecutionLog (JSONL)
```
{
  automation_id: string,
  trigger: {tipo: string, payload: dict},
  started_at: ISO,
  ended_at: ISO,
  status: enum [ok, partial, error, interrupted],
  steps: [{n: int, action_tipo: string, ok: bool, duration_ms: int, error?: string, output?: dict}]
}
```

---

## Success Criteria

- **SC-001**: Una automatización completa (trigger Stripe → 2 acciones) se
  crea en el editor, se guarda, recibe un webhook real (o simulado) y se
  ejecuta correctamente en **menos de 3 minutos** desde "página vacía".
- **SC-002**: 8 tipos de triggers + 10 tipos de actions están operativos
  (con tests verdes para cada uno).
- **SC-003**: El widget cockpit #13 muestra cambios de estado de ejecuciones
  con **latencia < 1s** desde que ocurren.
- **SC-004**: Test suite ampliada pasa al 100% (anterior + nuevos). Cero
  regresiones en 002.
- **SC-005**: 3 ejemplos cargados, parseables, ejecutables tras activar.
- **SC-006**: Documentación `AUTOMATIZACIONES.md` permite a alguien externo
  crear una automatización nueva sin tocar código en < 10 minutos.
- **SC-007**: Cockpit pulido: 7 workers publican datos verificados,
  reconexión WS con backoff exponencial activa, loading skeletons,
  tooltips en gauges/sparklines, sonido opcional toast Stripe, atajos
  teclado (`?`, `g h`, etc.).

---

## Assumptions

- El bot Telegram ya existe y la función Python subyacente (`bot.send_message`)
  es invocable desde el motor sin pasar por la capa MCP que sufre el bug de
  stall (memoria `project_telegram_enviar_stall.md`).
- `voz.auth.validar_token` sigue siendo la fuente de identidad.
- El WS broker actual (`tablero/v2/ws.py`) acepta añadir el canal `automation`
  sin breaking changes (se añade `automation` a `VALID_CHANNELS`).
- El catálogo de agentes del unified-agent es accesible vía
  `/tablero/api/v2/agentes/catalogo`.
- Stripe webhook secret ya configurado o se configurará en `.env.local`
  (`STRIPE_WEBHOOK_SECRET`). Si no, ese tipo queda como `available: false`.
- IMAP y SMTP NO están configurados aún → triggers/actions correspondientes
  son `available: false` en v1, pero su esquema está listo para activarse.

---

## Dependencies

- 001 voice-assistant — fuente de eventos `nota_capturada`/`voz_keyword`.
- 002 Fase B+C — `voz.auth`, `tablero/v2/capturar.py`, `atomic_write.py`,
  `agentes/catalogo`, vault.
- 003 Cockpit — WS broker, grid, hooks, NeuralGraph.
- unified-agent — `nosvers_agent.py --agente <name>`.
- `croniter` (nueva dep), `pyyaml` (ya), `reactflow` (nueva dep frontend),
  `@monaco-editor/react` (nueva dep frontend).

---

## Out of Scope (v1)

- Ramas paralelas (fan-out de un trigger a 2 cadenas distintas). Sólo
  cadena secuencial + `condicional` interno.
- Reanudación tras crash (idempotencia simple: las ejecuciones interrumpidas
  no se reintentan automáticamente).
- Variables globales compartidas entre ejecuciones.
- Versionado/rollback de automatizaciones (vive en git si se quiere).
- Permisos granulares (sólo angel/africa/claude por ahora, sin RBAC).
- UI mobile-first del editor (el editor visual asume desktop; el cockpit ya
  es responsive para la vista de lista y widget).
