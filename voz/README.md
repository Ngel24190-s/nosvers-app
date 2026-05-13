# voz/ — Asistente de Voz Personal NosVers

Módulo server-side del feature 001-voice-assistant. Captura, indexación
y búsqueda de notas dictadas por Angel y África, con resúmenes diarios
y semanales sintetizados por agt07_diario.

```
voz/
├── auth.py              Tokens JWT Bearer revocables (HS256, SQLite)
├── vault_io.py          Lectura/escritura del diario con flock + retries
├── stt.py               faster-whisper "small" (lazy load)
├── clasificar.py        Etiquetado Haiku → {trabajo,nosvers,familia,mental,idea,otro}
├── capturar.py          dia_capturar — orquesta STT + clasif + escribir
├── contexto.py          dia_contexto — síntesis Sonnet bajo demanda
├── buscar.py            dia_buscar — búsqueda con fragmento + <mark>
├── speaker_id.py        Identificación opcional de hablante
├── rest.py              FastAPI endpoints (montados en mcp_server.py)
├── data/                tokens.sqlite (NO commitear)
├── requirements.txt     faster-whisper, PyJWT, etc.
└── scripts/
    ├── issue_token.py   CLI emisión de tokens
    ├── revoke_token.py  CLI revocación / listado
    └── purge_audio.py   Cron 03:00: borra dia/audio/ >7d
```

## Endpoints y tools

| Capa | Operación | Implementación |
|------|-----------|----------------|
| MCP tool | `dia_capturar(texto, audio_b64, ts_iso, etiqueta, origen, autor, client_uuid)` | `mcp_server.py` → `voz.capturar.dia_capturar_impl` |
| MCP tool | `dia_contexto(rango_dias, incluir_calendario, incluir_estado_agentes, etiquetas_filtro, autor)` | `mcp_server.py` → `voz.contexto.dia_contexto_impl` |
| MCP tool | `dia_buscar(query, desde, hasta, limite, etiqueta, autor)` | `mcp_server.py` → `voz.buscar.dia_buscar_impl` |
| REST | `POST /voz/api/capturar` (JSON o multipart) | `voz/rest.py` — Bearer JWT |
| REST | `GET /voz/api/contexto` | `voz/rest.py` — Bearer JWT |
| REST | `GET /voz/api/buscar` | `voz/rest.py` — Bearer JWT |

## Tokens Bearer (JWT HS256)

Cada dispositivo (móvil Angel, móvil África, ordenador casa, etc.) tiene
su propio token, asociado a un `autor` (`angel` o `africa`). Los tokens
son **revocables**: el server consulta `tokens.sqlite` en cada llamada y
rechaza los `revoked_at` no nulos.

### Formato del JWT

```
Header  : { "alg": "HS256", "typ": "JWT" }
Payload : { "jti": "<uuid>",
            "device": "movil-angel",
            "autor":  "angel",
            "iat":    <unix-ts>,
            "exp":    <unix-ts> }   # iat + ttl_days
Sign    : HMAC-SHA256(secret = $VOZ_JWT_SECRET)
```

El secret se lee de `VOZ_JWT_SECRET` (fallback `MCP_TOKEN`). Sin secret,
`emitir_token()` falla en arranque — no hay tokens silenciosamente
inválidos.

### Emitir un token

```bash
ssh root@srv1313138.hstgr.cloud
cd /home/nosvers
python3 voz/scripts/issue_token.py \
    --device movil-angel \
    --autor angel \
    --ttl 365
```

Salida:

```
device: movil-angel
autor:  angel
jti:    7c3b1f9e-...
expira: 2027-05-13T11:00:00+02:00

JWT (pegar en la PWA):
eyJhbGciOi...
```

Pegar el JWT en el modal de token de la PWA (`https://nosvers-voz.72.61.160.108.nip.io/`).
El token queda **solo en localStorage del dispositivo**; nunca en el repo.

### Listar tokens activos

```bash
python3 voz/scripts/revoke_token.py --listar
```

```
7c3b1f9e-...  movil-angel           2027-05-13T11:00:00+02:00  activo
4a8e2d11-...  movil-africa          2027-05-13T11:05:00+02:00  activo
```

### Revocar un token

```bash
# Casos: dispositivo perdido, robo, rotación de credenciales tras incidente.
python3 voz/scripts/revoke_token.py --jti 7c3b1f9e-...
```

Tras revocar, el siguiente request del dispositivo recibe `401` y la PWA
muestra el banner "Token inválido o revocado — pega uno nuevo".

### Rotación periódica recomendada

| Frecuencia | Acción |
|-----------|--------|
| Anual (TTL default 365d) | Emitir nuevo + revocar viejo. Pegar el nuevo en cada dispositivo. |
| Tras incidente (móvil perdido / contraseña filtrada) | Revocación inmediata + nuevo token + auditar `dia/` desde la fecha del incidente. |
| Cambio de manos (Angel ↔ África) | Emitir token con el nuevo `--autor` y revocar el anterior. |

### Inspección manual de la BD

```bash
sqlite3 /home/nosvers/voz/data/tokens.sqlite \
    "SELECT jti, device_label, issued_at, expires_at, revoked_at FROM tokens;"
```

## Logs

Todos los componentes loguean en `/home/nosvers/logs/voz_*.log` y
`agt07_diario.log`. Rotación gestionada por
`/etc/logrotate.d/nosvers-voz` (10MB · 5 rotaciones · redacción de
`Bearer ey...` y `token=ey...` antes de comprimir).

## Tests

```bash
cd /home/nosvers && pytest tests/voz/ -v
```

Cobertura: `vault_io`, `auth`, `clasificar`, `stt` (mocked),
`capturar` (contrato + end-to-end), `contexto`, `buscar`, `agt07_diario`,
`speaker_id`.

## Constitución

- Cada nuevo tool MCP MUST tener prueba de contrato + integración (constitución v1.0.0).
- Tokens NUNCA en logs, repo o tracking system.
- `VOZ_JWT_SECRET` solo en `/home/nosvers/.env` (fuera del repo).
- Pool común `dia/` (BRIEF §14): notas con `autor: angel|africa` en frontmatter,
  audios con sufijo `_{autor}.opus`.
