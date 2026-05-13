# BRIEF — Automation Engine NosVers (Proyecto 004)

Fase D del roadmap original del Second Brain Dashboard. Editor visual de automatizaciones tipo **n8n light** sobre la infraestructura existente (vault, MCP, unified-agent, cockpit). Es proyecto Spec Kit propio (no parche del 002).

## Por qué AHORA y no antes

Pre-requisitos cumplidos:
- 001 voice-assistant ✓ (proporciona dia_capturar/contexto como event source)
- 002 Fase A+B+C ✓ (vault multi-usuario, tablero, MCP tools)
- 002 Cockpit ✓ (UI lista para embeber el editor visual)
- unified-agent ✓ (ejecutor confiable de tareas async)

## Visión

Angel y África definen automatizaciones SIN ESCRIBIR CÓDIGO:
- "Cuando llegue email de Stripe con monto > 100€ → captura nota en `dia/` con etiqueta `nosvers` → mándame Telegram con confeti"
- "Cada lunes a las 9 → ejecuta agt05_africa → si encuentra cambios en el huerto → notifica África"
- "Si dictado de voz contiene palabra 'urgente' → mensaje Telegram inmediato + crea entrada en calendario para mañana"
- "Si AEGIS detecta alerta crítica → para freqtrade → notifica con sonido en el cockpit"

## Componentes

### 1. Storage de automatizaciones
Cada automatización es un fichero YAML en `knowledge_base/automatizaciones/*.yaml`:
```yaml
id: auto_2026_05_13_stripe_pago
nombre: "Notificar pagos Stripe grandes"
autor: angel
creado: 2026-05-13T18:00:00Z
activo: true
trigger:
  tipo: webhook_stripe
  evento: payment_intent.succeeded
  filtros:
    amount_gte_eur: 100
acciones:
  - tipo: dia_capturar
    texto: "Pago Stripe {{trigger.amount}}€ de {{trigger.customer}}"
    etiqueta: nosvers
  - tipo: telegram
    mensaje: "💰 {{trigger.amount}}€ - {{trigger.customer}} acaba de comprar"
```

### 2. Editor visual (en el Cockpit)
Página nueva `/cockpit/automatizaciones` o widget expandible:
- Lista de automatizaciones activas/pausadas con toggle
- Botón "Nueva" → editor canvas tipo n8n con cards drag-and-drop:
  - Card Trigger (1) → Card Action (n) en cadena
  - Conectores con flechas animadas
  - Click en card → panel lateral con configuración
- Preview del YAML generado en tiempo real
- Botón "Test run" para ejecutar con datos de prueba sin guardar

### 3. Catálogo de Triggers
- `cron`: programado (rrule estilo iCal)
- `webhook_stripe`: pagos Stripe (requiere webhook URL configurada en Stripe dashboard)
- `nota_capturada`: cuando dia_capturar añade entrada con filtros (autor/etiqueta/contenido_regex)
- `agente_terminado`: cuando un agente del unified-agent finaliza con estado X
- `aegis_alerta`: cuando AEGIS emite alerta
- `email_match`: cuando llega email a la cuenta principal con filtros (requiere IMAP setup)
- `voz_keyword`: cuando dictado contiene palabra clave
- `vps_threshold`: cuando CPU/RAM/disco supera un umbral

### 4. Catálogo de Actions
- `dia_capturar`: crea entrada en vault
- `telegram`: envía mensaje
- `ejecutar_agente`: lanza agente del unified-agent
- `claude_prompt`: invoca Claude (Haiku o Opus) con prompt y guarda respuesta en vault
- `email_enviar`: manda email (requiere SMTP)
- `webhook_call`: POST a URL externa
- `cockpit_toast`: notificación visual en el cockpit
- `wp_post`: crea borrador WordPress
- `delay`: pausa N segundos/minutos
- `condicional`: rama if/else basada en valor

### 5. Motor de ejecución
Un nuevo agente `unified-agent/automation_runner.py`:
- Lee todos los YAML al arrancar
- Suscrito al WS broker del cockpit para eventos en vivo
- Cron interno para triggers de tipo `cron`
- Para cada trigger activado → ejecuta la cadena de acciones secuencialmente con state machine
- Log estructurado por ejecución en `knowledge_base/automatizaciones/logs/YYYY-MM-DD.jsonl`
- Idempotencia por trigger_id + timestamp para evitar duplicados si se reinicia

### 6. Visibilidad en el Cockpit
Nuevo widget #13 en el cockpit (que se añade al grid existente):
- Lista últimas 10 ejecuciones (timestamp, automatización, resultado)
- Verde si OK, rojo si error, ámbar si en curso
- Stream en vivo via WS canal `automation`

## Stack

Frontend:
- React Flow (`reactflow` npm) — la mejor lib para editor visual de nodos con drag-and-drop
- shadcn/ui para forms del panel lateral
- Monaco editor para el YAML preview (read-only)

Backend:
- FastAPI nuevo endpoint `/tablero/api/v2/automatizaciones/*` (CRUD + test_run + activate/pause)
- Pydantic models para validación de schemas Trigger/Action
- `croniter` para evaluar reglas cron
- `pyyaml` (ya estaba) para serializar

Motor:
- Python asyncio (mismo runtime que el unified-agent)
- Conexión al broker WS del cockpit como SUSCRIPTOR (no como publisher)

## Constraints

- Soberanía: nada de Zapier/IFTTT/n8n cloud. Todo local.
- Vault source of truth: cada automatización es .yaml en vault, recargable con `git pull`
- Sandboxing: cada acción tiene timeout (default 30s), errores no rompen la cadena (siguen las siguientes salvo `condicional` lo decida)
- Auditoría: TODO log con autor humano detrás de la creación (no se crean automatizaciones anónimamente)
- Privacidad: como con notas, autor=angel/africa visible. Compartido por defecto (sesión 14.3).
- No regresión: cero impacto en 001, 002, cockpit existente. Solo añade.

## Flujo Spec Kit

1. `/speckit-specify` — spec desde este brief
2. `/speckit-clarify` — solo si hay dudas críticas
3. `/speckit-plan` — stack, schemas, integraciones con WS broker existente
4. `/speckit-tasks` — agrupado por: storage, editor visual, motor, integración cockpit
5. `/speckit-implement` — ejecuta sin parar

## Constraints operacionales

- Bug telegram_enviar conocido — NO usar para mensajes intermedios. Solo UNO final al cerrar.
- Settings.json global ya tiene auto-approve para tools MCP + Bash + filesystem.
- `linger=yes` activado — tmux no se cae.
- Si algún MCP call cuelga > 30s, abortar y reintentar una vez.
- Al cerrar todo: marcar tasks + dejar instrucciones para Angel (push, OAuth configs si aplica).

## Pulido del cockpit como side-task

Mientras esperas a algo (o como sub-fase), pule estos detalles del cockpit ya desplegado:
- Verifica que los 7 workers (claude, health, activity, agentes, revenue, aegis, wake) publican datos. Si alguno no publica, fixearlo.
- Reconexión WS automática con backoff exponencial si la red cae (en `useWebSocket.ts`)
- Loading skeletons para los widgets antes del primer tick
- Tooltips en hover de gauges/sparklines mostrando valor exacto
- Sound opcional cuando aparece toast Stripe (file en /public/sounds/cha-ching.mp3)
- Atajos de teclado: `?` muestra modal de shortcuts, `g h` va a health widget, etc.

## Estimación

Trabajo humano: 3-4 semanas. Para Claude Code: 4-6 horas (similar a Fase B+C).

## Definition of done

- 8+ tipos de triggers operativos
- 10+ tipos de actions operativos
- Editor visual con drag-and-drop funcional
- Al menos 3 automatizaciones de ejemplo cargadas y activas (proporcionar plantillas)
- Widget de visibilidad en cockpit funcionando
- Tests: unit tests del motor (mock triggers + actions), integration test de una cadena completa
- Documentación en `tablero/AUTOMATIZACIONES.md`
- Pulido del cockpit hecho

---
*Brief preparado por Claude Opus 4.7 (sesión móvil), 2026-05-13 18:00 UTC*
