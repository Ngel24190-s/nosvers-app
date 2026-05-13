# Quickstart — Asistente de Voz Personal NosVers

**Feature**: 001-voice-assistant
**Date**: 2026-05-12

Guion de aceptación manual end-to-end. Permite a Angel (o a Claude Opus
en la revisión de seguridad) validar que cada sub-componente cumple su
historia de usuario sin tocar código.

---

## Requisitos previos

- VPS con `mcp_server.py` desplegado y `systemctl status nosvers-mcp` =
  active (running).
- `.env` del VPS contiene `ANTHROPIC_API_KEY`, `APP_TOKEN`, `TELEGRAM_TOKEN`,
  `ANGEL_CHAT_ID`.
- Token Bearer válido emitido para `device_label=test-quickstart` (script
  `voz/scripts/issue_token.py`).

---

## 0. Pre-flight — verificar no regresión

Verifica que los servicios existentes siguen vivos antes de tocar nada.

```bash
# MCP server existente
curl -s https://nosvers-mcp.72.61.160.108.nip.io/health
# → {"ok":true,"tools":18+}

# Agentes cron OK
ls /home/nosvers/logs/agt0*.log | head -5
# → 5 ficheros recientes

# Bot Telegram
systemctl status nosvers-bot
# → active (running)

# WordPress
curl -sI https://nosvers.com | head -1
# → HTTP/1.1 200 OK
```

Cualquier falla aquí → **abortar deploy y revertir** antes de continuar.

---

## 1. Componente (a) — Tools MCP `dia_*`

### 1.1 `dia_capturar` con texto puro

```bash
curl -X POST https://nosvers-mcp.72.61.160.108.nip.io/voz/api/capturar \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "texto": "Pedir a África las fotos del extracto vivo antes del viernes",
    "ts_iso": "2026-05-12T09:23:45+02:00",
    "etiqueta": "auto",
    "origen": "texto_directo",
    "device_label": "test-quickstart",
    "client_uuid": "11111111-1111-1111-1111-111111111111"
  }'
```

**Espera**:
- HTTP 200.
- JSON con `ok=true`, `etiqueta_aplicada` razonable (esperado `nosvers`).
- Archivo `knowledge_base/angel/dia/2026-05-12.md` creado/actualizado con
  la nota y frontmatter correcto.

### 1.2 `dia_capturar` reintento idempotente

Repetir el mismo `curl` con el mismo `client_uuid`. Espera misma respuesta
sin duplicar nota en el archivo.

### 1.3 `dia_capturar` con audio Opus

```bash
# Genera un sample Opus de prueba (gstreamer u opusenc)
opusenc test_clip.wav test_clip.opus

curl -X POST https://nosvers-mcp.72.61.160.108.nip.io/voz/api/capturar \
  -H "Authorization: Bearer $TOKEN" \
  -F 'meta={"ts_iso":"2026-05-12T09:24:00+02:00","origen":"voz_movil","device_label":"test-quickstart","client_uuid":"22222222-..."};type=application/json' \
  -F "audio=@test_clip.opus;type=audio/opus"
```

**Espera**:
- HTTP 200, transcripción del clip presente en el archivo del día.
- Archivo `dia/audio/2026-05-12/09-24-00.opus` existe.

### 1.4 `dia_contexto`

```bash
curl "https://nosvers-mcp.72.61.160.108.nip.io/voz/api/contexto?dias=7" \
  -H "Authorization: Bearer $TOKEN"
```

**Espera**: HTTP 200, `notas_count > 0`, `sintesis` no vacía.

### 1.5 `dia_buscar`

```bash
curl "https://nosvers-mcp.72.61.160.108.nip.io/voz/api/buscar?q=África" \
  -H "Authorization: Bearer $TOKEN"
```

**Espera**: HTTP 200, al menos 1 resultado con fragmento `<mark>África</mark>`.

### 1.6 Fallback de clasificación

Simular timeout Haiku (env var `CLASIFICADOR_FORCE_FAIL=1` en el proceso
MCP, reinicio del servicio para esa prueba):

```bash
CLASIFICADOR_FORCE_FAIL=1 systemctl restart nosvers-mcp
# Repetir 1.1
```

**Espera**: HTTP 200, `etiqueta_aplicada="otro"`, `confianza=0.0`,
`modelo="fallback"`. Y entrada en `/home/nosvers/logs/voz_capturar.log`
señalando el fallback.

Después: `unset CLASIFICADOR_FORCE_FAIL && systemctl restart nosvers-mcp`.

### 1.7 Auth — token revocado

```bash
python3 /home/nosvers/voz/scripts/revoke_token.py --jti <jti-del-test>
curl -X POST .../voz/api/capturar -H "Authorization: Bearer $TOKEN" ...
```

**Espera**: HTTP 401, `{"ok":false,"error":"auth_invalido"}`.

### 1.8 Smoke test de tests automáticos

```bash
cd /home/nosvers && pytest tests/voz/ -v
```

**Espera**: todos los tests verdes.

---

## 2. Componente (d) — Agente `agt07_diario`

### 2.1 Ejecución manual del resumen diario

```bash
python3 /home/nosvers/agents/agt07_diario/agt07_diario.py --dia --fecha 2026-05-12
```

**Espera**:
- Archivo `knowledge_base/angel/dia/resumenes/2026-05-12.md` creado.
- Contenido conforme a data-model §3: síntesis, ideas/pendientes, gráfico
  de etiquetas.
- Log en `/home/nosvers/logs/agt07_diario.log`.

### 2.2 Día sin actividad

```bash
python3 /home/nosvers/agents/agt07_diario/agt07_diario.py --dia --fecha 2099-01-01
```

**Espera**: NO crea archivo, log dice "sin actividad", exit code 0.

### 2.3 Resumen semanal

```bash
python3 /home/nosvers/agents/agt07_diario/agt07_diario.py --semana --fecha 2026-05-12
```

**Espera**: Archivo `dia/resumenes/2026-W19.md` con secciones
"Hilos principales", "Tendencias", "Pendientes recurrentes",
"Distribución acumulada", "Comparación con semana anterior".

### 2.4 Notificación Telegram opt-in

```bash
TELEGRAM_NOTIFY_RESUMENES=1 python3 .../agt07_diario.py --dia --fecha 2026-05-12
```

**Espera**: Llega mensaje al chat de Angel con el resumen.

### 2.5 Cron instalado

```bash
cat /etc/cron.d/nosvers-voz
crontab -l -u nosvers
```

**Espera**: entradas presentes para `--dia` 23:30 y `--semana` domingos 22:00
y `purge_audio.py` 03:00.

---

## 3. Componente (b) — Cliente Linux casa (post revisión seguridad)

### 3.1 Wake word detecta "Claudio"

```bash
cd ~/nosvers-voz-linux
python3 -m nosvers_voz.wake --test
# Decir "Claudio" frente al micro
```

**Espera**: log "wake detectado, confianza=0.84" en < 1.5s.

### 3.2 Falsos positivos en ambiente normal

Dejar `python3 -m nosvers_voz.wake --test` corriendo 1 hora con
conversación normal, TV de fondo, etc.

**Espera**: < 1 falso positivo en una hora (SC-006).

### 3.3 Cooldown durante playback TTS

Iniciar sesión, hacer que Claude responda con frase que contenga
"claudio" deletreado por TTS.

**Espera**: el detector NO vuelve a disparar durante la respuesta.

### 3.4 STT local

```bash
python3 -m nosvers_voz.stt_local --file sample.wav
```

**Espera**: transcripción razonable del audio. Cero red.

### 3.5 TTS Kokoro

```bash
python3 -m nosvers_voz.tts_local --texto "Hola Angel, ¿qué tal la obra?" --voz ef_dora
```

**Espera**: WAV/audio se reproduce, voz natural, ~200ms de latencia.

### 3.6 Cambio de velocidad runtime

Iniciar sesión, decir "Claudio". Cuando responda, decir "habla más rápido".

**Espera**: la siguiente frase emite ~1.3× la velocidad anterior.

### 3.7 End-to-end

Decir "Claudio". Tras confirmación, decir
"Captura: comprar bombillas led para el invernadero".

**Espera**:
- En menos de 5s, la nota aparece en `dia/2026-05-12.md` con etiqueta
  `nosvers` u `otro`, origen `voz_linux`.
- Audio en `dia/audio/2026-05-12/HH-MM-SS.opus`.

---

## 4. Componente (c) — PWA Android

### 4.1 Instalación

Abrir `https://voz.nosvers.com` en Chrome del Android. "Añadir a pantalla
de inicio".

**Espera**: icono Calculín (o placeholder NosVers) en la pantalla home.
App se abre en modo standalone (sin URL bar).

### 4.2 Onboarding — pegar token

Primera apertura → pantalla pidiendo token. Pegar el JWT generado en
`/home/nosvers/voz/scripts/issue_token.py --device movil-angel`.

**Espera**: token validado, pantalla principal de captura.

### 4.3 Captura online

Conexión Wifi/4G activa. Pulsar botón grande "Grabar", dictar
"Llamar a Mario por el camión", soltar.

**Espera**:
- Feedback visual < 500ms ("nota encolada").
- En < 5s, badge "✓ sincronizado" o desaparición de la nota de la lista
  de pendientes.
- Nota aparece en `dia/<hoy>.md` con `origen=voz_movil`.

### 4.4 Captura offline (avión)

Modo avión ON. Dictar 3 notas con intervalos de minutos.

**Espera**:
- Las 3 notas aparecen en la lista de "pendientes" en la UI.
- Cada una tiene su timestamp local.
- IndexedDB DevTools: 3 registros en `notas_pendientes`.

### 4.5 Recuperar conexión

Quitar modo avión.

**Espera**:
- En < 30s, las 3 notas se suben automáticamente sin acción del usuario.
- Cada una llega al vault con su timestamp original (no el de sync).
- IndexedDB se vacía.

### 4.6 TTL local

Forzar el reloj del móvil 8 días adelante. Abrir la PWA.

**Espera**: cualquier `audio_blob` en IndexedDB > 7 días se purga al
arrancar la app. Las 3 notas del 4.5 ya están sync → IndexedDB vacía sin
problema.

### 4.7 Token expirado

Forzar revocación del token con `revoke_token.py`.

**Espera**: próximo intento de sync devuelve 401, la PWA muestra
banner "sesión expirada — pegar token nuevo" sin perder las notas
pendientes.

---

## 5. No regresión final

Repetir el checklist del paso 0 tras todo lo anterior.

**Espera**: cero diferencias respecto al estado inicial.

---

## 6. Logs y observabilidad

Tras una jornada de uso normal, revisar:

```bash
ls -la /home/nosvers/logs/voz_*.log
ls -la /home/nosvers/logs/agt07_diario.log
ls -la /home/nosvers/logs/mcp.log
```

**Espera**:
- Logs presentes y rotando (max 10MB cada uno, max 5 rotaciones).
- Ningún log contiene tokens en claro ni texto de notas de usuario.

---

## Checklist resumido

- [ ] Pre-flight OK
- [ ] dia_capturar texto + idempotencia
- [ ] dia_capturar audio
- [ ] dia_contexto
- [ ] dia_buscar
- [ ] Fallback clasificador
- [ ] Auth revocación
- [ ] Tests automáticos verdes
- [ ] Resumen diario manual y automático
- [ ] Resumen semanal
- [ ] Día vacío no crea archivo
- [ ] Cron instalado
- [ ] Wake word Claudio detecta
- [ ] < 1 falso positivo/h
- [ ] Cooldown TTS
- [ ] STT local
- [ ] TTS Kokoro
- [ ] Velocidad runtime
- [ ] End-to-end voz Linux
- [ ] PWA install + onboarding
- [ ] Captura online
- [ ] Captura offline + sync diferido
- [ ] TTL local
- [ ] Token expirado UX
- [ ] No regresión final
- [ ] Logs limpios y rotando
