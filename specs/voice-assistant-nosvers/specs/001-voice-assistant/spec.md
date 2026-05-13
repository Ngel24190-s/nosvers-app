# Feature Specification: Asistente de Voz Personal NosVers

**Feature Branch**: `001-voice-assistant`

**Created**: 2026-05-12

**Status**: Draft

**Input**: User description: "Asistente de voz personal NosVers multi-dispositivo. Captura por voz desde móvil Android (PWA offline-first con buffer IndexedDB) y desde ordenador Linux casa (wake word custom Claudio + STT/TTS local). Persiste en vault knowledge_base/angel/dia/ con clasificación automática por Haiku. Resúmenes diarios y semanales por agente nuevo agt07_diario. Tres tools nuevos en nosvers-mcp-2026: dia_capturar, dia_contexto, dia_buscar. Contexto completo en BRIEF.md de la raíz del proyecto."

## Clarifications

### Session 2026-05-12

Las decisiones de BRIEF §11 (wake word `Claudio`, voz TTS regulable, español
por defecto) y §12 (clasificación Haiku en VPS, audio TTL 7 días, PWA con
buffer offline, agente `agt07_diario`) ya están integradas como FRs en este
spec. Las decisiones siguientes son autónomas (defaults razonables aplicados
para no bloquear la marcha del proyecto) y pueden revisarse en cualquier
momento sin invalidar la spec.

- **Captura en móvil — Push-to-talk en MVP, no wake word**.
  - Razón: el wake word custom requiere entrenamiento dedicado del modelo y
    consume batería de forma continua. Para el MVP la captura por botón es
    suficiente y mantiene el scope ajustado. Si Angel quiere manos-libres
    conduciendo puede recurrir a un intent del dictado nativo Android +
    "Compartir → PWA NosVers". Wake word en móvil queda fuera de scope MVP.
- **PWA STT — Server-side (Opción B del BRIEF §12.3)**.
  - Razón: simplifica el bundle de la PWA (no carga modelo Whisper ~30MB
    en cliente), no exige WASM pesado, mantiene soberanía porque el audio
    se transcribe en el propio VPS de Angel sobre HTTPS. La PWA envía el
    Opus comprimido al endpoint `dia_capturar` y el VPS transcribe con
    Whisper local antes de clasificar con Haiku y persistir.
- **Idioma de dictado — Detección automática multilingüe (es/fr)**.
  - Razón: Angel mezcla castellano interno y francés para contenido público
    NosVers. El motor STT (Whisper) ya soporta autodetección.
- **TTL audio en PWA — Espejo del servidor (7 días)**.
  - Razón: coherencia con la política de privacidad del VPS y evita que el
    móvil acumule audios indefinidamente.
- **Notificación Telegram de resúmenes — Opt-in, off por defecto en MVP**.
  - Razón: el resumen queda en el vault y es consultable desde la PWA o por
    voz. Empujarlo a Telegram cada noche puede saturar el chat. Angel
    activa la notificación con un parámetro de configuración cuando lo
    quiera.
- **Auto-cierre de sesión por inactividad post-wake-word — 8 segundos**.
  - Razón: ventana razonable para que Angel termine de pensar la frase tras
    decir "Claudio". Suficiente para no cortar pero corto para no dejar
    micrófono abierto en silencio.
- **Icono de la PWA — Calculín (libro gordo de Petete) provisto por Angel**.
  - Razón: identidad personal, instalable en pantalla de inicio del Android.
    Angel proporciona PNG 192×192 y 512×512 (rutas
    `pwa/assets/icon-192.png` y `pwa/assets/icon-512.png`). Mientras no
    estén, se usa un placeholder neutro NosVers para no bloquear el deploy.
    Uso doméstico/personal, single user — sin distribución pública.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Captura por voz desde el móvil durante la jornada (Priority: P1)

Angel conduce entre dos obras de DI Environnement. Le surge una idea para NosVers
("hay que pedir a África las fotos del extracto vivo antes del viernes"). Coge el
móvil, abre el icono del asistente en la pantalla de inicio del Android, pulsa
grabar, dicta la nota, suelta. La aplicación le confirma visualmente que la nota
quedó guardada — aunque en ese tramo de carretera no haya cobertura. Cuando recupera
señal minutos después, la nota se sincroniza sola al vault del VPS y aparece en la
entrada del día con su timestamp original y una etiqueta automática (`nosvers`).

**Why this priority**: Es el caso de uso de mayor frecuencia y mayor valor — Angel
pasa la mayor parte del día fuera del despacho. Si esto no funciona, el resto del
sistema no tiene sustrato. Es además el caso que la app oficial de Claude no
resuelve hoy (no soporta offline-first con buffer local).

**Independent Test**: Apagar la red móvil del teléfono, dictar tres notas con
intervalos de minutos, reactivar la red, verificar que las tres aparecen en
`knowledge_base/angel/dia/YYYY-MM-DD.md` con sus timestamps originales y
etiquetadas.

**Acceptance Scenarios**:

1. **Given** el teléfono tiene cobertura y la PWA está abierta, **When** Angel
   dicta una nota y la confirma, **Then** la nota aparece en la entrada del día
   en el vault en menos de 5 segundos con timestamp ISO y etiqueta automática.
2. **Given** el teléfono está sin cobertura, **When** Angel dicta una nota,
   **Then** la PWA muestra confirmación visual de captura, encola la nota
   localmente y marca su estado como "pendiente de sync".
3. **Given** hay notas pendientes de sync en el buffer local, **When** el
   teléfono recupera conexión a internet, **Then** todas las notas pendientes
   se envían al VPS automáticamente sin acción del usuario y desaparecen de la
   cola local.
4. **Given** una nota se acaba de sincronizar, **When** se inspecciona la
   entrada del día en el vault, **Then** la nota conserva el timestamp del
   momento de dictado, no el de sincronización.
5. **Given** la clasificación automática falla o tarda más de 3 segundos,
   **When** la nota llega al VPS, **Then** se guarda con etiqueta `otro` y
   queda registrada para reclasificación posterior, sin bloquear al usuario.

---

### User Story 2 - Recuperar contexto sintético bajo demanda (Priority: P2)

Angel termina un día de obra y, ya en el coche de vuelta, pregunta a Claude desde
el móvil: "¿qué dejé pendiente esta semana para NosVers?". Claude responde con un
resumen sintético de las últimas N entradas del vault filtradas por contexto
NosVers, junto con los eventos del calendario relacionados y el estado de los
agentes activos relevantes. Angel decide en función de eso si pasar por la
ferme antes de llegar a casa.

**Why this priority**: La captura sin recuperación es un diario muerto. Esta
historia convierte el vault en un segundo cerebro accionable. Es la segunda capa
de valor — sin la P1 no hay datos; con sólo P1 no hay decisión.

**Independent Test**: Con al menos 5 entradas dictadas en los últimos 3 días,
pedir a Claude el contexto de los últimos 7 días → debe devolver síntesis
estructurada con notas relevantes + eventos de calendario próximos + estado
agentes, en bajo 10 segundos.

**Acceptance Scenarios**:

1. **Given** existen entradas en el vault de los últimos 7 días, **When** Angel
   pide contexto a Claude, **Then** la respuesta incluye una síntesis de las
   notas, eventos próximos del calendario y el estado de los agentes activos.
2. **Given** Angel especifica un rango distinto (ej. "últimos 3 días"),
   **When** se solicita contexto, **Then** la síntesis se restringe a ese
   rango.
3. **Given** Angel pide contexto sin incluir calendario, **When** se invoca la
   herramienta, **Then** la respuesta omite los eventos y se centra en notas
   y agentes.
4. **Given** el vault tiene cero entradas en el rango pedido, **When** se
   solicita contexto, **Then** la respuesta indica explícitamente que no hay
   actividad registrada y sugiere ampliar el rango.

---

### User Story 3 - Activación manos-libres en el ordenador de casa (Priority: P3)

Angel está en casa frente a su ordenador Linux. Tiene las manos ocupadas
(cenando, cargando al pequeño, etc.). Dice "Claudio" y, sin tocar nada, se abre
una sesión con Claude que le escucha. Pregunta por voz lo que necesita y la
respuesta llega también por voz, en castellano, a velocidad de conversación
humana, sin sonar a robot. Si quiere que hable más rápido, lo dice y Claude
ajusta.

**Why this priority**: Cierra el círculo de "asistente multi-dispositivo". No es
crítico para arrancar — el móvil cubre el grueso del día — pero es el único
canal manos-libres real y completa la promesa del proyecto.

**Independent Test**: Decir "Claudio" frente al micrófono del ordenador → la
sesión arranca con confirmación auditiva en menos de 1.5 segundos. Hacer una
pregunta sencilla → recibir respuesta en castellano con voz natural, sin que la
propia respuesta dispare un nuevo wake word.

**Acceptance Scenarios**:

1. **Given** el ordenador está en reposo con el detector de wake word activo,
   **When** Angel dice "Claudio" con voz normal a 1-3m del micrófono, **Then**
   la sesión arranca en menos de 1.5s y emite un sonido o frase corta de
   confirmación.
2. **Given** la sesión está activa y Claude está hablando, **When** la
   respuesta contiene de forma incidental la palabra "Claudio" o similar,
   **Then** el wake word no se vuelve a disparar (cooldown o supresión durante
   playback).
3. **Given** Angel está hablando en castellano con Claude, **When** dice "habla
   más despacio" o "habla más rápido", **Then** la velocidad del TTS se ajusta
   inmediatamente en la siguiente frase emitida.
4. **Given** Angel está trabajando contenido NosVers en francés, **When** lo
   indica, **Then** Claude cambia el idioma de la voz a francés y mantiene el
   cambio durante la sesión.
5. **Given** el wake word detector tiene un falso positivo, **When** la sesión
   se abre sin que Angel hable después en X segundos, **Then** la sesión se
   cierra sola sin dejar grabación abierta.

---

### User Story 4 - Resúmenes diarios y semanales automáticos (Priority: P4)

Cada noche a las 23:30, sin que Angel haga nada, un agente del sistema lee todas
las entradas del día, las sintetiza en un resumen corto (5-8 líneas), extrae las
ideas y pendientes detectados, calcula la distribución de etiquetas del día y lo
deja en el vault. Los domingos a las 22:00 lo mismo pero abarcando los últimos
7 días, con más profundidad de síntesis. Opcionalmente Angel recibe el resumen
en Telegram.

**Why this priority**: Automatiza la reflexión que de otra forma Angel no se va
a sentar a hacer. Convierte el diario en feedback semanal de comportamiento.
Valor alto pero no bloqueante: el sistema vive sin él, los datos quedan
igualmente capturables y consultables.

**Independent Test**: Tener al menos 3 entradas en el día → esperar a las 23:30
o disparar manualmente el agente → comprobar que aparece
`knowledge_base/angel/dia/resumenes/YYYY-MM-DD.md` con resumen, ideas/pendientes
y gráfico de etiquetas.

**Acceptance Scenarios**:

1. **Given** existen entradas para el día en curso, **When** se ejecuta el
   agente de resumen diario (cron o manual), **Then** se crea el archivo de
   resumen en `dia/resumenes/YYYY-MM-DD.md` con 5-8 líneas de síntesis, lista
   de ideas/pendientes detectados y un gráfico textual de etiquetas
   dominantes.
2. **Given** es domingo a las 22:00 y existen entradas en los últimos 7 días,
   **When** se ejecuta el agente semanal, **Then** se crea un resumen semanal
   con mayor profundidad de síntesis que el diario.
3. **Given** Angel ha activado la notificación por Telegram, **When** se
   completa un resumen, **Then** recibe el resumen en su chat privado.
4. **Given** el día tuvo cero entradas, **When** el agente se ejecuta, **Then**
   no crea archivo de resumen vacío y registra en su log "sin actividad".

---

### User Story 5 - Búsqueda histórica por palabras y rango de fechas (Priority: P5)

Angel recuerda haber dictado algo sobre "lombrithé tibio" hace unas semanas pero
no localiza la entrada. Pide a Claude que lo busque en sus notas → recibe la
lista de entradas que contienen el término con su fecha y un fragmento de
contexto.

**Why this priority**: Conveniencia de archivo. Útil cuando el volumen de notas
crezca, pero no aporta valor inmediato en las primeras semanas de uso. Es una
historia P5 (nice-to-have) que cierra el ciclo captura → consulta → recuperación
puntual.

**Independent Test**: Dictar 10 notas con términos variados en varios días →
pedir a Claude que busque uno de los términos → recibir las entradas con fecha
y fragmento de contexto.

**Acceptance Scenarios**:

1. **Given** existen entradas que contienen un término concreto, **When** Angel
   pide buscarlo, **Then** la respuesta lista las entradas con fecha y un
   fragmento de la frase que contiene el término.
2. **Given** Angel acota la búsqueda con fechas `desde`/`hasta`, **When** se
   ejecuta, **Then** los resultados sólo incluyen entradas dentro de ese rango.
3. **Given** no hay coincidencias, **When** se ejecuta la búsqueda, **Then** la
   respuesta lo indica explícitamente sin error.

---

### Edge Cases

- **Sin cobertura prolongada (varios días)**: la PWA debe bufferizar todas las
  notas en local. El sistema no puede asumir nunca que la sincronización
  ocurrirá pronto.
- **Audio en local pero el VPS ya borró su contraparte**: la referencia
  `[audio: HH-MM-SS.opus]` en el transcript queda rota; el sistema acepta esa
  rotura silenciosa (decisión documentada en BRIEF §12.2).
- **Haiku timeout en clasificación**: fallback a `otro` + log para
  reclasificación.
- **Wake word custom "Claudio" no detectado por el modelo stock**: requiere
  modelo entrenado a medida — el sistema debe degradar a una alternativa
  push-to-talk si el detector no alcanza un umbral de fiabilidad mínimo.
- **TTS auto-dispara wake word**: la respuesta de Claude contiene la palabra o
  un sonido similar → debe haber cooldown o supresión del detector durante el
  playback.
- **Falso positivo de wake word con la sesión abierta y sin habla**: la sesión
  debe cerrarse sola tras un timeout sin actividad de usuario.
- **Notas dictadas simultáneamente desde dos dispositivos** (improbable pero
  posible si Angel cambia de canal): ambas notas se preservan en el día con
  sus respectivos timestamps; no se hace deduplicación destructiva.
- **Cambio de idioma a mitad de sesión**: el sistema reconoce la orden y
  cambia el idioma de salida sin reiniciar la sesión.
- **Vault temporalmente bloqueado por otro proceso** (agente cron escribiendo a
  la vez): la escritura se reintenta con backoff hasta 3 veces antes de fallar
  y notificar.
- **Calendario externo inaccesible**: `dia_contexto` con `incluir_calendario`
  devuelve la parte de notas + agentes y marca calendario como "no disponible".
- **Audio mayor de 7 días intentando reproducirse**: el archivo ya fue purgado;
  el transcript se devuelve sin enlace de audio.
- **Resumen diario lanzado sin que el día tenga entradas**: no crea archivo
  vacío.

## Requirements *(mandatory)*

### Functional Requirements

#### Captura

- **FR-001**: El sistema MUST permitir capturar notas habladas desde el móvil
  Android de Angel mediante una aplicación instalable en la pantalla de inicio.
- **FR-002**: La aplicación móvil MUST funcionar sin conexión a internet,
  almacenando las notas en un buffer local persistente hasta que recupere
  conexión.
- **FR-003**: La aplicación móvil MUST mostrar feedback visual inmediato (en
  menos de 500ms) confirmando que la nota se ha capturado, independientemente
  del estado de la red.
- **FR-004**: Las notas pendientes en el buffer local MUST sincronizarse
  automáticamente al VPS cuando la conexión vuelva, sin requerir acción del
  usuario.
- **FR-005**: Cada nota MUST preservar el timestamp del momento de dictado, no
  el de sincronización.
- **FR-006**: El sistema MUST permitir capturar notas por voz desde el
  ordenador Linux de Angel sin tocar teclado ni ratón, mediante detección de
  la palabra de activación `Claudio`.
- **FR-007**: El detector de wake word MUST tener cooldown o supresión durante
  el playback del TTS para evitar autodisparos.
- **FR-008**: El sistema MUST cerrar automáticamente la sesión si tras
  detectar el wake word no hay habla del usuario en un intervalo razonable.

#### Persistencia y clasificación

- **FR-009**: Cada nota capturada MUST persistirse como entrada de texto en el
  archivo del día en el vault, bajo `knowledge_base/angel/dia/YYYY-MM-DD.md`,
  con timestamp ISO.
- **FR-010**: Cada nota MUST recibir una etiqueta automática entre
  `trabajo` | `nosvers` | `familia` | `mental` | `idea` | `otro`,
  determinada por un modelo de clasificación rápido.
- **FR-011**: Si la clasificación automática falla o excede 3 segundos, el
  sistema MUST etiquetar como `otro` y registrar el evento para reclasificación
  posterior, sin bloquear la captura.
- **FR-012**: El prompt usado para la clasificación MUST vivir en el vault
  (`knowledge_base/angel/prompts/clasificar_nota.md`) y ser editable sin
  redespliegue del código.
- **FR-013**: El audio crudo del dictado MUST conservarse máximo 7 días bajo
  `knowledge_base/angel/dia/audio/YYYY-MM-DD/HH-MM-SS.opus` y ser borrado
  automáticamente por un proceso programado a partir del día 8.
- **FR-014**: Cada entrada de transcript MUST referenciar su archivo de audio
  asociado mientras éste exista; la referencia puede romperse silenciosamente
  cuando el audio expira.

#### Recuperación de contexto

- **FR-015**: El sistema MUST permitir, bajo demanda, devolver una síntesis del
  contexto reciente: entradas de las últimas N días, eventos próximos del
  calendario externo de Angel y estado de los agentes activos del proyecto.
- **FR-016**: La síntesis MUST poder restringirse por rango de días y
  configurarse para incluir o excluir el calendario.
- **FR-017**: Si el calendario externo no está accesible, el sistema MUST
  devolver el resto de la síntesis y marcar explícitamente la indisponibilidad
  del calendario.
- **FR-018**: El sistema MUST permitir búsqueda textual en las entradas del
  diario, opcionalmente acotada por rango de fechas, devolviendo la lista de
  coincidencias con fecha y un fragmento de contexto.

#### Resúmenes automáticos

- **FR-019**: El sistema MUST generar automáticamente un resumen diario de las
  entradas del día a las 23:30 hora Europe/Paris, almacenado en
  `knowledge_base/angel/dia/resumenes/YYYY-MM-DD.md`.
- **FR-020**: El resumen diario MUST contener: 5-8 líneas de síntesis,
  ideas/pendientes detectados, y un gráfico textual de distribución de
  etiquetas del día.
- **FR-021**: El sistema MUST generar automáticamente un resumen semanal los
  domingos a las 22:00 hora Europe/Paris, leyendo los 7 días previos, con mayor
  profundidad de síntesis que el diario.
- **FR-022**: Cuando un día tiene cero entradas, el sistema MUST NO crear
  archivo de resumen y MUST registrar el hecho en su log.
- **FR-023**: El sistema MUST permitir, opcionalmente, notificar a Angel los
  resúmenes vía Telegram.

#### Voz (TTS / STT / Wake word)

- **FR-024**: La voz de respuesta MUST sonar fluida y natural, no robótica ni
  cantada ni arrastrada.
- **FR-025**: La velocidad de la voz MUST ser regulable por el usuario, tanto
  mediante configuración como en runtime ("habla más rápido / más despacio").
- **FR-026**: La velocidad por defecto MUST corresponder a ritmo natural de
  conversación humana.
- **FR-027**: La voz MUST poder hablar en español castellano por defecto y
  cambiar a francés bajo orden explícita del usuario, manteniendo el cambio
  durante la sesión.
- **FR-028**: El proceso de speech-to-text MUST ejecutarse de forma que el
  audio de Angel no salga del dispositivo o servidor controlado por NosVers,
  salvo decisión técnica explícitamente justificada en el plan.
- **FR-029**: El wake word MUST ser `Claudio` (no `Claude`), con un detector
  capaz de distinguirlo dentro del habla natural en castellano sin disparos
  frecuentes por falsos positivos.

#### Integridad operativa

- **FR-030**: La autenticación de la aplicación móvil MUST hacerse con un
  token revocable emitido por el servidor del proyecto, almacenado localmente
  en el dispositivo. Credenciales reutilizables (usuario/contraseña, API keys
  con scope amplio) están prohibidas en el cliente.
- **FR-031**: El sistema MUST poder anular un token concreto sin afectar a
  otros dispositivos o tokens activos.
- **FR-032**: Los logs del sistema MUST redactar tokens y secretos antes de
  persistirse, y MUST rotar para no crecer sin límite.
- **FR-033**: La introducción del asistente MUST NO causar regresión sobre
  componentes existentes del proyecto NosVers (unified-agent, agentes cron,
  bot Telegram, WordPress). Cualquier cambio en estos componentes MUST ser
  estrictamente aditivo y reversible.
- **FR-034**: Antes de desplegar los clientes (móvil y Linux casa), el sistema
  MUST notificar a Angel para que se ejecute una revisión de seguridad sobre
  la infraestructura existente.

### Key Entities

- **Nota dictada (entrada de día)**: Texto con timestamp ISO, etiqueta
  semántica (`trabajo`/`nosvers`/`familia`/`mental`/`idea`/`otro`), origen
  (`voz_movil`/`voz_linux`/`otro`), referencia opcional al audio asociado.
  Vive como bloque dentro del archivo del día.
- **Archivo del día**: Markdown bajo `knowledge_base/angel/dia/YYYY-MM-DD.md`
  que contiene la cronología de notas del día. Verdad permanente.
- **Audio efímero**: Archivo `.opus` bajo
  `knowledge_base/angel/dia/audio/YYYY-MM-DD/HH-MM-SS.opus`. TTL 7 días.
- **Resumen del día / de la semana**: Markdown bajo
  `knowledge_base/angel/dia/resumenes/`. Generado por agente, derivable de los
  archivos del día.
- **Prompt de clasificación**: Markdown bajo
  `knowledge_base/angel/prompts/clasificar_nota.md`. Editable a mano sin
  redespliegue.
- **Sesión de voz**: Ventana temporal de interacción manos-libres en el
  ordenador de casa. Inicia con detección de wake word, se cierra por
  inactividad o por orden explícita.
- **Cola local de notas pendientes**: Estructura persistente en el dispositivo
  móvil que retiene notas dictadas mientras no hay red. Cada elemento conserva
  el timestamp original de dictado.
- **Token de cliente**: Credencial revocable emitida por el servidor para
  autenticar la aplicación móvil contra los servicios del proyecto.
- **Agente de resumen (agt07_diario)**: Proceso programado que lee los
  archivos del día, los sintetiza, y escribe los resúmenes diarios y
  semanales.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Angel puede dictar una nota desde el móvil mientras conduce sin
  cobertura y comprobar al llegar a casa que la nota está en el vault con su
  timestamp original — en el 100% de las veces que ese caso ocurra.
- **SC-002**: El tiempo desde que Angel termina de dictar una nota con
  cobertura hasta que ésta aparece en el vault es inferior a 5 segundos
  end-to-end.
- **SC-003**: La aplicación móvil retiene al menos 24 horas de notas
  acumuladas sin conexión sin perder ninguna.
- **SC-004**: La clasificación automática acierta la etiqueta en al menos el
  80% de las notas en una muestra representativa de uso real durante la
  primera semana de funcionamiento.
- **SC-005**: La síntesis de contexto bajo demanda llega a Angel en menos de
  10 segundos desde la pregunta, cuando hay menos de 50 entradas en el rango
  pedido.
- **SC-006**: La detección del wake word `Claudio` tiene una tasa de falsos
  positivos inferior a 1 por hora en uso doméstico normal de Angel
  (conversaciones, audio de fondo, televisión).
- **SC-007**: El tiempo desde decir `Claudio` hasta recibir confirmación
  auditiva de la sesión es inferior a 1.5 segundos.
- **SC-008**: La voz de respuesta es percibida por Angel como "natural"
  (criterio cualitativo: Angel aprueba explícitamente la voz como aceptable
  tras al menos 3 sesiones de uso real).
- **SC-009**: Los resúmenes diarios se generan automáticamente cada noche a
  las 23:30 en al menos el 95% de los días con actividad, sin intervención
  manual.
- **SC-010**: La búsqueda histórica devuelve resultados relevantes con su
  fragmento de contexto en menos de 3 segundos para un vault de hasta 12
  meses de notas.
- **SC-011**: Cero regresiones detectadas en los componentes existentes
  (unified-agent, agentes cron, bot Telegram, WordPress, ventas Stripe)
  durante las dos semanas siguientes al despliegue del asistente.
- **SC-012**: Audio crudo en el VPS nunca permanece más de 7 días: un sondeo
  manual en cualquier momento sobre `knowledge_base/angel/dia/audio/`
  encuentra exclusivamente archivos de los últimos 7 días.

## Assumptions

- **Usuario único**: el asistente lo usa exclusivamente Angel. África y otros
  miembros del entorno NO son usuarios de este sistema en esta versión.
- **Dispositivo móvil**: Android moderno con Chrome o navegador con soporte
  para PWA, MediaRecorder API y Background Sync.
- **Ordenador casa**: Linux con micrófono y altavoces operativos. El stack
  exacto (distribución, audio backend) se decide en `/speckit-plan`.
- **Cobertura intermitente**: la PWA debe funcionar offline-first como
  contrato base, no como degradación.
- **Calendario externo**: existe acceso al Google Calendar de Angel a través
  del entorno actual del proyecto.
- **MCP base**: el servidor MCP `nosvers-mcp-2026` ya existe y se amplía con
  los tools nuevos del proyecto. No se construye un servidor MCP paralelo.
- **Vault como verdad**: todo dato persistente del asistente vive en el vault.
  No hay bases de datos paralelas para datos de usuario.
- **Modelo de clasificación rápido**: existe un modelo capaz de etiquetar
  textos cortos con coste y latencia compatibles con el caso de uso (decisión
  de modelo concreto en `/speckit-plan`).
- **Idioma primario de interacción**: castellano. El francés está soportado
  como segundo idioma para contenido público NosVers.
- **Privacidad y soberanía**: prevalecen sobre conveniencia salvo
  justificación explícita en el plan técnico.
- **Compatibilidad de plataformas STT/TTS local**: existe al menos una
  combinación de tecnologías open-source que cumple los requisitos de
  naturalidad y velocidad regulable (decisión concreta en `/speckit-plan`).
- **No reinventar**: cualquier funcionalidad ya cubierta por los tools
  existentes del MCP (`vault_*`, `telegram_enviar`, `agente_ejecutar`, etc.)
  se reutiliza, no se duplica.
