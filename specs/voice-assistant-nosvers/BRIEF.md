# Brief — Asistente de Voz Personal NosVers

Documento de handoff inicial. Lee esto antes de ejecutar `/speckit-constitution`.

---

## 1. Quién es el usuario

**Angel** — CEO y lead técnico de NosVers (granja de vermicultura y agroecología en Neuvic, Dordogne). Su vida profesional tiene dos polos:

- **DI Environnement Sud Ouest**: Conducteur de Travaux en desamiantage. Trabajo de campo + supervisión, mucho tiempo fuera del despacho.
- **NosVers**: proyecto que está convirtiendo en su sustento principal. África (esposa) es co-fundadora y directora de campo.

Valores no negociables que afectan el diseño:
- **Soberanía tecnológica**: open-source, stack propio, sin vendor lock-in
- **RESILIENCIA** (camino) y **SOBERANÍA** (destino) como guías
- Habla en español con Claude (interno). Contenido público NosVers en francés.

## 2. El problema que resolvemos

Angel quiere un **asistente personal por voz multi-dispositivo** que:

1. Capture sus pensamientos y contexto durante el día — tanto del trabajo en DI Environnement, como de NosVers, como cualquier cosa cotidiana o "movida mental"
2. Le devuelva ese contexto cuando lo necesite, de forma sintética
3. Pueda controlar el ordenador de casa Y el VPS de NosVers
4. Funcione desde el móvil Android (donde pasa la mayor parte del día) Y desde el ordenador Linux en casa

No es un asistente de productividad genérico. Es **un segundo cerebro con voz**, anclado en SU infraestructura, con SU vault como memoria persistente.

## 3. Infraestructura existente — NO REINVENTAR

Todo esto YA está montado y funcionando:

| Componente | Ubicación | Estado |
|---|---|---|
| VPS Ubuntu (este servidor) | 72.61.160.108 | Activo |
| WordPress + WooCommerce | `nosvers.com` | Stripe live |
| Vault (knowledge base) | `/home/nosvers/public_html/knowledge_base/` | Source of truth |
| Unified agent | `/home/nosvers/unified-agent/` | Docker, Haiku ejecutor + Opus advisor |
| MCP server propio | `nosvers-mcp-2026` (https://nosvers-mcp.72.61.160.108.nip.io/mcp) | 12 tools, listado abajo |
| Bot Telegram | Chat directo con Angel | Activo |
| Claude Code 2.1.76 | `/usr/bin/claude` | OAuth Claude Max |
| Python 3.12.3 + uv 0.11.13 | Instalados | Listos |

**Herramientas del MCP `nosvers-mcp-2026`** (ya existen, NO crear duplicados):
- `sistema_estado`, `ejecutar_comando`, `git_pull_vps`, `deploy_vps`
- `agente_ejecutar`, `agente_logs`, `agentes_estado`
- `telegram_enviar`, `vault_leer`, `vault_escribir`, `vault_listar`
- `wp_crear_post`

Conectores activos en Claude.ai: Google Calendar, Gmail, Google Drive, Figma, Stripe, Canva, WordPress, Magic Patterns, Netlify, Ahrefs, nosvers-mcp-2026.

## 4. Requisitos funcionales (lo que debe hacer)

### Captura
- Hablar al móvil Android desde cualquier lugar y que se guarde con timestamp + etiqueta automática (`trabajo` | `nosvers` | `familia` | `mental` | `idea` | `otro`)
- Hablar al ordenador de casa con wake word ("Hey Claude" o lo que se decida) sin tocar teclado
- Todo se persiste en el vault bajo `knowledge_base/angel/dia/YYYY-MM-DD.md` (o estructura equivalente a decidir)

### Contexto
- Bajo demanda, dar a Claude el contexto sintético de los últimos N días (entradas + calendario + estado agentes)
- Resúmenes diarios/semanales automáticos generados por un agente del unified-agent

### Control
- Desde móvil: ejecutar comandos en el VPS, leer/escribir vault, lanzar agentes, todo lo que el MCP ya permite
- Desde casa Linux: lo mismo + control del ordenador local

## 5. Stack candidato (a decidir en /speckit-plan)

**Para el móvil Android**: la opción más limpia es **Claude Code Remote Control** (feature nativa Anthropic, febrero 2026). Lanza una sesión Claude Code en el VPS dentro de tmux con `/remote-control`, conectas la app Claude Android. La voz la pone el dictado nativo Android. **Cero código nuevo, máxima integración**.

**Para Linux casa** (ordenador de Angel, no este VPS): tres candidatos investigados:
1. **VoiceMode MCP server** (v8.2.0, MIT) — añade voz a Claude Code como MCP. Whisper.cpp + Kokoro TTS local. El más coherente con el stack MCP-first de NosVers.
2. **4rdii/claude-listener** — always-on Whisper + Ollama clasificador, escribe a vault. Linux+Mac.
3. **synthia-ai.com** — específico Linux, también con remote via Telegram (encaja con AEGIS/ALAMO).

**Decisión recomendada**: VoiceMode MCP como base, complementado por un par de tools nuevos en `nosvers-mcp-2026` (ver punto 6).

## 6. Tools nuevos a añadir a `nosvers-mcp-2026`

Son la pieza que cierra el ciclo. Deben implementarse en el código del MCP server existente:

- `dia_capturar(texto: str, etiqueta: str = "auto", origen: str = "voz")` 
  → Escribe entrada en `knowledge_base/angel/dia/YYYY-MM-DD.md` con timestamp ISO y etiqueta. Si `etiqueta=="auto"`, clasifica con Haiku.
  
- `dia_contexto(rango_dias: int = 7, incluir_calendario: bool = True)` 
  → Devuelve síntesis de las últimas N entradas + eventos calendario próximos + estado agentes activos. Output cacheable.

- `dia_buscar(query: str, desde: str = None, hasta: str = None)` 
  → Búsqueda full-text en las entradas del diario por rango de fechas.

## 7. Constraints técnicos

- **Soberanía**: nada de servicios cloud propietarios para STT/TTS si hay alternativa local viable (Whisper local, Piper TTS, etc.). API de Anthropic SÍ se usa (es el cerebro).
- **MCP-first**: cualquier funcionalidad nueva expuesta como tool MCP, no como endpoint REST aislado.
- **Vault es source of truth**: nada de bases de datos paralelas. Markdown en `knowledge_base/`.
- **Docker sandbox**: cualquier servicio nuevo va dentro del Dockerfile del unified-agent o como contenedor propio, no procesos sueltos en el host.
- **Idempotencia y logs**: todo en `/home/nosvers/logs/` con rotación.
- **No romper lo que funciona**: el unified-agent, los cron, el bot Telegram, la web WordPress NO se tocan salvo para añadir tools al MCP.

## 8. ~~Decisiones abiertas~~ — CERRADAS (ver sección 12)

1. ¿Wake word personalizado o "Hey Claude" estándar?
2. ¿La clasificación de etiqueta automática se hace en cliente (Linux) o en el VPS vía Haiku?
3. ¿El audio crudo se conserva o solo el transcript? (privacidad vs trazabilidad)
4. ¿Cómo se sincroniza si Angel habla offline en el móvil sin cobertura?
5. ¿Los resúmenes diarios los genera un agente nuevo del unified-agent o uno existente extendido?

## 9. Definition of done

- Angel puede dictar al móvil mientras conduce entre obras de DI Environnement → la entrada queda en el vault del VPS antes de llegar a casa
- Angel puede preguntar "¿qué tenía pendiente para NosVers esta semana?" desde el móvil y Claude responde con contexto real del vault
- Angel puede decir "Hey Claude" en su ordenador de casa → empieza sesión sin tocar nada
- AEGIS y los agentes existentes siguen funcionando sin regresiones
- Toda la pieza nueva tiene su entrada en `EVOLUTION_ROADMAP.md`

## 10. Flujo Spec Kit a seguir

1. `/speckit-constitution` — fija los principios del proyecto (soberanía, MCP-first, vault-anchored, no-regresión)
2. `/speckit-specify` — escribe la spec funcional completa desde este brief
3. `/speckit-clarify` — resuelve las 5 decisiones abiertas del punto 8
4. `/speckit-plan` — plan técnico, eligiendo stack definitivo
5. `/speckit-tasks` — desglose en tareas testables
6. `/speckit-implement` — ejecutar

**Cuando termines la implementación, avisa a Angel por Telegram para que Claude (Opus, vía la app) haga la revisión de seguridad sobre la infraestructura existente antes del deploy.**

---

*Brief escrito por Claude (Opus 4.7) desde la app móvil de Angel, 2026-05-12.*

---

## 11. Resoluciones del usuario (2026-05-12)

Decisiones del punto 8 ya cerradas por Angel:

### Wake word
- **Palabra de activación**: `Claude` (sola, no "Hey Claude")
- ⚠️ Nota técnica para `/speckit-plan`: "Claude" es una palabra muy común en cualquier conversación que Angel mantenga con la IA, así que el modelo de wake word necesita umbral de confianza alto y/o un detector entrenado específicamente para minimizar falsos positivos. Si openWakeWord no da la fiabilidad necesaria, considerar Picovoice Porcupine (modelo custom entrenable) o un modelo entrenado a medida.

### Voz de respuesta (TTS)
- **Naturalidad**: voz fluida, humana, NO tipo robot, NO sintética cantada, NO lenta arrastrada
- **Velocidad**: regulable por el usuario (parámetro de configuración o ajuste en caliente por voz tipo "Claude, habla más rápido")
- **Velocidad por defecto**: ritmo natural de conversación humana (ni acelerada ni lenta)

### Candidatos TTS que cumplen estos requisitos
Ordenados por naturalidad descendente, con trade-off soberanía:

1. **ElevenLabs** (cloud, ~5$/mes plan starter) — top en naturalidad y prosodia, velocidad regulable nativa. Trade-off: rompe soberanía total, pero solo procesa el texto de salida (no audio ni contexto privado).
2. **Kokoro TTS** (local, 82M params) — neural, muy decente, baja latencia. Velocidad regulable. Más sobrio que ElevenLabs pero claramente neural-natural, no robótico.
3. **XTTS-v2 / Coqui TTS** (local) — calidad alta, multi-idioma (importante: español para Angel, francés para contenidos NosVers), voice cloning opcional.
4. **F5-TTS** (local, 2025) — estado del arte open-source, calidad casi ElevenLabs, velocidad regulable.
5. **Piper TTS** (local, ultra-ligero) — el más rápido y eficiente pero el menos natural de la lista. Descartar si la prioridad es naturalidad.

**Recomendación** para `/speckit-plan`: empezar con **Kokoro** (cumple soberanía + naturalidad razonable + velocidad regulable + cero coste). Si tras prueba de uso Angel no queda satisfecho con la naturalidad, escalar a **F5-TTS** local o, como último recurso si quiere máxima calidad, **ElevenLabs**.

### Idioma de la voz
- Default: **español** (es el idioma con el que Angel habla a Claude)
- Capacidad de cambiar a francés cuando esté trabajando contenido público NosVers

---

## 11. Decisiones tomadas por Angel (2026-05-12, vía móvil)

### Wake word
- **Palabra elegida**: `Claudio` (castellanización de "Claude" — encaja con español de Angel)
- **Nota técnica**: palabra trisílaba clara en español castellano. Riesgo bajo de falsos positivos porque "Claudio" no aparece en la conversación cotidiana de Angel (a diferencia de "Claude"). En `/speckit-clarify` validar:
  - Sensibilidad del modelo de wake word para "Claudio" pronunciado en castellano
  - Casi seguro toca entrenar custom con openWakeWord (Porcupine no trae "Claudio" stock) — pipeline en Colab Pro ~75-90min, genera ONNX ~200KB para detección on-device
  - Cooldown mínimo entre activaciones para evitar que la propia respuesta TTS del asistente auto-dispare el wake word

### Voz de respuesta (TTS)
- **Requisito**: voz natural, fluida, NO robot, NO lenta
- **Velocidad**: regulable por el usuario (parámetro accesible, idealmente en runtime sin reiniciar)
- **Candidatos a evaluar en `/speckit-plan`** (priorizando soberanía local sobre cloud):
  1. **Kokoro TTS** (82M params, local, calidad alta, ya validado por el setup RHEL10 con Claude Code) — recomendado
  2. **Piper TTS** (local, rápido, varias voces multiidioma, español incluido)
  3. **Coqui XTTS-v2** (local, clonable, calidad muy alta pero más pesado)
  4. **ElevenLabs** (cloud, calidad máxima) — fallback solo si las locales no llegan
- **Idioma**: español castellano por defecto (Angel habla en español con Claude). Voz masculina o neutra, NO infantil.
- **Streaming**: si el TTS soporta streaming chunk-by-chunk, usarlo — reduce la sensación de "latencia robótica" al empezar a hablar antes de tener la frase completa.

Estas dos decisiones quedan cerradas. Las otras 4 decisiones abiertas (sección 8) las resuelve `/speckit-clarify` con Angel.


---

## 12. Decisiones tomadas por Angel (2026-05-12, vía móvil, sesión 2)

Estas 4 cierran las preguntas de la sección 8. Cada una arrastra implicaciones técnicas que `/speckit-plan` debe recoger.

### 12.1 Clasificación de etiqueta → **Siempre Haiku en VPS**
- `dia_capturar` invoca Haiku (claude-haiku-4-5) con un prompt de clasificación que devuelve una de: `trabajo` | `nosvers` | `familia` | `mental` | `idea` | `otro`.
- Coste estimado: ~$0.0001 por nota → < $0.10/mes incluso con dictado intensivo.
- Latencia añadida: ~500ms. Aceptable para captura en background.
- Prompt template debe vivir en el vault (`knowledge_base/angel/prompts/clasificar_nota.md`) para que sea editable sin redeploy.
- Fallback: si Haiku falla o timeout > 3s, etiquetar como `otro` y dejar log para reclasificación posterior.

### 12.2 Audio dictado → **Híbrido: audio 7 días + transcript permanente**
- Estructura propuesta:
  - `knowledge_base/angel/dia/YYYY-MM-DD.md` → transcript permanente (texto)
  - `knowledge_base/angel/dia/audio/YYYY-MM-DD/HH-MM-SS.opus` → audio comprimido (Opus codec, ~30KB/min)
- Cron job nightly a las 03:00 borra audios con más de 7 días de antigüedad.
- Cada entrada en el `.md` referencia su audio: `[audio: 17-23-45.opus]` que se rompe automáticamente cuando el archivo se borra (acepto).
- Justificación 7 días: ventana suficiente para detectar errores de transcripción y reprocesar; después, el transcript es la verdad.

### 12.3 Sin cobertura → **PWA Android propia con buffer local + sync diferido**
- ⚠️ **Esto amplía significativamente el alcance del proyecto**. La app Claude oficial no soporta esto, hay que construir PWA dedicada.
- Stack candidato a evaluar en `/speckit-plan`:
  - Frontend: vanilla JS + Web Components, o Vite + Svelte para algo más mantenible
  - Grabación: MediaRecorder API → Opus
  - Buffer: IndexedDB con cola de notas pendientes (id, timestamp, audio_blob, transcript_local_opcional)
  - Sync: Service Worker con Background Sync API; fallback a sync al abrir la app
  - STT: dos opciones a comparar:
    - **A** Whisper.cpp WASM en cliente (descarga inicial ~30MB del modelo, todo offline) — alineado con soberanía
    - **B** Audio se sube al VPS y se transcribe server-side (más simple, requiere conexión para STT)
  - Hosting: `pwa.nosvers.com` o `voz.nosvers.com` subdominio en el mismo VPS, HTTPS por Let's Encrypt
  - Auth: token largo emitido por el MCP server, almacenado en localStorage
- La PWA llama directamente al MCP `nosvers-mcp-2026` exponiendo `dia_capturar` por HTTPS (tendrá que añadirse endpoint REST junto al MCP o un proxy).

### 12.4 Resúmenes diarios → **Agente nuevo `agt07_diario`**
- Ubicación: `/home/nosvers/agents/agt07_diario/` siguiendo la estructura de los agentes existentes.
- Cron: diario a las 23:30 hora Europe/Paris.
- Input: `knowledge_base/angel/dia/YYYY-MM-DD.md`
- Output: `knowledge_base/angel/dia/resumenes/YYYY-MM-DD.md` con:
  - Resumen en 5-8 líneas
  - Lista de ideas/pendientes detectados
  - Etiquetas dominantes del día (gráfico texto: `trabajo:5 ▓▓▓▓▓ nosvers:3 ▓▓▓ mental:1 ▓`)
- Resumen semanal los domingos a las 22:00 leyendo los 7 últimos `dia/YYYY-MM-DD.md`.
- Notificación opcional por Telegram con el resumen.
- Modelo: Haiku para el día, Opus para el semanal (más síntesis necesaria).

---

## 13. Próximos pasos para Claude Code al arrancar la sesión

1. `cat BRIEF.md` para asegurarse del contexto
2. `/speckit-constitution` con principios: soberanía tecnológica, MCP-first, vault como source of truth, no regresión sobre infra existente, privacidad por defecto
3. `/speckit-specify` desde este brief — debe producir spec completa para los 4 sub-componentes:
   - (a) Tools nuevos del MCP (`dia_capturar`, `dia_contexto`, `dia_buscar`)
   - (b) Servicio TTS+wake word para Linux casa (VoiceMode MCP o equivalente, wake word "Claudio" custom)
   - (c) PWA Android offline-first
   - (d) Agente `agt07_diario`
4. `/speckit-plan` — stack definitivo por componente
5. `/speckit-tasks` — desglose testable
6. `/speckit-implement` — empezar por (a) y (d) que son los más simples y validan el flujo completo en VPS antes de tocar cliente

Cuando termine (a) y (d) y estén testeados, AVISAR a Angel por Telegram para que Claude (Opus desde la app móvil) revise seguridad de la infraestructura existente ANTES de seguir con (b) y (c).

---

## 14. ADDENDUM MULTI-USUARIO (2026-05-13, vía móvil, sesión 3)

⚠️ **Estas decisiones modifican la arquitectura ya implementada en T001-T054. Refactor obligatorio antes de continuar con T055+.**

### 14.1 Identificación de quién habla → Speaker ID automático con pyannote

- **Modelo**: `pyannote.audio` para speaker verification (1-vs-N), o alternativa más ligera `Resemblyzer` si pyannote pesa demasiado en runtime
- **Enrollment**: 30 segundos de Angel + 30 segundos de África grabados como muestras de referencia. Embeddings precalculados.
  - Almacenamiento: `/home/nosvers/voz/data/speakers/{angel,africa}.npy`
  - Script CLI: `voz/scripts/enroll_speaker.py --usuario {angel|africa} --audio <ruta>`
- **Flujo runtime** (Linux casa):
  1. Wake word "Claudio" dispara grabación
  2. Audio capturado → extraer embedding
  3. Comparar contra embeddings de Angel y África (cosine similarity)
  4. Si max_similarity ≥ threshold (0.7-0.8, calibrar): identidad confirmada
  5. Si max_similarity < threshold: asistente pregunta "¿Quién habla?" (fallback)
- **En PWA Android**: dispositivo = identidad. JWT del token incluye `sub: angel` o `sub: africa`. NO speaker ID en móvil (overkill, cada usuario tiene su PWA).
- **Latencia añadida**: ~300-500ms sobre el wake word. Aceptable.

### 14.2 Estructura del vault → Pool común con metadata autor

⚠️ **CAMBIO DE PATHS**. El código actual usa `knowledge_base/angel/dia/`. Hay que migrar a:

```
knowledge_base/
├── dia/
│   ├── 2026-05-13.md           ← pool común, todas las notas del día
│   ├── audio/2026-05-13/       ← audios 7 días
│   └── resumenes/              ← resúmenes diarios y semanales
├── prompts/                     ← prompts MCP (clasificar, resumir)
└── compartido/                  ← documentos largos compartidos (proyectos, decisiones)
```

**Formato de cada entrada** en `dia/YYYY-MM-DD.md`:

```markdown
## 17:23:45 · [angel] · trabajo · confianza 0.92
Texto de la nota...
[audio: 17-23-45.opus]
---
## 18:05:12 · [africa] · nosvers · confianza 0.88
Texto de la nota...
[audio: 18-05-12.opus]
```

**Refactor obligatorio antes de T055**:
- `voz/capturar.py`: cambiar path base, añadir parámetro `autor: Literal["angel","africa"]` a `dia_capturar_impl`
- `voz/buscar.py`: añadir filtro opcional `autor`
- `voz/contexto.py`: añadir filtro opcional `autor` y por defecto incluir ambos
- `voz/vault_io.py`: parsear el formato nuevo de bloques con metadata
- `mcp_server.py`: actualizar signatures de los 3 tools
- `agt07_diario.py`: generar resumen del día con sección "Angel hizo / dijo" + "África hizo / dijo" + "conjunto"
- Tests: actualizar todos los `tests/voz/test_*.py` para el nuevo formato
- **Migración del archivo existente** (`knowledge_base/angel/dia/2026-05-13.md`): mover a `knowledge_base/dia/2026-05-13.md` y añadir `[angel]` a las entradas existentes

### 14.3 Privacidad → Todo compartido (cero privacidad)

- No hay scoping por permisos. Cualquier nota es visible para ambos.
- Decisión política, simplifica enormemente la implementación: no hay que validar permisos en `dia_buscar` ni en el dashboard.
- Solo se usa el campo `autor` como **filtro opcional** ("dame solo lo de África hoy"), nunca como ACL.

### 14.4 Dashboard → Proyecto Spec Kit separado `002-second-brain-dashboard`

Ver `/home/nosvers/specs/second-brain-dashboard/BRIEF.md` (siguiente).

Claude Code en este proyecto (001) **NO** trabaja el dashboard. Solo asegura que la estructura del vault y los tools MCP sean compatibles con la futura visualización web (formato consistente, metadata explícita, endpoints REST listos).

---

## 15. Plan tras este addendum

1. **Refactor T001-T054** según sección 14.2. No es opcional. Sin esto, el dashboard del 002 no podrá leer datos multi-usuario y el speaker ID del 002 quedaría desconectado.
2. **Migrar entrada existente** del 13 de mayo (la del test de la revisión de seguridad) al nuevo formato.
3. **Continuar con T055+** (sub-componentes b y c) ya con multi-usuario incorporado desde el inicio. La PWA Android tiene que diferenciar Angel/África por device. El asistente Linux casa hace speaker ID.
4. Al terminar, Telegram a Angel + revisión por Opus móvil + lanzar proyecto 002.


---

## 14. Addendum multi-usuario (2026-05-13, decisión Angel post-revisión seguridad)

El BRIEF original asumía mono-usuario (solo Angel). Esto se amplía: **Angel + África** son usuarios distinguibles del mismo asistente. Decisiones tomadas:

### 14.1 Identificación → Speaker ID automático con pyannote
- Sin login explícito por voz. El sistema identifica al hablante por su voz.
- Stack: `pyannote.audio` con modelo de embedding (`pyannote/embedding` o `speechbrain/spkrec-ecapa-voxceleb`).
- **Enrollment one-shot**: cada usuario graba ~30s al instalar. Se calcula embedding promedio y se guarda en `knowledge_base/system/speakers/{angel,africa}.npy`.
- En cada captura: extraer embedding del audio del usuario, comparar por cosine similarity con los enrolled.
- **Threshold de confianza** (a calibrar en `/speckit-clarify`): si max_sim > 0.75 → identidad asignada; si entre 0.55-0.75 → preguntar "¿Eres Angel o África?"; si < 0.55 → "no te reconozco" + log.
- Latencia añadida: 300-500ms sobre el wake word. Aceptable.
- Aplicable al asistente voz Linux casa. En la PWA Android, el dispositivo = identidad (cada PWA instalada está vinculada al usuario que se enrolló), no hace falta speaker ID por audio.

### 14.2 Vault → Pool común con metadata autor
**Cambio fundamental respecto al BRIEF original sección 6 y 12.1.**

- Estructura anterior: `knowledge_base/angel/dia/YYYY-MM-DD.md`
- Estructura nueva: `knowledge_base/dia/YYYY-MM-DD.md` (sin segmentación por usuario)
- Cada nota dentro del archivo lleva su `autor` en el frontmatter:
  ```markdown
  ## 14:32:17 [autor:angel] [etiqueta:trabajo]
  La obra de Bordeaux tiene un retraso de 3 días por...
  
  ## 17:45:02 [autor:africa] [etiqueta:nosvers]
  Las lombrices del lecho 3 han producido hoy...
  ```
- Tools del MCP afectados: `dia_capturar`, `dia_contexto`, `dia_buscar` añaden parámetro opcional `autor: str = None` (None = ambos). El autor por defecto se infiere del speaker ID; se puede sobreescribir si se llama desde el dashboard.
- Audio: `knowledge_base/dia/audio/YYYY-MM-DD/HH-MM-SS_{autor}.opus` (los 7 días de retención del BRIEF 12.2 se mantienen).

### 14.3 Privacidad → Todo compartido
- Cero permisos por nota.
- Cualquier query devuelve todas las notas relevantes sin filtrar por hablante.
- Filtros por `autor` son funcionales (ver qué hizo Angel hoy / qué dijo África), no de privacidad.
- Justificación Angel: "tanto monta, vais a una".

### 14.4 Refactor pendiente sobre código de la noche anterior

Claude Code escribió anoche con la arquitectura mono-usuario. Al retomar, ANTES de T055 (sub-componente b), DEBE refactorizar:

1. **`voz/vault_io.py`**: cambiar todas las rutas `knowledge_base/angel/dia/` → `knowledge_base/dia/`. Añadir helpers `serializar_nota(autor, etiqueta, texto, ts)` y `parsear_notas(md, filtro_autor=None)`.
2. **`voz/capturar.py`**: añadir parámetro `autor: str` requerido. Inyectar `[autor:X]` en el header de la nota.
3. **`voz/buscar.py`** y **`voz/contexto.py`**: añadir parámetro opcional `autor`. Filtrar tras parsear.
4. **`mcp_server.py`**: actualizar signatures de los 3 tools `dia_*` para exponer `autor`.
5. **`tests/voz/`**: actualizar fixtures y tests para cubrir notas de Angel y África en el mismo archivo + filtrado.
6. **`agt07_diario.py`**: el resumen diario debe agrupar por autor + global ("Angel: 5 notas trabajo, 2 nosvers; África: 3 huerto, 1 idea").
7. **Migración del único archivo de test existente** (`knowledge_base/angel/dia/2026-05-13.md` creado por Opus en la revisión) → mover a `knowledge_base/dia/2026-05-13.md` y reformatear.

### 14.5 Nuevo módulo: Speaker ID

Sub-componente NUEVO entre (a) y (b):
- **`voz/speaker_id.py`**: enrollment, comparación, cache de embeddings.
- **`voz/scripts/enroll_speaker.py`**: CLI para enrollment one-shot (`python -m voz.scripts.enroll_speaker angel /path/to/sample.wav`).
- **Tests** en `tests/voz/test_speaker_id.py`.
- Integración en el wake word loop del Linux casa: tras detectar "Claudio" y antes de procesar el comando, identificar hablante.

### 14.6 Dashboard — SE SACA DE ESTE PROYECTO

El dashboard ha sido decidido pero como **proyecto separado `002-second-brain-dashboard`** (ver `/home/nosvers/specs/second-brain-dashboard/BRIEF.md`). NO empezar hasta haber acabado 001 completo y validado por Angel.

---
*Addendum redactado por Claude Opus 4.7 móvil tras 4 decisiones de Angel, 2026-05-13 06:00 UTC*
