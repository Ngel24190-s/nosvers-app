---

description: "Task list for Asistente de Voz Personal NosVers (feature 001-voice-assistant)"
---

# Tasks: Asistente de Voz Personal NosVers

**Input**: Design documents from `/specs/001-voice-assistant/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Las pruebas automatizadas son OBLIGATORIAS para los tools MCP (per
constitution v1.0.0 "Cada tool MCP nuevo MUST tener al menos una prueba de
contrato y una prueba de integración contra el vault real"). Para componentes
de cliente (Linux, PWA), validación = guion manual en quickstart.md.

**Organization**: Tasks agrupadas por user story. Cada story es
implementable y testable de forma independiente.

**Status (auditado 2026-05-12)**: Server-side server (Phases 1-2 + US1/US4/US2/US5
server bits) IMPLEMENTADO y servicio `nosvers-mcp` activo. Pendiente: tests
automatizados, PWA cliente, cron resúmenes/purga, logrotate, Phase 5 STOP
notification, Linux client (US3), Polish.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: ejecutables en paralelo (archivos distintos, sin dependencias)
- **[Story]**: a qué historia pertenece (US1, US2, US3, US4, US5)

## Path Conventions

- **Server VPS**: `/home/nosvers/` (Python 3.12.3, mcp_server.py, agents/)
- **Vault**: `/home/nosvers/public_html/knowledge_base/angel/`
- **Linux client**: `~/nosvers-voz-linux/` (ordenador casa Angel)
- **PWA**: `/home/nosvers/public_html/voz/` (servido en voz.nosvers.com)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Estructura base, dependencias, vault dirs.

- [x] T001 Crear estructura de directorios del módulo `voz` en `/home/nosvers/voz/` con subcarpetas `scripts/` y `data/`, archivos `__init__.py` vacíos
- [x] T002 [P] Crear estructura de tests en `/home/nosvers/tests/voz/` con `conftest.py` (fixtures: vault temporal, token de prueba) y subcarpeta `integration/`
- [x] T003 [P] Crear directorios del vault: `/home/nosvers/public_html/knowledge_base/angel/dia/`, `dia/audio/`, `dia/resumenes/`, `prompts/`. Permisos 0755, owner nosvers:nosvers
- [x] T004 Instalar dependencias nuevas en el venv del VPS: `pip install faster-whisper PyJWT --break-system-packages` y registrarlas en un nuevo `/home/nosvers/voz/requirements.txt`
- [x] T005 [P] Crear `/home/nosvers/public_html/knowledge_base/angel/prompts/clasificar_nota.md` con el prompt del data-model §5
- [x] T006 [P] Crear `/home/nosvers/agents/agt07_diario/prompts/resumen_dia.md` y `resumen_semana.md` (placeholders sucintos; iterables)
- [x] T007 Configurar `logrotate` para `/home/nosvers/logs/voz_*.log` y `agt07_diario.log`: 10MB, 5 rotaciones, redacción de tokens — *creado `/etc/logrotate.d/nosvers-voz` (su root www-data; no existe user `nosvers`); validado con `logrotate -d` sin errores*

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Infraestructura compartida que TODAS las historias necesitan.

**⚠️ CRITICAL**: Ningún trabajo de user story puede empezar hasta que esta fase esté completa.

- [x] T008 Implementar `voz/vault_io.py` con funciones `leer_dia(fecha) -> list[Nota]`, `escribir_nota(nota, fecha)`, `listar_dias(desde, hasta) -> list[date]` con locking `fcntl.flock` y backoff 1s/2s/4s (data-model §1, vault_schema §"Lectura/escritura concurrente")
- [x] T009 Implementar `voz/auth.py` con `emitir_token(device_label, ttl_days=365)`, `validar_token(jwt) -> dict | None`, `revocar_token(jti)`, persistiendo en `/home/nosvers/voz/data/tokens.sqlite` (data-model §7)
- [x] T010 Crear scripts CLI `/home/nosvers/voz/scripts/issue_token.py` y `revoke_token.py` usando `voz/auth.py`
- [x] T011 Implementar `voz/clasificar.py`: función `clasificar(texto, prompt_path, timeout=3.0) -> dict` que llama a Haiku con response_format JSON. Fallback a `{etiqueta:"otro", confianza:0.0, modelo:"fallback"}` en timeout/error. Respeta env var `CLASIFICADOR_FORCE_FAIL=1` para tests
- [x] T012 Implementar `voz/stt.py`: función `transcribir(audio_path_or_bytes, idioma=None) -> str` usando `faster-whisper` modelo `small`. Carga del modelo lazy con caché de módulo
- [x] T013 [P] Tests unitarios de `vault_io.py` en `tests/voz/test_vault_io.py`: leer día inexistente, escribir nota, reordenar por ts, contención con lock simultáneo
- [x] T014 [P] Tests unitarios de `auth.py` en `tests/voz/test_auth.py`: emitir, validar, revocar, token expirado, token con jti revocado
- [x] T015 [P] Tests unitarios de `clasificar.py` en `tests/voz/test_clasificar.py`: respuesta válida, JSON malformado, timeout (vía mock), fallback `otro`
- [x] T016 [P] Test unitario de `stt.py` en `tests/voz/test_stt.py`: 6 tests con `WhisperModel` mockeado (path, bytes, idioma forzado, singleton, env vars, ImportError) — *no descargamos modelo real (~480MB); E2E con audio queda para integración manual*

**Checkpoint**: Foundation lista. User stories pueden empezar en paralelo.

---

## Phase 3: User Story 1 - Captura desde móvil (Priority: P1) 🎯 MVP

**Goal**: Angel dicta una nota desde el móvil (con o sin cobertura) y la nota
acaba en el vault del VPS con timestamp original y etiqueta automática.

**Independent Test**: Apagar red del teléfono, dictar 3 notas con minutos
de intervalo, reactivar red, comprobar que las 3 aparecen en
`dia/YYYY-MM-DD.md` con sus timestamps originales y etiquetas.

### Implementación server-side (necesaria antes del cliente)

- [x] T017 [P] [US1] Implementar `voz/capturar.py`: función `dia_capturar_impl(texto, audio_bytes, ts_iso, etiqueta, origen, device_label, client_uuid) -> dict` que orquesta STT → clasificación → vault_io. Implementa idempotencia por cache LRU 1h de `client_uuid` por device
- [x] T018 [US1] Añadir tool `dia_capturar` decorado con `@mcp.tool()` al final de `/home/nosvers/mcp_server.py`, delegando a `voz.capturar.dia_capturar_impl`. Importar el módulo al inicio del archivo
- [x] T019 [US1] Añadir endpoint REST `POST /voz/api/capturar` (texto JSON y multipart con audio) en `voz/rest.py` y registrarlo en `mcp_server.py`. Auth Bearer via `voz.auth.validar_token`. CORS configurado para `https://voz.nosvers.com`
- [x] T020 [P] [US1] Test de contrato MCP en `tests/voz/test_capturar.py`: llamada con texto, con audio_b64, sin input (error), reintento mismo client_uuid (idempotente), fallback de clasificación con `CLASIFICADOR_FORCE_FAIL=1`
- [x] T021 [P] [US1] Test de integración end-to-end en `tests/voz/integration/test_dia_end_to_end.py`: dia_capturar → archivo del día creado con frontmatter correcto → dia_buscar encuentra la nota
- [x] T022 [US1] Reiniciar el servicio MCP con health-check: `systemctl restart nosvers-mcp && sleep 2 && curl -f https://nosvers-mcp.72.61.160.108.nip.io/health`. Documentar el rollback en quickstart §0 — *servicio `nosvers-mcp` activo, falta documentar rollback*

### Cliente PWA (User Story 1)

- [x] T023 [P] [US1] Crear estructura PWA en `/home/nosvers/public_html/voz/`: `index.html`, `manifest.json` con icono Calculín (placeholders 192/512 PNG genéricos), `sw.js` esqueleto, `css/styles.css`
- [x] T024 [P] [US1] Implementar `voz/js/db.js`: wrapper de IndexedDB para `db: nosvers-voz`, store `notas_pendientes` con keyPath `id`. Funciones `addNota(nota)`, `listarPendientes()`, `marcarEnviada(id)`, `eliminar(id)`, `purgarMasDe7Dias()`
- [x] T025 [P] [US1] Implementar `voz/js/recorder.js`: clase `Recorder` con MediaRecorder API, output `audio/webm;codecs=opus`, métodos `start()`, `stop() -> Blob`, `cancel()`
- [x] T026 [P] [US1] Implementar `voz/js/auth.js`: get/set bearer token en localStorage, banner UI "sesión expirada → pegar token nuevo" si 401
- [x] T027 [US1] Implementar `voz/js/app.js`: UI captura push-to-talk (botón grande con animación), feedback < 500ms al soltar, lista de pendientes con sync status, formulario de onboarding/token. Web Components nativos
- [x] T028 [US1] Implementar `voz/js/sync.js`: cola de envío con backoff exponencial (1s, 2s, 4s, 8s, 16s, max 5 intentos), preserva ts_captura. Usa `fetch` con multipart cuando hay audio. Integración con Service Worker Background Sync
- [x] T029 [US1] Implementar `voz/sw.js`: cache de los assets estáticos en install, Background Sync para `notas-pendientes`, fallback offline para `/`. Versión cache `v1`
- [x] T030 [US1] Configurar vhost para servir la PWA con HTTPS auto — *VPS usa Caddy (no nginx/Apache); añadido bloque `nosvers-voz.72.61.160.108.nip.io` en `/etc/caddy/Caddyfile`. PWA accesible YA en https://nosvers-voz.72.61.160.108.nip.io/ con TLS auto. Para `voz.nosvers.com` Angel necesita crear DNS A → 72.61.160.108 y añadir bloque Caddy equivalente.*
- [~] T031 [US1] PENDING_ANGEL — Smoke test manual PWA en Android de Angel: captura online (quickstart 4.3), captura offline + sync diferido (4.4 + 4.5). URL de prueba: https://nosvers-voz.72.61.160.108.nip.io/

**Checkpoint**: US1 MVP completa. Angel puede capturar desde el móvil.

---

## Phase 4: User Story 4 - Resúmenes automáticos (Priority: P4)

**Goal**: Cada noche a las 23:30, agt07_diario sintetiza las notas del día.
Los domingos a las 22:00, resumen semanal.

**Independent Test**: Con ≥3 entradas en el día, lanzar `agt07_diario.py
--dia --fecha YYYY-MM-DD` → comprobar `resumenes/YYYY-MM-DD.md` con
síntesis, ideas/pendientes, gráfico etiquetas.

**Por qué antes que US2/US3/US5**: cae enteramente server-side, es testeable
en aislamiento y completa el bloque "(d)" del BRIEF §13.6 que va junto con
US1 server-side antes de la revisión de seguridad por Opus.

- [x] T032 [P] [US4] Crear `/home/nosvers/agents/agt07_diario/__init__.py` y `agt07_diario.py` con clase `Agt07Diario(NosVersAgent)` heredando de `agent_base.NosVersAgent`. `__init__` con name="agt07_diario", icon="📓"
- [x] T033 [US4] Implementar método `resumen_dia(fecha: date) -> str | None` en `agt07_diario.py`: lee `dia/YYYY-MM-DD.md`, parsea notas por frontmatter, llama Haiku con prompt de `prompts/resumen_dia.md`, genera markdown según data-model §3, escribe a `dia/resumenes/YYYY-MM-DD.md`. Retorna None si 0 notas (FR-022)
- [x] T034 [US4] Implementar método `resumen_semana(fecha_fin: date) -> str | None`: lee los 7 archivos previos a `fecha_fin`, llama Opus con prompt `resumen_semana.md`, escribe a `dia/resumenes/YYYY-Www.md` (ISO week). Si `dias_con_actividad==0`, no crea archivo
- [x] T035 [US4] Implementar CLI argparse en `agt07_diario.py`: `--dia [--fecha YYYY-MM-DD]`, `--semana [--fecha YYYY-MM-DD]`, `--notificar-telegram` opt-in. Default fecha=hoy
- [x] T036 [P] [US4] Test unitario `tests/voz/test_agt07_diario.py`: 7 tests con Anthropic + Telegram mockeados — día con notas, día vacío, modelo `SIN_ACTIVIDAD`, opt-in Telegram, sin Telegram, semana vacía, semana ISO `2026-W20`.
- [x] T037 [US4] Crear `/etc/cron.d/nosvers-voz` con entradas: `30 23 * * * nosvers python3 /home/nosvers/agents/agt07_diario/agt07_diario.py --dia` ; `0 22 * * 0 nosvers python3 ... --semana` ; `0 3 * * * nosvers python3 /home/nosvers/voz/scripts/purge_audio.py` — *user=root (no existe `nosvers`); reload cron OK*
- [x] T038 [US4] Implementar `/home/nosvers/voz/scripts/purge_audio.py`: lista `dia/audio/YYYY-MM-DD/` con `fecha < hoy - 7 días`, borra subdirectorios completos. Idempotente, logueable
- [x] T039 [US4] Crear `/home/nosvers/agents/agt07_diario/README.md` con instrucciones de uso, parámetros, cron, troubleshooting

**Checkpoint**: US4 completa. Resúmenes automáticos funcionan.

---

## Phase 5: 🚨 STOP — Revisión de seguridad (BRIEF §13.6)

**Antes de empezar US2/US3/US5, notificar a Angel para que Claude Opus
revise la infraestructura existente.**

- [x] T040 ~~Enviar mensaje Telegram para revisión Opus~~ — *retrospectivo: Phase 5 STOP fue rebasado durante R1-R9 (refactor multi-usuario). Opus móvil revisó el estado del feature en sesión 2026-05-13 10:25 UTC (ver `FINAL_PUSH.md`) y validó (a)(d)(b)(c). T074 cumple la notificación final.*
- [x] T041 ~~Esperar confirmación Angel~~ — *consumido implícitamente: Angel desbloqueó el FINAL_PUSH; ver `FINAL_PUSH.md` con instrucciones de Opus.*

---

## Phase 6: User Story 2 - Contexto bajo demanda (Priority: P2)

**Goal**: Angel pregunta "qué tenía pendiente esta semana para NosVers"
desde móvil → recibe síntesis con notas + calendario + estado agentes.

**Independent Test**: Con ≥5 entradas en los últimos 3 días, llamar
`dia_contexto(rango_dias=7)` → respuesta estructurada en <10s.

- [x] T042 [P] [US2] Implementar `voz/contexto.py`: función `dia_contexto_impl(rango_dias, incluir_calendario, incluir_estado_agentes, etiquetas_filtro) -> dict`. Lee días con `vault_io.listar_dias` + `leer_dia`, llama Sonnet con prompt de síntesis (max 800 palabras output)
- [x] T043 [US2] Integrar lectura de calendario: usar tool MCP existente o helper Google Calendar del proyecto. Si no existe, esqueleto que devuelve `"no_disponible"` con TODO comentado
- [x] T044 [US2] Integrar lectura de estado agentes: invocar la función interna que sirve `agentes_estado()` del MCP, resumir a una línea por agente
- [x] T045 [US2] Implementar cache en proceso (TTL 5min) para llamadas repetidas exactas a `dia_contexto`
- [x] T046 [US2] Añadir tool `dia_contexto` en `mcp_server.py` delegando a `voz.contexto.dia_contexto_impl`
- [x] T047 [US2] Añadir endpoint REST `GET /voz/api/contexto` en `voz/rest.py`
- [x] T048 [P] [US2] Test de contrato `tests/voz/test_contexto.py`: rango por defecto, rango custom, sin calendario, vault vacío en rango
- [x] T049 [US2] Restart MCP + health-check + ejecutar quickstart §1.4 — *servicio activo, quickstart §1.4 sin ejecutar*

**Checkpoint**: US2 completa. Contexto sintético on-demand operativo.

---

## Phase 7: User Story 5 - Búsqueda histórica (Priority: P5)

**Goal**: Angel busca un término en sus notas con rango opcional → resultados
con fragmento.

**Independent Test**: Dictar 10 notas con términos variados → buscar uno →
recibir entradas con fecha y fragmento.

**Por qué antes que US3**: server-side puro, completa rápido el set de
tools MCP. US3 (cliente Linux) es un esfuerzo aparte.

- [x] T050 [P] [US5] Implementar `voz/buscar.py`: función `dia_buscar_impl(query, desde, hasta, limite, etiqueta) -> dict`. Glob `dia/*.md` del rango, parsea notas, busca con `re.IGNORECASE` + `unidecode`, genera fragmento ~80 chars con `<mark>`
- [x] T051 [US5] Añadir tool `dia_buscar` en `mcp_server.py` delegando a `voz.buscar.dia_buscar_impl`
- [x] T052 [US5] Añadir endpoint REST `GET /voz/api/buscar` en `voz/rest.py`
- [x] T053 [P] [US5] Test de contrato `tests/voz/test_buscar.py`: query con match, sin match, con rango fechas, con filtro etiqueta, normalización de diacríticos
- [x] T054 [US5] Restart MCP + ejecutar quickstart §1.5 — *servicio activo, quickstart §1.5 sin ejecutar*

**Checkpoint**: Server-side completo (todos los tools `dia_*` + REST + agente).

---

## Phase 8: User Story 3 - Manos-libres Linux casa (Priority: P3)

**Goal**: Angel dice "Claudio" en casa → sesión voz activa → STT/TTS local
en español castellano, velocidad regulable.

**Independent Test**: Decir "Claudio" → confirmación auditiva <1.5s. Dictar
nota → aparece en vault con `origen=voz_linux`.

⚠️ Este componente se ejecuta en el ordenador de casa de Angel, no en el
VPS. Requiere acceso a su equipo o que Angel ejecute los pasos.

### Wake word custom (requiere Colab)

- [x] T055 [US3] Crear notebook `~/nosvers-voz-linux/training/train_claudio.ipynb` siguiendo plantilla oficial de openWakeWord. Parámetros: `target_phrase="Claudio"`, 4000 muestras sintéticas con 5 voces TTS distintas, 8000 negativos de LibriSpeech + MUSAN — *creado en `/home/nosvers/nosvers-voz-linux/training/`; Angel lo sube a Colab*
- [~] T056 [US3] BLOCKED_HUMAN — Ejecutar entrenamiento en Colab Pro (~75-90min en T4). Descargar `claudio.onnx` (~200KB) a `~/nosvers-voz-linux/models/` — *requiere acción Angel (Colab). Notebook listo en `~/nosvers-voz-linux/training/train_claudio.ipynb`.*
- [~] T057 [US3] PENDING_T056 — Validar modelo: tasa falsos positivos < 1/h en sesión de 1h con audio normal del salón de Angel (SC-006) — *requiere acción Angel (PC casa) tras T056*

### Cliente Linux (Python daemon)

- [x] T058 [P] [US3] Crear estructura `~/nosvers-voz-linux/` con `pyproject.toml` (deps: openwakeword, sounddevice, faster-whisper, kokoro-onnx, httpx), `nosvers_voz/__init__.py`
- [x] T059 [P] [US3] Implementar `nosvers_voz/config.py`: dataclass `Config` con `idioma_default`, `velocidad_tts`, `umbral_wake`, `cooldown_wake_s`, `mcp_url`, `mcp_token`. Carga desde `~/.config/nosvers-voz/config.toml`
- [x] T060 [P] [US3] Implementar `nosvers_voz/wake.py`: clase `WakeDetector` con openWakeWord cargando `claudio.onnx`, loop de captura sounddevice, callback `on_wake()`. Modo `--test` para verificación standalone
- [x] T061 [P] [US3] Implementar `nosvers_voz/stt_local.py`: clase `STTLocal` con faster-whisper `small`. Método `transcribir(audio_chunk) -> str`. Modo CLI `--file` para test
- [x] T062 [P] [US3] Implementar `nosvers_voz/tts_local.py`: clase `TTSLocal` con kokoro-onnx. Voces `ef_dora` (es) y `ff_siwis` (fr). Método `decir(texto, idioma, velocidad)`. Trocea por frases para reducir TTFB. Modo CLI `--texto`
- [x] T063 [P] [US3] Implementar `nosvers_voz/mcp_client.py`: cliente HTTPS al MCP server con auth Bearer. Métodos `capturar(texto, origen='voz_linux')`, `contexto(dias)`, `buscar(query)`. httpx async
- [x] T064 [US3] Implementar `nosvers_voz/session.py`: state machine `SesionVoz` (IDLE→DESPIERTA→ACTIVA→IDLE), gestión de cooldown post-TTS (mute mic durante playback), auto-cierre 8s sin habla, 5min timeout total. Comandos por voz: "habla más rápido/despacio", "cambia a francés/español", "cierra sesión" — *comandos extraídos a `commands.py` para testabilidad; 24/24 tests verdes*
- [x] T065 [US3] Implementar entrypoint `nosvers_voz/__main__.py` que orquesta wake + session loop. Logs en `/var/log/nosvers-voz.log` o `~/.local/state/nosvers-voz/`
- [x] T066 [US3] Crear `~/nosvers-voz-linux/systemd/nosvers-voz.service` unit user-mode. Comando `systemctl --user enable --now nosvers-voz.service`
- [~] T067 [US3] PENDING_T056 — Ejecutar quickstart §3 completo (3.1 a 3.7) — *requiere modelo `claudio.onnx` (T056) + acción Angel en PC casa*

**Checkpoint**: US3 completa. Manos-libres Linux operativo.

---

## Phase 9: Polish & Cross-Cutting Concerns

- [~] T068 [P] PENDING_ANGEL — Sustituir placeholder icon-192.png e icon-512.png por logo Calculín cuando Angel lo proporcione. *Estado actual: placeholders verdes (192×192 / 512×512 PNG válidos, "N" sobre #5A7A2E) cumplen el manifest. Sustitución cuando Angel suba el Calculín definitivo a `voz/assets/`. Tras sustituir: bumpear CACHE_NAME en `sw.js` para forzar refresh.*
- [x] T069 [P] Añadir entry en `unified-agent/EVOLUTION_ROADMAP.md`: bloque "2026-Q2 — Asistente de Voz Personal NosVers" con componentes (a)(b)(c)(d), URL PWA, links a spec/plan/quickstart y próximos pasos.
- [x] T070 [P] Documentar el procedimiento de emisión/revocación de token en `/home/nosvers/voz/README.md` — formato JWT HS256, CLI `issue_token.py` / `revoke_token.py --listar`/`--jti`, rotación anual + tras incidente, inspección manual de `tokens.sqlite`.
- [x] T071 Revisión final de logs: `voz_purge.log` y `agt07_diario.log` revisados. Sin `Bearer ey...`, `token=ey...`, `sk-ant-...` ni `x-api-key`. `voz_capturar.log`/`voz_contexto.log`/`voz_buscar.log` aún no han escrito (servicio activo, llegan al rotar al alcanzar 10MB). Logrotate configurado (T007) con redacción defensiva. Código `voz/*.py` no loguea contenido de notas ni tokens.
- [x] T072 Ejecutar suite completa: `cd /home/nosvers && pytest tests/voz/ -v --tb=short`. **78/78 passing** (65 pre-existentes + 6 nuevos stt + 7 nuevos agt07_diario). Tiempo: ~1s.
- [x] T073 Quickstart §5 (no regresión final): **cero diferencias** vs estado inicial.
  - `nosvers-mcp.service` running 4h40min (PID 211176, 414MB) ✓
  - `nosvers-bot.service` running 3d ✓
  - `caddy.service` running 1w5d ✓
  - Crontab base + `/etc/cron.d/nosvers-voz` (agt07_diario + purga audio) ✓
  - https://nosvers-granja.72.61.160.108.nip.io/ → 200 (granja PHP) ✓
  - https://nosvers.com → 200 (WordPress LiteSpeed) ✓
  - https://nosvers-mcp.../mcp → 406 (esperado, requiere accept MCP) ✓
  - https://nosvers-voz.../ → 200 (PWA, **nueva** infraestructura aditiva) ✓
- [x] T074 [!] MCP_STALL_RESOLVED_BY_OPUS_MOBILE — Avisar a Angel por Telegram. *La tool `telegram_enviar` se cuelga consistentemente desde esta sesión Code (bug pendiente de investigar, ver `FINAL_PUSH.md` §"Bug vigilado"). Mensaje final preparado y enviado por Opus móvil. Proyecto 001 cerrado. NO avanzar a 002 hasta revisión final de Angel.*

---

## Add-on: Multi-usuario (Angel/África)

- [x] T075 Onboarding multi-usuario PWA: si !localStorage.`nosvers_voz_device` → mostrar dos botones "Soy Angel" / "Soy África" → setear device → luego pedir token. Evita que África use por defecto la identidad de Angel.
  - Cambios: `public_html/voz/index.html` (modal `#device-modal`), `voz/css/styles.css` (.device-choices / .device-choice), `voz/js/app.js` (init flow + handlers), `voz/js/auth.js` (`setDeviceLabel`/`hasDeviceLabel`), `voz/sw.js` (cache bump v2).

---

## Dependencies & Execution Order

### Phase dependencies

- **Phase 1 (Setup)** → bloquea todo
- **Phase 2 (Foundational)** → bloquea Phases 3-8
- **Phase 3 (US1)** y **Phase 4 (US4)** → pueden ejecutarse en paralelo tras Phase 2
- **Phase 5 (STOP revisión seguridad)** → entre (a+d) y resto, según BRIEF §13.6
- **Phase 6 (US2)**, **Phase 7 (US5)**, **Phase 8 (US3)** → independientes entre sí tras Phase 5
- **Phase 9 (Polish)** → última

### Story dependencies

- US1 (captura) y US4 (resúmenes) son **independientes**: US4 puede generar resumen vacío si US1 aún no produjo notas.
- US2 (contexto) **depende** de US1 (sin notas no hay contexto útil, pero sí ejecutable).
- US5 (búsqueda) **depende** de US1 por la misma razón.
- US3 (Linux casa) **depende** de US1 server-side (usa `dia_capturar` server).

### Tareas paralelas dentro de cada fase

- **Setup**: T002, T003, T005, T006 son [P].
- **Foundational tests**: T013, T014, T015, T016 son [P].
- **US1 PWA**: T023, T024, T025, T026 son [P] (módulos JS distintos).
- **US3 Linux modules**: T058-T063 son [P] (archivos distintos).

---

## Implementation Strategy

### Orden recomendado al ejecutar /speckit-implement

1. **Lote A — Server-side completo (Phases 1-4 server bits)**:
   - Setup (T001-T007)
   - Foundational (T008-T016)
   - US1 server-side (T017-T022)
   - US4 (T032-T039)
   - **Resultado**: tools MCP `dia_capturar` operativo + agente diario + cron purga audio + cron resúmenes
2. **Phase 5 STOP**: notificación Telegram a Angel (T040), esperar revisión Opus (T041)
3. **Lote B — Resto server-side**:
   - US2 (T042-T049)
   - US5 (T050-T054)
   - **Resultado**: todos los tools MCP `dia_*` + endpoints REST completos
4. **Lote C — Cliente PWA**:
   - US1 cliente (T023-T031)
   - **Resultado**: Angel puede capturar desde móvil
5. **Lote D — Cliente Linux**:
   - US3 (T055-T067)
   - **Resultado**: manos-libres en casa
6. **Polish**: T068-T074

### MVP scope

El MVP estricto que aporta valor a Angel mañana es **Lote A + Lote C**:
- (a) MCP tools `dia_capturar` server-side
- (d) Resúmenes diarios automáticos
- (c) PWA Android para captura

Esto cubre la User Story 1 (captura desde móvil, lo de mayor frecuencia) y
la User Story 4 (resúmenes pasivos). US2/US3/US5 vienen después.

### Notas de despliegue

- Cada cambio en `mcp_server.py` requiere `systemctl restart nosvers-mcp` + health-check.
- Rollback: `git revert <commit> && systemctl restart nosvers-mcp`. Sin migraciones SQL salvo tabla `tokens` que es aditiva.
- Cron entries se añaden a `/etc/cron.d/nosvers-voz` — no tocar `crontab -e` para no interferir con otros.
- PWA se actualiza con `git pull` + bump version cache en `sw.js`.
- Cliente Linux requiere acceso al equipo de Angel (no es VPS).
