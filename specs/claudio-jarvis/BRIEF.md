# BRIEF — Claudio Jarvis Evolution (Proyecto 005)

> "El homme à tout faire digital de la familia Angel + África"
> No solo NosVers — la vida entera.

## Visión

Claudio evoluciona de asistente de NosVers a **mayordomo digital familiar completo**. Es:

- **Quien recuerda** cumpleaños, ITV del coche, fechas de seguros, vacunas del perro Bris
- **Quien apunta** gastos cuando dices "he pagado 45€ de gasolina"
- **Quien archiva** facturas, contratos, papeles del médico cuando los dictás
- **Quien sugiere** menús según lo que hay en el huerto y la nevera
- **Quien filtra** emails y te despeja la bandeja
- **Quien planifica** vacaciones con África sin que tú abras Booking
- **Quien aprende** de cada conversación sin perder tu privacidad
- **Quien protege** todo dentro de TU vault, NO en cloud ajeno

## Principios no-negociables

1. **Soberanía total**: vault local, MCP local, modelos via Anthropic Pro plan (no APIs sueltas que cuesten). Cero Zapier, cero IFTTT, cero cloud propietario para datos familiares.
2. **Vault es la memoria**: cada hecho, cada nota, cada decisión, queda como markdown en `knowledge_base/`. Si Anthropic desaparece mañana, los datos siguen siendo legibles con un editor de texto.
3. **Speaker ID + identidad clara**: Claudio sabe quién habla (Angel/África) y adapta el tono. Decisiones financieras importantes piden confirmación al ojo que tiene autoridad (ambos en el día a día, pero Angel para inversiones, África para decisiones del huerto).
4. **Modo doméstico vs modo negocio**: el mismo Claudio, dos personalidades coloreadas. Calidez familiar en lo doméstico, sobrio y técnico en NosVers/infraestructura.
5. **Pro-actividad CON consentimiento**: Claudio puede sugerir e iniciar conversaciones (recordatorios, alertas, ideas) pero NUNCA actuar irreversiblemente sin aprobación humana. "Mañana ITV → ¿reservo cita?" SÍ. Reservar la cita solo NO.
6. **Familia primero**: África tiene el mismo rango que Angel, sin asimetrías. Bris el perro tiene su propio espacio.

## Arquitectura del vault (reorganización Fase 1)

Estructura nueva bajo `public_html/knowledge_base/`:

```
knowledge_base/
├── claudio/              ← NUEVO: identidad, prompts, memorias compartidas
│   ├── IDENTIDAD.md
│   ├── personalidad.md
│   ├── memorias/{angel,africa,compartido}/*.md
│   └── conocimiento/{nucleo_familiar,bris,casa,coche,abuelos}.md
├── familia/              ← NUEVO
│   ├── cumpleanos.md
│   ├── decisiones/
│   ├── recordatorios/
│   └── conversaciones/
├── finanzas/             ← NUEVO
│   ├── gastos/{YYYY-MM}.md
│   ├── ingresos/
│   ├── recurrentes.yaml   (Netflix, internet, seguros, etc.)
│   ├── presupuesto-mes.md
│   └── alertas.md
├── salud/                ← NUEVO
│   ├── medicacion.yaml
│   ├── citas/
│   ├── sintomas/{YYYY-MM}.md
│   └── chequeos.md
├── documentos/           ← NUEVO
│   ├── facturas/{YYYY}/
│   ├── contratos/
│   ├── seguros/
│   ├── impuestos/
│   └── INDEX.md           (índice automantenido)
├── casa/                 ← NUEVO
│   ├── electrodomesticos.yaml
│   ├── mantenimiento.md
│   └── reformas/
├── coche/                ← NUEVO
│   ├── INDEX.md          (matrícula, ITV, seguro, gastos)
│   ├── mantenimiento/
│   └── gastos/
├── viajes/               ← NUEVO
│   ├── planificacion/
│   ├── recuerdos/{YYYY}/
│   └── checklist-general.md
├── lectura/              ← NUEVO
│   ├── notas/
│   ├── highlights/
│   └── cola.md           (qué leer)
├── compras/              ← NUEVO
│   ├── lista_actual.md
│   ├── historico/{YYYY-MM}.md
│   └── despensa.yaml
├── menus/                ← NUEVO
│   ├── recetas/
│   ├── semana_actual.md
│   └── favoritos.md
├── nosvers/              ← YA EXISTE (mantiene su contenido actual)
├── operaciones/          ← YA EXISTE
├── agentes/              ← YA EXISTE
├── dia/                  ← YA EXISTE (diario común Angel + África)
└── automatizaciones/     ← YA EXISTE (Engine v1)
```

Migración cuidadosa: nada de lo existente se mueve hasta tener certeza. Solo se CREAN los directorios nuevos vacíos con un README.md inicial. Lo existente sigue intacto.

## Tools MCP nuevos (Fase 1)

Añadir al `mcp_server.py` (extender, no romper los 15 existentes):

### Dominio familia/recordatorios
- `recordatorio_crear(texto, fecha_o_recurrencia, autor, prioridad)` → crea entrada en `familia/recordatorios/`
- `recordatorios_listar(periodo='proximos_7_dias', autor=None)` → devuelve recordatorios activos
- `recordatorio_completar(id)` → marca como hecho, mueve a `familia/recordatorios/completados/`

### Dominio finanzas
- `gasto_anotar(monto_eur, concepto, categoria, autor)` → añade a `finanzas/gastos/YYYY-MM.md`
- `gastos_resumen(periodo='mes_actual', categoria=None)` → devuelve agregado
- `recurrente_alertar()` → revisa `finanzas/recurrentes.yaml`, alerta de cargos próximos

### Dominio compras/menús
- `lista_compras_añadir(item, cantidad=1, urgente=False, autor)` → añade a `compras/lista_actual.md`
- `lista_compras_ver()` → devuelve lista vigente
- `lista_compras_completar(item)` → marca comprado, registra en histórico
- `menu_sugerir(dia, ingredientes_disponibles=None)` → sugiere receta de `menus/recetas/` filtrando por ingredientes
- `receta_guardar(nombre, ingredientes, pasos, fuente)` → añade a `menus/recetas/`

### Dominio coche
- `coche_estado()` → devuelve resumen de `coche/INDEX.md` (próxima ITV, último mantenimiento, kilómetros)
- `coche_evento(tipo, fecha, monto, notas)` → registra evento (gasolina/mantenimiento/multa/etc.)

### Dominio documentos
- `documento_anotar(tipo, contenido_texto, fecha, fuente, autor)` → guarda en `documentos/<tipo>/` con frontmatter
- `documentos_buscar(query)` → grep estructurado sobre `documentos/`

### Dominio salud
- `medicacion_recordar()` → revisa `salud/medicacion.yaml`, devuelve tomas pendientes hoy
- `cita_medica_anotar(quien, especialista, fecha, notas)` → añade a `salud/citas/`

### Dominio claudio identidad
- `claudio_recordar(autor, hecho, importancia=5)` → guarda hecho personal en `claudio/memorias/{autor}/YYYY-MM.md`
- `claudio_contexto(autor, query)` → devuelve memorias relevantes para responder

**Total nuevos tools: ~22**. Sumados a los 15 existentes (más Automation Engine) = ~50 tools MCP.

## Identidad de Claudio (markdown que él lee al arrancar)

Archivo `claudio/IDENTIDAD.md` que se inyecta como contexto persistente del asistente. Define:

- Quién es Claudio: mayordomo digital, no app
- Núcleo familiar: Angel (esposo), África (esposa), Bris (boxer)
- Lenguajes: español con familia, francés para NosVers público, inglés solo si se pide
- Tono: cariñoso pero directo, sin lambioso, con humor sobrio cuando toca
- Valores heredados de Angel: resiliencia + soberanía
- Qué NO hace: no actúa irreversiblemente sin permiso, no envía mensajes a terceros sin OK, no compra cosas, no contrata servicios
- Modo según hora: silencio en horas de descanso de la familia (definir con Angel)
- Cuándo callar: si conversación es íntima entre Angel y África, Claudio se aparta

## Personalidad diferenciada

`claudio/personalidad.md` define perfiles según contexto:

- **familia**: cariñoso, paciente, recuerda detalles, pregunta cómo va el día
- **negocio_nosvers**: enfocado, sobrio, KPI-oriented
- **tecnico_infra**: preciso, directo, asume conocimiento de Angel
- **salud**: empático, prudente, recuerda siempre "no soy médico"
- **finanzas**: factual, alerta de riesgos sin alarmismo
- **niños** (futuro): respuestas apropiadas, sin contenido adulto

Claudio detecta el contexto por el dominio del tool llamado y por el speaker.

## Integración con cockpit

Nuevos widgets a añadir al cockpit en una Fase 2 (no esta):
- **Recordatorios hoy/semana**: cards glassmorphism con check
- **Gastos del mes**: bar chart por categoría
- **Lista compras pendiente**: rápido check con voz
- **Próxima medicación**: hora + qué
- **Coche status**: tarjeta con próxima ITV destacada
- **Menú de hoy**: receta + foto

En esta Fase 1 NO se tocan widgets del cockpit. Solo backend + vault + tools MCP.

## Automatizaciones de ejemplo (3 nuevas precargadas activo:false)

1. **`recordatorio_diario_morning.yaml`** — cada día 7:30 → consultar recordatorios del día → mandar Telegram a Angel (y África si tiene)
2. **`itv_coche_3_meses.yaml`** — si `coche/INDEX.md` indica ITV en próximos 90 días → Telegram con "Reserva cita ITV antes de DD/MM"
3. **`recurrente_alerta_dia_anterior.yaml`** — un día antes de cada cargo recurrente → notificar

## Bot Telegram (mejora paralela)

Hoy bot_v2.py tiene 7 tools de Claude. Evolución:
- Comandos rápidos para añadir gasto, compra, recordatorio sin abrir el cockpit
- `/gasto 45 gasolina` → llama `gasto_anotar`
- `/compra leche` → llama `lista_compras_añadir`
- `/recordar mañana 18h pediatra Bris` → llama `recordatorio_crear`
- Respuestas naturales generadas por Claudio con su nueva personalidad

## Voice assistant (PWA Android + Linux casa)

Hoy entiende dictado para nota_capturada. Con Jarvis:
- Detecta intent: ¿es nota? ¿es gasto? ¿es recordatorio? ¿es pregunta?
- Router a la herramienta correcta
- Confirma con voz natural: "He apuntado 45€ de gasolina. Te quedan 230€ del presupuesto del mes."

En Fase 1 SOLO se preparan los hooks; la integración real con el dictado se hace en Fase 2.

## Stack

NADA NUEVO. Reutiliza:
- FastMCP server (extender mcp_server.py)
- Vault markdown
- Bot Telegram (extender bot_v2.py)
- Automation Engine (añadir ejemplos)
- Cockpit (preparado para widgets futuros)

Únicas dependencias nuevas: ninguna. Todo es Python + markdown.

## Constraints

- NO mover ni borrar nada del vault existente
- Tests para cada tool nuevo (mock vault temporal)
- Documentación viva en `claudio/IDENTIDAD.md` que se lee en cada nuevo proyecto
- Bug telegram_enviar conocido: solo Telegram final, mensaje OPUS_MOBILE_FALLBACK si cuelga
- Logueo estructurado en `claudio/logs/YYYY-MM-DD.jsonl` de cada llamada a tool
- Privacidad: medicación y salud requieren autor explícito, nunca acción anónima

## Flujo Spec Kit

1. `/speckit-specify` desde este BRIEF (spec del Fase 1)
2. `/speckit-clarify` — solo si crítico
3. `/speckit-plan` — extensión MCP server + vault structure + tests
4. `/speckit-tasks` — agrupado por dominio (familia, finanzas, compras, coche, documentos, salud, claudio_identity, automations)
5. `/speckit-implement` — ejecuta sin parar

## Definition of Done Fase 1

- Vault tiene los 11 nuevos directorios con README.md inicial cada uno
- `claudio/IDENTIDAD.md` y `claudio/personalidad.md` redactados con voz y profundidad real (no placeholders)
- ~22 tools MCP nuevos implementados y testeados
- 3 automations YAML de ejemplo creadas con activo:false
- Bot Telegram acepta `/gasto`, `/compra`, `/recordar` mínimo
- mcp_server.py restartado para cargar los tools nuevos
- Documentación `claudio/IDENTIDAD.md` legible y útil
- Commit conventional por dominio (8 commits aprox)

## Roadmap completo (no Fase 1, contexto para futuras tandas)

- **Fase 1** (esta): foundation familiar, vault + tools MCP + identidad
- **Fase 2**: integración con dictado del voice assistant (intent routing)
- **Fase 3**: widgets cockpit familiares (recordatorios, gastos, compras, menú, coche)
- **Fase 4**: integraciones externas (weather, mapas, Home Assistant si aplica, Spotify)
- **Fase 5**: pro-actividad (Claudio sugiere antes de que pregunten)
- **Fase 6**: modo niños (cuando lleguen)
- **Fase 7**: OCR + ingestión automática de PDFs/fotos de facturas

## Estimación Fase 1

Trabajo humano: 2-3 semanas. Claude Code: 4-6h.

---
*BRIEF preparado por Claude Opus 4.7 (sesión móvil), 2026-05-13 ~20:00 UTC*
*Visión a largo plazo discutida con Angel — "el homme à tout faire digital de la familia"*
