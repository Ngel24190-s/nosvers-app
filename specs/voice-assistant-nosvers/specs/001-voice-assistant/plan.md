# Implementation Plan: Asistente de Voz Personal NosVers

**Branch**: `001-voice-assistant` | **Date**: 2026-05-12 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-voice-assistant/spec.md`

## Summary

Cuatro sub-componentes federados por el servidor MCP `nosvers-mcp-2026`:

1. **(a) Tools MCP `dia_*`** — `dia_capturar`, `dia_contexto`, `dia_buscar`
   añadidos a `/home/nosvers/mcp_server.py`. Cierra el flujo de captura
   (texto u Opus → Whisper local → Haiku clasifica → vault), recuperación
   sintética y búsqueda full-text.
2. **(d) Agente `agt07_diario`** — bajo `/home/nosvers/agents/agt07_diario/`,
   hereda `NosVersAgent`. Genera resumen diario (Haiku, 23:30) y semanal
   (Opus, domingos 22:00).
3. **(b) Cliente Linux casa** — daemon con detector wake word "Claudio"
   (openWakeWord custom), Whisper local STT, Kokoro TTS, dialoga contra
   Claude vía MCP `dia_*` y otros tools existentes. Modelo wake word se
   entrena en Colab (~75-90min) y se despliega como `.onnx` ~200 KB.
4. **(c) PWA Android** — `voz.nosvers.com` servido desde el VPS. Vanilla JS
   + Web Components, IndexedDB queue, Service Worker Background Sync,
   MediaRecorder→Opus, auth con token Bearer revocable contra
   `dia_capturar` (endpoint HTTP REST adyacente al MCP).

Orden de ataque (forzado por BRIEF §13.6 y constitution IV "No regresión"):
**(a) y (d) primero** → testeo end-to-end en VPS → **revisión seguridad
Opus por Angel** → (b) → (c).

## Technical Context

**Language/Version**: Python 3.12.3 (server-side, agentes, MCP). Vanilla JS
ES2022 (PWA). Sin TypeScript en MVP — Web Components nativos + módulos JS.

**Primary Dependencies**:
- VPS / MCP: `fastmcp`, `requests`, `python-dotenv`, `anthropic` (ya
  instalados), `faster-whisper` (a añadir, para STT local server-side),
  `PyJWT` (para tokens revocables de la PWA).
- Agente `agt07_diario`: hereda de `agents/agent_base.py` (`NosVersAgent`).
- Linux client: `openWakeWord` (detector), `sounddevice` (captura),
  `faster-whisper` (STT local), `kokoro-onnx` (TTS), `requests`/`httpx`
  (MCP HTTP).
- PWA: vanilla JS + Web Components, IndexedDB API, Service Worker API,
  MediaRecorder API, Web Crypto API (para hashing local). Sin frameworks
  pesados en MVP.

**Storage**:
- Vault: `/home/nosvers/public_html/knowledge_base/angel/` (markdown).
- Audio efímero: `knowledge_base/angel/dia/audio/YYYY-MM-DD/HH-MM-SS.opus`
  (TTL 7 días, cron nightly purga).
- Cache de búsqueda (opcional, regenerable): SQLite FTS5 en
  `/home/nosvers/cache/dia_search.sqlite` si el volumen de notas lo exige
  (umbral: > 1.000 entradas). Para MVP, búsqueda lineal sobre markdown.
- PWA cliente: IndexedDB (`db: nosvers-voz`, `store: notas_pendientes`).

**Testing**:
- MCP tools: `pytest` con tests de contrato (entrada → JSON esperado) y
  de integración contra vault real bajo `tests/integration/`.
- Agente: `pytest` + fixtures de vault sintético.
- Linux client / PWA: tests manuales con guion de aceptación (ver
  `quickstart.md`).

**Target Platform**:
- Server-side (MCP + agente): VPS Hostinger Ubuntu, FastMCP HTTP en
  `https://nosvers-mcp.72.61.160.108.nip.io/mcp`.
- Linux client: ordenador casa Angel (RHEL10 según CLAUDE.md), Python 3.12+,
  pulseaudio/pipewire.
- Mobile: Android 10+ con Chrome/Chromium reciente (PWA standards 2025).

**Project Type**: Multi-componente, web-service (MCP+REST) + cron-agent +
desktop-app (Linux) + mobile-app (PWA).

**Performance Goals**:
- `dia_capturar` (texto): < 1s persist en vault + clasificación Haiku.
- `dia_capturar` (audio Opus 30s): < 5s end-to-end (incluye STT).
- `dia_contexto` (7 días, < 50 entradas): < 3s incluyendo síntesis.
- `dia_buscar` (12 meses, < 5k entradas, búsqueda lineal): < 3s.
- Wake word → confirmación auditiva: < 1.5s.
- Resumen diario (Haiku, 1 día): < 30s.

**Constraints**:
- Soberanía: STT y wake word locales obligatorios; sólo Haiku/Opus en cloud
  (justificado por constitution I).
- TTL audio 7 días estricto en VPS y espejo en PWA.
- No regresión sobre `nosvers-mcp-2026` existente, unified-agent, agentes
  cron, bot Telegram, WordPress.
- PWA debe funcionar offline con buffer ≥ 24h.

**Scale/Scope**:
- Usuario único (Angel). 5-50 notas/día estimadas.
- Volumen anual estimado: < 20k entradas, ~ 50 MB markdown, ~ 2 GB audio si
  no se purgara (con purga a 7 días: ~ 40 MB rotando).
- Linux client: 1 instancia. PWA: 1 instalación (móvil Angel).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Validado contra `.specify/memory/constitution.md` v1.0.0:

| Principio | Aplicación | Estado |
|---|---|---|
| **I. Soberanía Tecnológica** | Whisper local (STT), openWakeWord (wake), Kokoro (TTS local). Anthropic API solo para clasificación Haiku + síntesis. Sin ElevenLabs en MVP. | ✅ PASS |
| **II. MCP-First** | Toda funcionalidad nueva (`dia_capturar/contexto/buscar`) amplía `nosvers-mcp-2026`. El endpoint REST `/voz/api/capturar` para la PWA vive en el mismo binario que el MCP server (FastMCP+FastAPI), comparte auth y logging — no es API paralela. | ✅ PASS |
| **III. El Vault es la Verdad** | Notas, audio, resúmenes, prompts → todo en `knowledge_base/angel/`. Cache SQLite FTS5 sólo si > 1k notas y siempre regenerable desde markdown. | ✅ PASS |
| **IV. No Regresión** | Aditivo puro: 3 tools nuevos en MCP, 1 agente nuevo en `agents/agt07_diario/`. Sin cambios en agt0X existentes, unified-agent, bot Telegram, WordPress, Stripe. Reversible con `git revert + systemctl restart mcp-server`. | ✅ PASS |
| **V. Privacidad por Defecto** | Audio TTL 7 días (cron `/etc/cron.d/nosvers-voz`). Tokens revocables (Bearer JWT con jti). Logs redactan tokens. Audio crudo no sale del VPS de Angel salvo el viaje cliente→VPS sobre HTTPS. | ✅ PASS |

**Resultado**: Sin violaciones. No requiere entradas en "Complexity Tracking".

## Project Structure

### Documentation (this feature)

```text
specs/001-voice-assistant/
├── plan.md              # This file
├── research.md          # Phase 0 output — decisiones tecnológicas
├── data-model.md        # Phase 1 output — entidades y formatos vault
├── quickstart.md        # Phase 1 output — guía de prueba manual end-to-end
├── contracts/
│   ├── mcp_tools.md     # Contrato JSON-RPC de los 3 tools `dia_*`
│   ├── rest_endpoints.md # Contrato HTTP de `/voz/api/capturar` (PWA)
│   └── vault_schema.md  # Esquema de los markdown del día y resúmenes
├── checklists/
│   └── requirements.md  # Ya creado en /speckit-specify
└── tasks.md             # Generado por /speckit-tasks
```

### Source Code (repository root)

```text
# Componente (a) — Tools MCP (modifica archivo existente)
/home/nosvers/mcp_server.py                  # +3 tools dia_* al final + endpoint REST
/home/nosvers/voz/                           # módulo nuevo, importado por mcp_server
├── __init__.py
├── capturar.py                              # lógica dia_capturar
├── contexto.py                              # lógica dia_contexto
├── buscar.py                                # lógica dia_buscar
├── clasificar.py                            # llamada Haiku con prompt del vault
├── stt.py                                   # transcripción Whisper local server-side
├── vault_io.py                              # lectura/escritura archivos del día
├── auth.py                                  # JWT bearer con jti revocable
├── rest.py                                  # endpoint REST /voz/api/capturar para la PWA
└── scripts/
    └── purge_audio.py                       # cron nightly TTL 7 días

/home/nosvers/tests/voz/
├── conftest.py
├── test_capturar.py
├── test_contexto.py
├── test_buscar.py
├── test_clasificar.py
├── test_auth.py
└── integration/
    └── test_dia_end_to_end.py

/home/nosvers/public_html/knowledge_base/angel/
├── dia/                                     # NUEVO directorio
│   ├── YYYY-MM-DD.md                        # transcript del día
│   ├── audio/YYYY-MM-DD/HH-MM-SS.opus       # audio efímero
│   └── resumenes/YYYY-MM-DD.md              # resúmenes diarios/semanales
└── prompts/
    └── clasificar_nota.md                   # prompt Haiku editable

# Componente (d) — Agente agt07_diario
/home/nosvers/agents/agt07_diario/
├── __init__.py
├── agt07_diario.py                          # clase Agt07Diario(NosVersAgent)
├── prompts/
│   ├── resumen_dia.md
│   └── resumen_semana.md
└── README.md

# Cron entries añadidas en /etc/cron.d/nosvers-voz (sin tocar crons existentes)
# 30 23 * * *  nosvers  python3 /home/nosvers/agents/agt07_diario/agt07_diario.py --dia
# 0  22 * * 0  nosvers  python3 /home/nosvers/agents/agt07_diario/agt07_diario.py --semana
# 0   3 * * *  nosvers  python3 /home/nosvers/voz/scripts/purge_audio.py

# Componente (b) — Cliente Linux casa
# (vive en el ordenador de Angel, no en el VPS — directorio orientativo)
~/nosvers-voz-linux/
├── pyproject.toml
├── nosvers_voz/
│   ├── __init__.py
│   ├── wake.py                              # openWakeWord loop con modelo Claudio.onnx
│   ├── stt_local.py                         # faster-whisper modelo "small"
│   ├── tts_local.py                         # Kokoro client
│   ├── mcp_client.py                        # llamadas HTTPS al MCP del VPS
│   ├── session.py                           # state machine sesión voz
│   └── config.py                            # idioma, velocidad TTS, umbrales
├── models/
│   └── claudio.onnx                         # entrenado en Colab, ~200KB
└── systemd/
    └── nosvers-voz.service

# Componente (c) — PWA Android (servida desde VPS)
/home/nosvers/public_html/voz/               # raíz pública de voz.nosvers.com
├── index.html
├── manifest.json                            # icono Calculín 192/512
├── sw.js                                    # service worker
├── assets/
│   ├── icon-192.png                         # placeholder hasta que Angel suba
│   └── icon-512.png
├── js/
│   ├── app.js                               # UI captura push-to-talk
│   ├── db.js                                # IndexedDB queue
│   ├── sync.js                              # Background Sync API
│   ├── recorder.js                          # MediaRecorder → Opus
│   └── auth.js                              # bearer token storage
└── css/
    └── styles.css
```

**Structure Decision**: Multi-componente, no monorepo único. El código
server-side (a+d) vive en el repo `/home/nosvers/` ya existente. El
cliente Linux (b) es un proyecto Python independiente que se distribuye
al ordenador de casa de Angel. La PWA (c) es estática servida desde el
VPS bajo el directorio público.

## Phase 0 — Resumen de research

Ver `research.md` para detalle. Decisiones consolidadas:

| Decisión | Elección | Alternativas descartadas | Razón breve |
|---|---|---|---|
| Server-side STT | `faster-whisper` modelo `small` multilenguaje | whisper.cpp, Vosk | Mejor balance latencia/calidad CPU. Servidor tiene RAM. |
| Cliente Linux STT | `faster-whisper` modelo `small` o `medium` | whisper.cpp | Ya validado en RHEL10. |
| Wake word | openWakeWord custom "Claudio" | Porcupine ($, modelo Claudio inexistente), Snowboy (deprecado) | Open-source, modelo entrenable en Colab, runtime ONNX <200KB. |
| TTS | Kokoro (82M params, local, ONNX) | F5-TTS (más pesado), ElevenLabs (cloud, paga, viola soberanía) | Cumple naturalidad razonable, velocidad regulable, cero coste. |
| Clasificador etiqueta | claude-haiku-4-5 vía Anthropic API | Modelo local | Latencia ~500ms aceptable, coste despreciable (~$0.10/mes). |
| Resumen semanal | claude-opus-4-7 vía API | Sonnet | Síntesis mayor, frecuencia baja (1/semana) → coste OK. |
| PWA framework | Vanilla JS + Web Components | Svelte, React | Cero build pesado, mantenible en solitario, < 50KB JS. |
| PWA STT | Server-side (decisión clarify) | Whisper WASM cliente | Simplifica bundle, mantiene soberanía (VPS de Angel). |
| Auth PWA | JWT Bearer con jti revocable | Sesión cookie, OAuth | Apropiado para SPA + cero infraestructura extra. |
| Cache búsqueda | Markdown directo en MVP, SQLite FTS5 si >1k notas | Whoosh, Elasticsearch | YAGNI. Regenerable desde vault. |
| Cron purga audio | Cron del sistema (`/etc/cron.d/nosvers-voz`) | Agente dedicado | Tarea trivial, 5 líneas Python. |
| Hosting PWA | `voz.nosvers.com` subdominio Hostinger + Let's Encrypt | Pages externas | Mismo VPS, mismo dominio, soberanía. |

## Phase 1 — Design artifacts

Ver:
- `data-model.md` — entidades, esquema del archivo del día, formato YAML
  frontmatter por nota, esquema del resumen, esquema cola IndexedDB PWA.
- `contracts/mcp_tools.md` — JSON-RPC de los 3 tools.
- `contracts/rest_endpoints.md` — HTTP REST para la PWA.
- `contracts/vault_schema.md` — esquema markdown de día y resumen.
- `quickstart.md` — guion de aceptación manual end-to-end.

## Post-design Constitution re-check

Tras Phase 1 (data model + contracts + quickstart):

| Principio | Revisión post-design | Estado |
|---|---|---|
| I. Soberanía | Confirmado: ningún contrato exige servicio cloud no autorizado. | ✅ |
| II. MCP-First | El endpoint REST `/voz/api/capturar` vive en el mismo binario del MCP server y comparte auth/log. No es API paralela. | ✅ |
| III. Vault verdad | Esquema de archivo del día = markdown puro con frontmatter YAML por nota. Sin SQL como fuente. | ✅ |
| IV. No regresión | El binario MCP se reinicia tras añadir tools — riesgo controlado con health-check + rollback git. Documentado en quickstart. | ✅ |
| V. Privacidad | Token revocable con jti; cron purga audio 03:00; logs redactan Authorization. | ✅ |

## Complexity Tracking

> Sin violaciones declaradas. Tabla vacía.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| — | — | — |
