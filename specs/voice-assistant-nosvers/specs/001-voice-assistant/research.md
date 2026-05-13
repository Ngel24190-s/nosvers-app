# Research — Asistente de Voz Personal NosVers

**Feature**: 001-voice-assistant
**Date**: 2026-05-12

Decisiones técnicas con racional y alternativas evaluadas. Cualquier
NEEDS CLARIFICATION del Technical Context queda aquí resuelto.

---

## 1. STT server-side (para PWA y para reclasificación)

**Decisión**: `faster-whisper` modelo `small` multilenguaje (es+fr).

**Rationale**:
- Implementación de Whisper basada en CTranslate2: 3-4× más rápido que
  `whisper.cpp` en CPU x86_64 y ~5× menos RAM.
- `small` (244M params, ~466MB peso) tiene WER aceptable para dictado
  conversacional limpio en castellano (~10-12%).
- Carga única en memoria del proceso MCP (FastMCP es un binario long-running
  → modelo se mantiene caliente).
- Soporta `language=None` para autodetección — cubre el caso es/fr de Angel.

**Alternatives considered**:
- `openai-whisper` original: 3-4× más lento en CPU. Descartado.
- `whisper.cpp`: muy ligero pero la versión Python tiene overhead. Mejor en
  el cliente Linux que en el servidor (donde no hay restricción RAM).
- Vosk: más rápido pero peor calidad y peor soporte español castellano.
  Descartado.

**Cita config**:
```python
from faster_whisper import WhisperModel
model = WhisperModel("small", device="cpu", compute_type="int8")
segments, info = model.transcribe(audio_path, language=None, beam_size=5)
```

---

## 2. STT cliente Linux casa

**Decisión**: `faster-whisper` modelo `small` (o `medium` si el equipo de
Angel lo soporta).

**Rationale**:
- Mismo motor que el servidor (consistencia) pero con modelo más pequeño si
  fuera necesario por hardware.
- Funciona offline 100% — no depende del VPS para STT en la sesión de voz
  casera.

**Alternatives**: igual que punto 1.

---

## 3. Wake word custom "Claudio"

**Decisión**: `openWakeWord` con modelo entrenado a medida en Google Colab
Pro y exportado a ONNX.

**Rationale**:
- Open-source MIT, runtime puro ONNX (~200KB por modelo).
- Pipeline de entrenamiento documentado en `dscripka/openWakeWord`:
  ~75-90min en Colab T4 con dataset sintético de TTS para la palabra.
- Soporta umbral de confianza ajustable en runtime.
- Cooldown nativo configurable (`activation_threshold`, `min_activations`).

**Alternatives considered**:
- Picovoice Porcupine: comercial (free tier limitado). El SDK Personal
  permite generar wake words custom pero requiere cuenta y consola web.
  Descartado por dependencia cloud y proceso menos reproducible.
- Snowboy: deprecado por su autor (KITT.AI cerrado 2020). Sin
  mantenimiento de seguridad.
- Modelo from-scratch con PyTorch: 100× más esfuerzo, sin ganancia clara.

**Mitigación falsos positivos**:
- Umbral inicial `0.6`, ajustable por config.
- Cooldown 3s post-activación.
- Supresión total del detector durante playback del TTS (mute mic).
- Si tras 60s sin habla tras wake, sesión se cierra automáticamente.

**Plan de entrenamiento**: notebook Colab guardado en
`~/nosvers-voz-linux/training/train_claudio.ipynb` — script generado por la
plantilla oficial de openWakeWord, parámetro `target_phrase="Claudio"`,
4000 muestras sintéticas con 5 voces TTS distintas + 8000 negativos del
dataset `LibriSpeech` y ruido ambiente `MUSAN`.

---

## 4. TTS — voz de respuesta

**Decisión**: Kokoro TTS (82M params) como motor base, vía
`kokoro-onnx` con voces `ef_dora` (es-ES) y `ff_siwis` (fr-FR).

**Rationale**:
- 82M params: pequeño, ~330MB. Inferencia CPU < 200ms para frases cortas.
- Calidad subjetivamente "neural-natural", no robótica. Mejor que Piper.
- Soporta velocidad regulable en runtime (`speed` parámetro 0.5–2.0).
- ONNX exportable: sin dependencia de PyTorch en runtime.
- Multilenguaje con voces en castellano y francés.
- Cero coste, cumple soberanía.

**Alternatives considered**:
- F5-TTS: calidad superior pero modelo más pesado (1.5GB), latencia 1-2s.
  Reservado como upgrade futuro si Angel pide más naturalidad.
- ElevenLabs: máxima calidad pero rompe soberanía (BRIEF §11). Reservado
  como último recurso opt-in.
- Piper TTS: el más ligero pero el menos natural — descartado por BRIEF.
- Coqui XTTS-v2: muy pesado (>1GB), licencia restrictiva post-cierre Coqui.
  Descartado.

**Streaming**: Kokoro genera frase completa antes de devolver — no soporta
streaming nativo true chunk-by-chunk. Mitigación: trocear la respuesta del
LLM en frases (sentencer) y generar TTS frase a frase → reduce TTFB ≈ 60%.

---

## 5. Clasificador de etiqueta (Haiku en VPS)

**Decisión**: `claude-haiku-4-5-20251001` vía Anthropic API directa desde
`agt07_diario` y desde `voz/clasificar.py`.

**Rationale**:
- BRIEF §12.1 lo cierra explícitamente.
- Latencia típica ~500ms; coste ~$0.0001/nota → $0.10/mes para 1000 notas.
- Prompt vive en vault (`knowledge_base/angel/prompts/clasificar_nota.md`)
  → editable sin redeploy.
- Fallback: timeout 3s → etiqueta `otro` + entrada en log para reclasificación
  por `agt07_diario` posterior.

**Schema de respuesta**: forzado JSON con tool use o `response_format` para
garantizar parsing fiable. Output esperado:
```json
{"etiqueta": "nosvers", "confianza": 0.92, "razon": "menciona África y fotos"}
```

---

## 6. Resumen semanal (Opus)

**Decisión**: `claude-opus-4-7` para resumen semanal, `claude-haiku-4-5`
para resumen diario.

**Rationale**:
- Diario: síntesis ligera de 5-8 líneas → Haiku basta y es rapidísimo.
- Semanal: síntesis cruzada de 7 días + detección de tendencias → Opus
  porque aporta razonamiento. Frecuencia 1/semana → coste $0.20-0.50/sem.

---

## 7. PWA — framework y stack

**Decisión**: Vanilla JS ES2022 + Web Components nativos. Sin bundler.

**Rationale**:
- App es de ~5 pantallas (captura, lista pendientes, settings, log, login).
  No justifica React/Vue/Svelte.
- Sin bundler = sin pipeline npm; menos ataque, menos mantenimiento.
- Web Components soportados en Chrome Android desde hace años; cubre el
  100% de los dispositivos de Angel.
- Tamaño total < 50KB JS + CSS minificado a mano.

**Alternatives considered**:
- Svelte + Vite: añadir un build pipeline para 5 pantallas es overkill.
- React: bundle muy pesado para los requisitos. Innecesario para single
  user.

---

## 8. PWA — STT server-side vs cliente

**Decisión**: Server-side (Opción B del BRIEF §12.3). Cliente sube Opus al
endpoint REST del MCP y el VPS transcribe con `faster-whisper`.

**Rationale (ya documentada en Clarifications del spec)**:
- Simplifica bundle PWA (sin Whisper WASM ~30MB).
- Audio se cifra en tránsito vía HTTPS y se elimina del cliente tras sync.
- Mantiene soberanía: audio se procesa exclusivamente en el VPS de Angel.
- Permite reclasificación posterior si el modelo de clasificación mejora.

**Trade-off aceptado**: la PWA requiere conexión activa para transcribir
en el momento. En offline, mantiene el blob Opus en IndexedDB y lo procesa
al recuperar conexión — el timestamp de captura se preserva.

---

## 9. PWA — Autenticación

**Decisión**: JWT Bearer con claim `jti` (UUID) almacenado en una tabla
SQLite del VPS para permitir revocación individual.

**Rationale**:
- Single user pero múltiples tokens posibles (móvil, segundo móvil de
  emergencia, futuro tablet).
- Cada token tiene `jti` único → revocar un dispositivo no invalida los
  otros (FR-031).
- Token largo (1 año) almacenado en `localStorage` de la PWA.
- Validación en cada request: firma + jti no en blacklist.

**Alternatives considered**:
- Sesión cookie: requiere CORS configurado entre PWA y MCP; más fricción.
- OAuth: overkill para single user, requiere infraestructura externa.
- API key estática: no permite revocación granular.

**Generación de token inicial**:
- Comando manual `voz/scripts/issue_token.py --device "movil-angel"` en
  el VPS produce el JWT. Angel lo pega en la PWA en el primer onboarding.

---

## 10. Cache de búsqueda

**Decisión**: MVP usa búsqueda lineal sobre los archivos `dia/*.md` con
`re.finditer` y filtrado por fecha del nombre de archivo. Sin SQLite.

**Rationale**:
- Volumen esperado MVP: 5-50 notas/día × 30 días = 150-1500 notas. Lineal
  sobre markdown < 100ms.
- Si llegamos a > 1000 notas o búsquedas > 3s, migrar a SQLite FTS5
  regenerable desde el vault (idempotente).

**Schema FTS5 propuesto (cuando se necesite)**:
```sql
CREATE VIRTUAL TABLE notas_fts USING fts5(
    fecha, hora, texto, etiqueta, origen,
    tokenize = 'unicode61 remove_diacritics 2'
);
```

---

## 11. Cron purga audio

**Decisión**: Script Python invocado por cron del sistema a las 03:00.

```bash
# /etc/cron.d/nosvers-voz
0 3 * * * nosvers /usr/bin/python3 /home/nosvers/voz/scripts/purge_audio.py
```

**Rationale**: Tarea trivial (5 líneas Python que listan
`dia/audio/YYYY-MM-DD/` y borran subcarpetas cuya fecha es > 7 días).
No merece ser un agente.

---

## 12. Hosting de la PWA

**Decisión**: Subdominio `voz.nosvers.com` apuntando al mismo VPS,
servido por nginx/Apache existente, certificado Let's Encrypt mediante
certbot.

**Rationale**:
- Mismo VPS, soberanía total.
- Subdominio en lugar de `nosvers.com/voz/` para evitar conflictos con
  WordPress y poder aplicar CSP/CORS específicos.
- Let's Encrypt ya está en uso para el dominio principal.

**Trabajo previo necesario** (no en este plan, infraestructura):
- DNS A record `voz.nosvers.com` → IP del VPS.
- vhost en nginx/Apache para servir `/home/nosvers/public_html/voz/`.
- Certbot --expand para el subdominio.

---

## 13. Idempotencia y rollback

**Decisión**:
- El binario MCP recargado tras añadir tools: el systemd unit
  `nosvers-mcp.service` (asumido existente; si no, se crea como parte de
  task de despliegue) se reinicia con `systemctl restart nosvers-mcp`.
- Rollback: `git revert <commit>` + `systemctl restart nosvers-mcp` deja
  el sistema como antes. Sin migraciones SQL → reversible.
- Para audio: si purge falla, próximo ciclo lo arregla. Idempotente.

---

## NEEDS CLARIFICATION — resueltos en este research

- ¿STT server o cliente? → server-side (§8).
- ¿Modelo de wake word concreto? → openWakeWord custom (§3).
- ¿TTS engine concreto? → Kokoro (§4).
- ¿Auth de la PWA? → JWT Bearer con jti revocable (§9).
- ¿Hosting PWA? → subdominio `voz.nosvers.com` mismo VPS (§12).

Sin NEEDS CLARIFICATION restantes.
