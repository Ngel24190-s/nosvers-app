---
nombre: pwa-contextos
fase: 007
creado: 2026-05-14
estado: live
---

# Claudio PWA Contextos · 007

PWA familiar instalable con **3 contextos isolated** (Casa, NosVers,
Trabajo). Estética propia por contexto. PTT global hold-to-talk con 5
fases. Servida desde `claudio.72.61.160.108.nip.io`.

## URL principal

- **PWA**: https://claudio.72.61.160.108.nip.io
- **API trabajo**: https://claudio.72.61.160.108.nip.io/tablero/api/v3/trabajo/*
- **API familia/general**: https://claudio.72.61.160.108.nip.io/tablero/api/v2/*
- **PTT endpoint**: POST https://claudio.72.61.160.108.nip.io/voz/api/dictado-procesar

Acepta JWT en `Authorization: Bearer ...` y contexto en
`X-Claudio-Context: casa|nosvers|trabajo`.

## Arquitectura

```
PWA frontend                          Backend
─────────────                         ───────
tablero/web-claudio/  ──── Caddy ────▶ tablero/v2 (port 8766)
  Vite + React + TS    claudio.72…    ├── /tablero/api/v2/*
  Tailwind 3 themes                   ├── /tablero/api/v3/trabajo/*
  framer-motion + lucide              ├── /voz/api/dictado-procesar
  SW offline read                     ├── WS broker (canal "trabajo")
                                      └── workers (recordatorios, gastos,
                                                   compras, revenue,
                                                   trabajo, ...)
```

Stack ya existente reutilizado:
- JWT auth: `voz/auth.py` (extendido en 007 con `available_contexts`).
- Intent router: `voz/intent_router.py` (extendido con
  `contexts_permitidos`).
- Tools MCP: `claudio_tools/` (10 tools nuevos en `trabajo.py`).
- Broker WS: `tablero/v2/ws.py` (canal `trabajo` con scope gating).

## JWT extendido

Payload:
```json
{
  "jti": "...",
  "sub": "angel|africa",
  "device": "...",
  "iat": 1715688000,
  "exp": 1747224000,
  "available_contexts": ["casa", "nosvers", "trabajo"]
}
```

Reglas:
- `trabajo` solo se concede a `sub=angel`. `emitir_token()` lanza
  `ValueError` si África pidiera `trabajo`.
- Tokens viejos sin `available_contexts` se tratan como
  `["casa", "nosvers"]` (default seguro, NUNCA trabajo).
- `voz.auth.check_context(payload, requested)` es el único punto de
  verificación. Lo usa: `voz/rest.py` dictado-procesar,
  `tablero/v2/api_trabajo.py`, `tablero/v2/ws.py` (subscribe).

## Emisión de tokens

Script ad-hoc desde el VPS:
```bash
cd /home/nosvers
export $(grep -v '^#' .env | xargs)
python3 -c "
from voz.auth import emitir_token
t_angel = emitir_token('android-angel', autor='angel')   # 3 contextos
t_africa = emitir_token('android-africa', autor='africa')  # 2 contextos
print('ANGEL:', t_angel['jwt'])
print('AFRICA:', t_africa['jwt'])
"
```

Luego abrir la PWA con `?token=<jwt>` en la URL (la PWA lo guarda en
`localStorage` y limpia la URL).

## Identidad visual por contexto

| Contexto | bg | primary | accent | tipografía | tono |
|---|---|---|---|---|---|
| Casa | `#FEFAF4` | `#5A7A2E` | `#D97706` amber | Playfair + DM Sans | cálido familiar |
| NosVers | `#FEFAF4` | `#5A7A2E` | `#10b981` emerald | DM Serif + DM Sans | sobrio KPI |
| Trabajo | `#FFFFFF` | `#D62828` rojo DI | `#000000` | Inter Black + tracking-tighter | bicromático, MAYÚSCULAS, técnico |

El contexto activo se aplica via
`document.documentElement.dataset.context`. Las variables CSS están en
`src/styles/themes.css`.

## Vault Trabajo (aislado)

`public_html/knowledge_base/trabajo/` — solo accesible con JWT que
incluya `trabajo` en `available_contexts`.

```
trabajo/
├── chantiers/{slug}/INDEX.md, journal/YYYY-MM-DD.md
├── equipe/operateurs.yaml, formations/{op}/{año}.md
├── documents/{ppsps,plans-retrait,devis,certificats,diag-amiante}/
├── clients/
├── materiel/
├── normes/
└── formations/
```

África NO ve este vault — ni desde la PWA ni desde la API
(`/tablero/api/v3/trabajo/*` responde 403 a su JWT).

## 10 Tools MCP del contexto Trabajo

Modulo: `claudio_tools/trabajo.py`. Registrados en `mcp_server.py`.

| Tool | Qué hace |
|---|---|
| `chantier_listar(estado)` | activos / archivados / urgentes / todos |
| `chantier_crear(...)` | crea slug, INDEX.md, journal/ vacío |
| `chantier_evento(slug, tipo, descripcion, autor)` | append a journal |
| `chantier_estado(slug)` | snapshot completo |
| `chantier_documento_listar(slug, tipo)` | docs asociados |
| `equipe_listar()` | operadores activos |
| `equipe_anotar(operario, evento, fecha)` | append formación/incidente |
| `devis_anotar(cliente, monto, chantier_ref)` | append a devis |
| `ppsps_crear(chantier, version, observaciones)` | plantilla PPSPS |
| `documento_trabajo_archivar(tipo, contenido, chantier_ref)` | archivo |

Resolución de slug en `chantier_evento`/`chantier_estado`/`chantier_documento_listar`:
tolerante a keyword/prefijo (`bordeaux` → `bordeaux-nord-rehabilitation`
si es único match).

## Filtrado de tools por contexto (intent_router)

`voz/intent_router.TOOLS_POR_CONTEXTO`:

- `casa`: 22 tools Fase 1 + `dia_capturar`.
- `nosvers`: subset consulta (`claudio_contexto`, `documentos_buscar`,
  `dia_capturar`).
- `trabajo`: 10 tools nuevos + `dia_capturar` fallback.

El router construye el prompt con `tools_visibles =
ALLOWED_TOOLS & contexts_permitidos`. Tools no incluidos en el contexto
activo nunca se generan; si el modelo intentara, el wrapper cae a
`dia_capturar`.

`dia_capturar` con `context=trabajo` etiqueta la nota como `trabajo` y
origen `dictado:trabajo` (vault aislado).

## PTT hold-to-talk (5 fases)

Componente: `src/components/PTTOverlay.tsx`.

State machine: `idle → recording → sending → thinking → speaking →
idle`.

Gestos (pointer events):
- `pointerdown` + hold 200ms → recording (waveform Canvas live).
- `pointerup` → sending (envía multipart audio a `/voz/api/capturar` +
  POST a `/voz/api/dictado-procesar` con transcript).
- `pointermove` con dy < -80 px → cancel armed (suelta → cancelar).
- `pointercancel` o blur → cancel.
- Double-tap < 300ms → conversación 30s.

Audio: `MediaRecorder` WebM/Opus (fallback audio/mp4 en iOS).
`AnalyserNode` FFT para waveform (28 barras, 60 fps; 1 barra con
`prefers-reduced-motion`).

## Service Worker

`public/sw.js`: precache shell + stale-while-revalidate para GET API.
NO cachea POST. Bumpear `CACHE_NAME` (`claudio-pwa-vN`) en cada release.

`SKIP_WAITING` message disponible:
```js
navigator.serviceWorker.controller?.postMessage({ type: 'SKIP_WAITING' });
```

## Build + deploy

```bash
cd /home/nosvers/tablero/web-claudio
npm install            # solo si dependencies cambiaron
npm run build          # → dist/
# bumpear CACHE_NAME en public/sw.js antes del build
sudo systemctl reload caddy
```

Verificar:
```bash
curl -sk https://claudio.72.61.160.108.nip.io/ | head -3   # 200
curl -sk -D - https://claudio.72.61.160.108.nip.io/sw.js -o /dev/null | grep Cache-Control
```

## Caddy vhost

Bloque añadido al final de `/etc/caddy/Caddyfile`:

```caddy
claudio.72.61.160.108.nip.io {
    encode gzip
    @sw path /sw.js
    header @sw Cache-Control "no-cache, no-store, must-revalidate"
    @manifest path /manifest.json
    header @manifest Cache-Control "no-cache"
    @ws { header Connection *Upgrade* ; header Upgrade websocket }
    handle @ws { reverse_proxy localhost:8766 { transport http { versions 1.1 } } }
    handle /tablero/api/* { reverse_proxy localhost:8766 }
    handle /voz/api/* { reverse_proxy localhost:8766 }
    handle { root * /home/nosvers/tablero/web-claudio/dist ; try_files {path} /index.html ; file_server }
    request_body { max_size 20MB }
}
```

## Tests

- `tests/test_auth_contexts.py` — 7 casos (default, escope angel/africa,
  retro-compat).
- `tests/test_trabajo_tools.py` — 12 casos (10 tools + fuzzy slug +
  documents).
- `tests/test_intent_router.py` — 25 casos existentes siguen verde.

```bash
cd /home/nosvers
VOZ_JWT_SECRET=test python3 -m pytest tests/test_auth_contexts.py tests/test_trabajo_tools.py tests/test_intent_router.py -q
```

Smoke E2E manual:
```bash
# Angel ve los 3 endpoints
curl -sk -H "Authorization: Bearer $T_ANGEL" \
  https://claudio.72.61.160.108.nip.io/tablero/api/v3/trabajo/chantiers
# {"ok":true,"chantiers":[...]}

# África → 403
curl -sk -H "Authorization: Bearer $T_AFRICA" \
  https://claudio.72.61.160.108.nip.io/tablero/api/v3/trabajo/chantiers
# {"ok":false,"error":"context_no_autorizado"}
```

## Cómo añadir...

### un tool al contexto Trabajo

1. Implementar la función en `claudio_tools/trabajo.py`. Devuelve `str`.
2. Registrar `@mcp.tool()` en `mcp_server.py` (bloque trabajo).
3. Añadir el nombre a `TOOLS_TRABAJO` en `voz/intent_router.py`.
4. Mapear el dispatch en `voz/rest.py` `_execute_intent` (sección trabajo).
5. Actualizar `public_html/knowledge_base/prompts/intent_router.md`
   (sección Trabajo) con un ejemplo.

### un canal WS nuevo

1. Worker en `tablero/v2/workers/<canal>.py` que devuelve dict snapshot.
2. Registrar en `tablero/v2/workers/__init__.py` `register_all()`.
3. Añadir nombre a `VALID_CHANNELS` en `tablero/v2/ws.py`.
4. Si requiere scope: añadir entry a `CHANNEL_SCOPE`.
5. Front: usar `useChannel<T>('canal')` desde el componente.

### un widget al contexto Casa o NosVers

1. Crear `src/components/<contexto>/tabs/<Tab>.tsx`.
2. Importar y montar en el shell del contexto
   (`CasaShell.tsx` / `NosVersShell.tsx`).
3. Usar `useChannel` o `apiJson` con `context: '<ctx>'`.

### editar themes

1. Cambiar variables CSS en `src/styles/themes.css` bajo el selector
   correspondiente.
2. NO tocar Tailwind config — los nombres `bg-bg`, `text-fg`,
   `bg-primary` etc. se mantienen.

## Definition of Done — checklist

- [x] Sub-dominio `claudio.72.61.160.108.nip.io` sirve la PWA con cert Let's Encrypt.
- [x] 3 contextos navegables con identidades visuales diferenciadas (Casa cálido, NosVers verde, Trabajo bicromático).
- [x] PTT hold-to-talk funcional con 5 fases (idle/recording/sending/thinking/speaking).
- [x] `/voz/api/dictado-procesar` consume `context` desde JWT/header y filtra tools.
- [x] Vault `trabajo/` creado con estructura, README, stubs normes.
- [x] 10 tools MCP nuevos del dominio Trabajo registrados.
- [x] Token Angel emitido con `[casa, nosvers, trabajo]`. Token África con `[casa, nosvers]`. Intento África+trabajo → 403.
- [x] Frontend bundle compilado (`< 2 MB gzip`: JS+CSS ~100 KB gz).
- [x] Service Worker registrado, offline-lectura habilitada.
- [x] Tests: 7 (auth) + 12 (trabajo) + 25 (intent_router) = 44 verdes.
- [x] Documentación `claudio/PWA_CONTEXTOS.md` (este archivo).

## Bug telegram_enviar — recordatorio

NO se invocó `telegram_enviar` durante la implementación (memoria del
proyecto). Si alguna verificación final lo necesitase, abortar tras 30s
y marcar `MCP_STALL_RESOLVED_BY_OPUS_MOBILE` en `tasks.md`.

---

*Fase 007 cerrada · 2026-05-14*
