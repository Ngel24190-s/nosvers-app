# Clarify — Decisiones tomadas en solitario (Fase 7)

Angel pidió: "clarify solo si crítico". Aquí van **únicamente** los puntos
donde el BRIEF dejaba ambigüedad y la decisión necesita constar para no
parar la implementación. Resto: se sigue el BRIEF al pie de la letra.

---

## D1. Proyecto frontend separado (NO mismo bundle que tablero/web)

**Decisión**: la PWA vive en `tablero/web-claudio/` como un proyecto Vite
nuevo, NO se mezcla con `tablero/web/` (el cockpit existente).

**Razón**:
- Bundle separado simplifica < 2 MB target (NFR-3).
- Service Worker distinto (cockpit no es PWA instalable, esta sí).
- Sub-dominio propio `claudio.72.61.160.108.nip.io` (Caddy vhost dedicado).
- Estética distinta (cockpit es glassmorphism oscuro, PWA tiene 3 themes).
- Riesgo cero de romper el cockpit en producción.

Se comparten: `tsconfig` base (extiende del padre), tipos del WS broker
(canales), helpers de auth. Se duplica tailwind config porque los themes
son específicos.

---

## D2. JWT no se reemite al cambiar contexto

**Decisión**: el token JWT permanece igual durante toda la sesión. El
contexto activo se guarda como **state cliente** en `localStorage` +
header `X-Claudio-Context` en cada request (o query param `?context=...`
para WS y endpoints GET).

`available_contexts` (lista) viaja en el JWT. `context` activo NO viaja
en el JWT — viaja en header/query, validado contra `available_contexts`
en cada call.

**Razón**: reemitir JWT a cada switch añadiría:
- Round-trip de red en cada toque de card.
- Otra ruta sensible (`/voz/api/contexto-set`) que mantiene el secret.
- Necesidad de invalidar token viejo o aceptar dos válidos.

El header es suficiente porque la validación crítica es server-side
(`requested in available_contexts`). El cliente NO puede acceder a tools
de trabajo aunque mienta — solo descubre que dice 403.

**Implicación**: FR-B-6 del spec se simplifica → endpoint
`/voz/api/contexto-set` se mantiene como API opcional de auditoría
(loguea el cambio), pero no es estrictamente necesario para la PWA.
Lo dejamos como NICE-TO-HAVE T140 en tasks.

---

## D3. Formato JWT extendido (campos)

**Decisión**: payload final:

```json
{
  "jti": "uuid",
  "device": "device-label",
  "iat": 1715688000,
  "exp": 1747224000,
  "sub": "angel",
  "available_contexts": ["casa", "nosvers", "trabajo"]
}
```

Campos viejos quedan idénticos. Campo nuevo opcional: si ausente, el
validador asume `["casa", "nosvers"]` (retro-compat estricta, NUNCA
trabajo por default).

**Razón**: tokens viejos de la PWA voz siguen funcionando, solo no ven
trabajo (correcto).

---

## D4. Filtrado de tools por contexto en el router

**Decisión**: el router de intent (`voz/intent_router.py`) recibe ahora
un kwarg `contexts_permitidos: set[str]`. Función pura:
`route_intent(text, autor, contexts_permitidos, threshold, timeout)`.

El handler `dictado_procesar_handler` deriva `contexts_permitidos` así:

```python
ctx_header = request.headers.get("x-claudio-context", "casa").lower()
if ctx_header not in payload.get("available_contexts", ["casa", "nosvers"]):
    return _json({"error": "context_no_autorizado"}, 403)
contexts_permitidos = _tools_por_contexto(ctx_header)
```

Donde `_tools_por_contexto` devuelve el subset de `ALLOWED_TOOLS`:

```python
TOOLS_POR_CONTEXTO = {
    "casa": <22 tools Fase 1 + dia_capturar>,
    "nosvers": <consultas familia + ningún tool de trabajo>,
    "trabajo": <10 tools trabajo + dia_capturar>,
}
```

El prompt del modelo se actualiza para incluir SOLO los tools del
contexto activo (genera menos confusión, mejor precisión).

**Razón**: el filtrado a nivel router evita que un dictado en contexto
Casa accidentalmente cree un chantier; el modelo NUNCA verá esos tools.

---

## D5. Estética Trabajo — fuentes

**Decisión**: usar **Inter** con `font-weight: 900` y `letter-spacing:
-0.04em` como sustituto de "condensada" cuando no haya `Bebas Neue`
local. Cargar Inter desde `@fontsource/inter` (npm, self-hosted, sin
Google Fonts CDN).

**Razón**:
- Soberanía → no Google Fonts.
- Inter Black + tracking-tighter visualmente *muy* similar a condensada
  para titulares cortos.
- Bebas Neue tendría que descargarse y pesa ~80 KB. Si el bundle lo
  permite, se añade en una iteración. De momento Inter es suficiente.

Casa/NosVers usan Playfair Display + DM Sans (ya en design system
NosVers, `contexto/nosvers-design-system.md`). Estos también
self-hosted vía `@fontsource/*`.

---

## D6. Logo DI en card Trabajo

**Decisión**: NO usar imagen. Renderizar el "logo DI" como texto:
`<span class="font-black tracking-tighter text-black text-7xl">DI</span>`
en card home + header de contexto Trabajo.

**Razón**:
- Cero asset binario.
- Escala perfecta en cualquier resolución.
- Edita Angel cuando quiera el wording oficial DI Environnement.

Si Angel proporciona un SVG, se mete en `public/di-logo.svg` y se sustituye.

---

## D7. Worker `trabajo.py` — qué publica

**Decisión**: canal WS `trabajo` publica snapshot:

```json
{
  "chantiers_activos": 2,
  "alertas": [
    {"chantier": "bordeaux-nord", "tipo": "seguridad", "fecha": "2026-05-14"}
  ],
  "ultimo_evento": {
    "chantier": "bordeaux-nord",
    "tipo": "avance",
    "descripcion": "Acabada zona 2",
    "autor": "angel",
    "fecha": "2026-05-14"
  },
  "equipe_disponible": 4,
  "ts": "2026-05-14T15:00:00Z"
}
```

Refresca cada 60 s. Solo enviado a clientes que se suscribieron con
`?context=trabajo` y JWT que lo autorice. Si no hay clientes elegibles,
el worker corre igual pero no emite (snapshot disponible para próximo
suscriptor).

**Razón**: mismo patrón que `revenue`, `health` etc. (cockpit fase 3).

---

## D8. Service Worker — qué cachea de Trabajo

**Decisión**: cache `/tablero/api/v3/trabajo/*` solo si el último GET
fue exitoso con JWT trabajo. Si el usuario cambia de cuenta (otro JWT),
purgar cache de v3. Implementación: namespace cache por hash del JWT
`sub`.

**Razón**: África NO debe poder ver chantiers cacheados de Angel
aunque comparta dispositivo. Defensa contra cache leak.

---

## D9. Bug telegram_enviar conocido

**Decisión**: NO se invoca `telegram_enviar` durante la implementación,
ni siquiera para notificar al final. La memoria del proyecto ya recoge
esta regla. Si una verificación final lo necesitase, abortar tras 30 s
y marcar `MCP_STALL_RESOLVED_BY_OPUS_MOBILE` en `tasks.md`.

Angel verá el resultado por:
- `git log` (commits agrupados).
- Visita manual a `https://claudio.72.61.160.108.nip.io`.
- `tasks.md` con checkboxes [x].

---

## D10. Wake-word fuera de scope

**Decisión**: NO implementar wake-word "claudio" en esta fase. El BRIEF
lo marca como Fase 8 (TWA / Capacitor). Solo se mantiene el hint en
home: "o di 'claudio' desde el PC casa" — porque ya existe la integración
PC desde 006.

---

## D11. Tipos compartidos cliente ⇄ servidor

**Decisión**: no se genera un cliente OpenAPI. Se mantienen tipos
TypeScript en `tablero/web-claudio/src/lib/api-types.ts` escritos a
mano, mirando los handlers Python.

**Razón**: el contrato es pequeño (~10 endpoints), un cliente OpenAPI
añadiría toolchain. Mejor disciplina manual + tests E2E que cazan drift.

---

## D12. Identidad visual Trabajo — paleta exacta

| Token | Valor |
|---|---|
| `--trabajo-bg` | `#FFFFFF` |
| `--trabajo-fg` | `#000000` |
| `--trabajo-primary` | `#D62828` (rojo DI) |
| `--trabajo-primary-dark` | `#A91D1D` (hover, focus ring) |
| `--trabajo-accent` | `#000000` |
| `--trabajo-muted` | `#1A1A1A` (texto secundario) |
| `--trabajo-border` | `#000000` |
| `--trabajo-on-primary` | `#FFFFFF` |

Casa:
| Token | Valor |
|---|---|
| `--casa-bg` | `#FEFAF4` |
| `--casa-fg` | `#1c1510` |
| `--casa-primary` | `#5A7A2E` (verde NosVers) |
| `--casa-accent` | `#D97706` (amber-600) |
| `--casa-emerald` | `#34d399` |

NosVers:
| Token | Valor |
|---|---|
| `--nosvers-bg` | `#FEFAF4` |
| `--nosvers-fg` | `#1c1510` |
| `--nosvers-primary` | `#5A7A2E` |
| `--nosvers-emerald` | `#10b981` |
| `--nosvers-amber` | `#92400E` (tonos tierra) |

---

*Clarify NosVers Claudio Fase 7 — 2026-05-14*
