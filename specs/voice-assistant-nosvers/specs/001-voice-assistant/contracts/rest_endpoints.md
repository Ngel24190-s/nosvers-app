# REST Endpoints Contract — PWA ↔ MCP server

**Feature**: 001-voice-assistant
**Date**: 2026-05-12 (actualizado 2026-05-13 por addendum BRIEF §14 multi-usuario)
**Base URL**: `https://nosvers-mcp.72.61.160.108.nip.io` (mismo binario que MCP)
**Path prefix**: `/voz/api`

Estos endpoints HTTP REST sirven a la PWA (Android, ambos usuarios) y al
cliente Linux casa. Viven en el mismo binario que el MCP server
(`/home/nosvers/mcp_server.py`) para preservar Constitution II
(MCP-First) — no son una API paralela sino un transporte alternativo del
mismo conjunto de tools.

**Auth**: Todos los endpoints requieren header
`Authorization: Bearer <jwt>` con un token emitido vía
`voz/scripts/issue_token.py --device X --autor angel|africa` cuyo `jti` no
esté revocado.

> **⚠ Addendum multi-usuario (BRIEF §14, 2026-05-13)**
> - El JWT lleva `sub: "angel" | "africa"` (identidad del usuario).
> - `POST /voz/api/capturar`: el servidor toma `autor` del JWT (`sub`).
>   El cliente puede enviar `autor` en el body sólo si coincide con el
>   `sub` del token (defensa contra override accidental). Otros valores
>   son ignorados.
> - `GET /voz/api/contexto?autor=angel|africa` (parámetro opcional).
> - `GET /voz/api/buscar?autor=angel|africa` (parámetro opcional).
> - Cada nota devuelta en `buscar` incluye `"autor": "..."`.
> - El response de `capturar` incluye `"autor": "..."`.

**Content-Type**: `application/json` para todas las requests salvo donde se
indique multipart.

---

## `POST /voz/api/capturar`

Captura una nota desde la PWA. Acepta texto puro o audio Opus.

**Request (texto)**:

```http
POST /voz/api/capturar HTTP/1.1
Authorization: Bearer eyJ...
Content-Type: application/json

{
  "texto": "Pedir fotos a África",
  "ts_iso": "2026-05-12T09:23:45+02:00",
  "etiqueta": "auto",
  "origen": "voz_movil",
  "device_label": "movil-angel",
  "client_uuid": "uuid-de-la-cola-pwa"
}
```

**Request (audio)**:

```http
POST /voz/api/capturar HTTP/1.1
Authorization: Bearer eyJ...
Content-Type: multipart/form-data; boundary=...

--boundary
Content-Disposition: form-data; name="meta"
Content-Type: application/json

{"ts_iso":"...","etiqueta":"auto","origen":"voz_movil",
 "device_label":"movil-angel","client_uuid":"..."}
--boundary
Content-Disposition: form-data; name="audio"; filename="nota.opus"
Content-Type: audio/opus

<bytes opus>
--boundary--
```

**Response 200**:

```json
{
  "ok": true,
  "archivo": "knowledge_base/angel/dia/2026-05-12.md",
  "ts": "2026-05-12T09:23:45+02:00",
  "etiqueta_aplicada": "nosvers",
  "confianza": 0.92,
  "modelo": "claude-haiku-4-5",
  "audio_persistido": "knowledge_base/angel/dia/audio/2026-05-12/09-23-45.opus",
  "client_uuid": "uuid-de-la-cola-pwa"
}
```

**Response 401** (token revocado/inválido):

```json
{"ok": false, "error": "auth_invalido"}
```

**Response 400**:

```json
{"ok": false, "error": "input_vacio | parametro_invalido", "detalle": "..."}
```

**Idempotencia**: El campo `client_uuid` permite a la PWA reintentar
sin duplicar. El servidor mantiene un cache LRU de los últimos 1000
`client_uuid` por device durante 1h. Reintento del mismo UUID en esa
ventana devuelve `200` con el resultado original.

**Comportamiento interno**: Delega en la misma función Python que
`dia_capturar` (MCP tool) — sólo cambia el transporte.

---

## `GET /voz/api/contexto?dias=7&calendario=1`

Síntesis del contexto reciente. Equivalente a `dia_contexto` por HTTP.

**Request**:

```http
GET /voz/api/contexto?dias=7&calendario=1&etiquetas=nosvers,trabajo
Authorization: Bearer eyJ...
```

**Response 200**:

```json
{
  "ok": true,
  "rango": {"desde": "2026-05-05", "hasta": "2026-05-12"},
  "notas_count": 38,
  "sintesis": "## Hilos principales\n\n…",
  "calendario": [
    {"start": "2026-05-13T09:00", "title": "Reunión Bordeaux"}
  ],
  "agentes": "agt02_instagram OK · agt05_africa esperando email"
}
```

---

## `GET /voz/api/buscar?q=lombrithé&desde=2026-04-01`

Búsqueda equivalente a `dia_buscar`.

**Response 200**:

```json
{
  "ok": true,
  "query": "lombrithé",
  "rango": {"desde": "2026-04-01", "hasta": "2026-05-12"},
  "total": 3,
  "resultados": [
    {"fecha": "2026-04-22", "ts": "2026-04-22T18:10:00+02:00",
     "etiqueta": "nosvers",
     "fragmento": "...el <mark>lombrithé</mark> tibio aceleró un 40%..."}
  ]
}
```

---

## `GET /voz/api/pendientes`

Devuelve metadatos de las notas pendientes en el servidor para una device.
Útil para que la PWA sincronice estado tras un wipe local.

**Response 200**:

```json
{
  "ok": true,
  "device_label": "movil-angel",
  "ultimo_sync": "2026-05-12T09:25:00+02:00",
  "notas_recientes": 38
}
```

---

## `POST /voz/api/token/refrescar`

Permite que la PWA refresque su token antes de expiración (auto-renovación
1 mes antes del expiry).

**Request**:

```json
{}
```

**Response 200**:

```json
{
  "ok": true,
  "token": "eyJ...",
  "expira": "2027-05-12T00:00:00Z",
  "jti": "uuid"
}
```

El servidor revoca el `jti` anterior tras emitir el nuevo.

---

## Tabla de status codes

| Código | Cuándo |
|---|---|
| 200 | OK incluso si la clasificación cayó a fallback `otro`. |
| 400 | Validación de input fallida. |
| 401 | Sin Bearer, Bearer inválido, o `jti` revocado. |
| 403 | Token válido pero scope insuficiente (futuro multi-tenant). |
| 413 | Audio > 5MB (límite duro). |
| 415 | Content-Type no soportado. |
| 429 | Rate limit (futuro; MVP no limita). |
| 500 | Excepción interna (loguea trace, no revela detalles). |
| 503 | Vault bloqueado tras reintentos. |

---

## Headers de respuesta comunes

| Header | Valor | Notas |
|---|---|---|
| `X-Request-Id` | UUID | Echoed/generado para correlación con logs. |
| `Cache-Control` | `no-store` para writes, `max-age=300` para `/contexto`. | |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` | HTTPS-only. |
| `X-Content-Type-Options` | `nosniff` | |

---

## CORS

`Access-Control-Allow-Origin: https://voz.nosvers.com`
`Access-Control-Allow-Methods: GET, POST, OPTIONS`
`Access-Control-Allow-Headers: Authorization, Content-Type, X-Request-Id`
`Access-Control-Max-Age: 86400`

Sólo el subdominio de la PWA está permitido. No `*`.
