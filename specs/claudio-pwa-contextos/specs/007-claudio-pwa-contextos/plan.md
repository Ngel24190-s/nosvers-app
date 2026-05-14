# Implementation Plan — Claudio PWA Contextos (007)

**Feature**: `007-claudio-pwa-contextos`
**Created**: 2026-05-14
**Status**: Ready for tasks

---

## Estrategia general

Construir en 4 capas, de profunda a superficial:

1. **Backend foundation** (Python) — JWT extendido, validación contexto,
   vault `trabajo/`, 10 tools MCP, endpoints v3 trabajo, worker WS
   `trabajo`, intent_router contextualizado.
2. **Infra** (Caddy) — vhost `claudio.72.61.160.108.nip.io`, reverse
   proxy `/voz/api/*` y `/tablero/api/*`.
3. **PWA frontend** (Vite + React + TS + Tailwind) — proyecto nuevo
   `tablero/web-claudio/`, 3 themes, home, contextos, PTT, SW.
4. **Tests + docs** — pytest scope JWT, vitest smoke, doc final.

Capas 1 y 2 desbloquean 3; 4 cierra.

---

## Stack

| Componente | Tecnología | Versión / detalle |
|---|---|---|
| Backend | Python 3.11 + Starlette | ya presente |
| JWT | PyJWT (HS256) | ya presente |
| WS broker | asyncio + websockets | reusa `tablero/v2/ws.py` |
| MCP tools | módulos en `claudio_tools/` | extiende patrón Fase 1 |
| Frontend | Vite 5 + React 18 + TS 5 | nuevo |
| CSS | Tailwind 3 (con data-attribute themes) | nuevo |
| Animaciones | framer-motion 11 | tree-shaken |
| Iconos | lucide-react | tree-shaken por uso |
| Audio | Web Audio API + MediaRecorder | nativo |
| Service Worker | manual (Workbox-equivalent) | sin Workbox dep |
| Fonts | @fontsource/* (self-hosted) | Inter + Playfair + DM Sans |
| Tests Python | pytest + monkeypatch | ya configurado |
| Tests JS | vitest + @testing-library/react + jsdom | nuevo |
| Caddy | Caddy 2 (ya en VPS) | añadir vhost |

Cero deps cloud nuevas. Solo Vite + ecosistema.

---

## Estructura de archivos

### Nuevos

```
public_html/knowledge_base/trabajo/
├── README.md                     ← este vault es Angel-only
├── chantiers/INDEX.md            ← lista
├── chantiers/_ejemplo/INDEX.md   ← plantilla
├── equipe/operateurs.yaml        ← seed vacío
├── documents/{ppsps,plans-retrait,devis,certificats,diag-amiante}/.gitkeep
├── clients/INDEX.md
├── materiel/inventario.yaml
├── normes/inrs-ed-6262.md        ← stub legal
├── normes/code-travail.md        ← stub
├── normes/proteccion-individual.md ← stub
└── formations/.gitkeep

claudio_tools/
└── trabajo.py                    ← 10 tools

tablero/v2/
├── api_trabajo.py                ← handlers v3 endpoints (alternativa: inline en ws.py)
└── workers/trabajo.py            ← worker WS

tablero/web-claudio/              ← PWA nueva
├── package.json
├── vite.config.ts
├── tailwind.config.ts
├── tsconfig.json
├── postcss.config.js
├── index.html
├── public/
│   ├── manifest.json
│   ├── sw.js
│   ├── icon-192.png              ← generar / placeholder
│   ├── icon-512.png
│   └── apple-touch-icon.png
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── styles/
│   │   ├── index.css             ← Tailwind + variables CSS por contexto
│   │   └── themes.css            ← data-context overrides
│   ├── lib/
│   │   ├── api.ts                ← fetch wrapper con JWT + X-Claudio-Context
│   │   ├── api-types.ts          ← shapes endpoints
│   │   ├── auth.ts               ← localStorage JWT helpers
│   │   ├── ws.ts                 ← WebSocket hook contextual
│   │   ├── audio.ts              ← MediaRecorder + AnalyserNode helpers
│   │   └── context.ts            ← ContextProvider / hook
│   ├── components/
│   │   ├── PTTOverlay.tsx        ← global, 5 fases
│   │   ├── PTTFab.tsx            ← botón flotante
│   │   ├── Waveform.tsx          ← Canvas + analyser
│   │   ├── NeuralGraph.tsx       ← thinking phase
│   │   ├── ContextSwitcher.tsx   ← header con context activo
│   │   ├── BottomTabs.tsx        ← 4-5 tabs por contexto
│   │   ├── home/
│   │   │   ├── HomeScreen.tsx
│   │   │   ├── CardCasa.tsx
│   │   │   ├── CardNosVers.tsx
│   │   │   └── CardTrabajo.tsx
│   │   ├── casa/
│   │   │   ├── CasaShell.tsx
│   │   │   ├── tabs/Hoy.tsx
│   │   │   ├── tabs/Listas.tsx
│   │   │   ├── tabs/Gastar.tsx
│   │   │   ├── tabs/Recordar.tsx
│   │   │   └── tabs/Casa.tsx
│   │   ├── nosvers/
│   │   │   ├── NosVersShell.tsx
│   │   │   ├── tabs/HoyGranja.tsx
│   │   │   ├── tabs/Huerto.tsx
│   │   │   ├── tabs/Tienda.tsx
│   │   │   ├── tabs/AAPPMA.tsx
│   │   │   └── tabs/CockpitMini.tsx
│   │   └── trabajo/
│   │       ├── TrabajoShell.tsx
│   │       ├── tabs/Aujourdhui.tsx
│   │       ├── tabs/Chantiers.tsx
│   │       ├── tabs/Equipe.tsx
│   │       └── tabs/Docs.tsx
│   └── tests/
│       ├── home.test.tsx
│       ├── ptt.test.tsx
│       └── context-scope.test.tsx
└── dist/ (output)

specs/007-claudio-pwa-contextos/
├── spec.md
├── clarify.md
├── plan.md
└── tasks.md
```

### Modificados

```
voz/auth.py                       ← emitir_token añade contexts, validar añade default
voz/intent_router.py              ← acepta contexts_permitidos
voz/rest.py                       ← dictado_procesar_handler lee X-Claudio-Context
mcp_server.py                     ← registra los 10 tools trabajo
tablero/v2/ws.py                  ← +1 canal "trabajo" en VALID_CHANNELS, query param ?context
tablero/v2/workers/__init__.py    ← register trabajo worker
tablero/v2/rest.py o api.py       ← /tablero/api/v3/trabajo/* handlers
tablero/v2/api_v2.py o rest       ← endpoints v2 aceptan ?context (filtro suave)
/etc/caddy/Caddyfile              ← +bloque claudio.72.61.160.108.nip.io
public_html/knowledge_base/claudio/PWA_CONTEXTOS.md ← doc final
```

---

## Contratos exactos

### Backend Python

#### `voz/auth.py` — extensión

```python
AUTORES_VALIDOS = {"angel", "africa"}
CONTEXTS_DEFAULT = ["casa", "nosvers"]
CONTEXTS_TRABAJO_ONLY = {"trabajo"}

def emitir_token(
    device_label: str,
    ttl_days: int = 365,
    autor: str = "angel",
    contexts: list[str] | None = None,
) -> dict:
    autor = autor.strip().lower()
    if autor not in AUTORES_VALIDOS: raise ValueError(...)
    if contexts is None:
        contexts = ["casa", "nosvers", "trabajo"] if autor == "angel" else CONTEXTS_DEFAULT
    contexts = [c.strip().lower() for c in contexts]
    # Defense in depth: trabajo solo para Angel
    if "trabajo" in contexts and autor != "angel":
        raise ValueError("contexto trabajo solo permitido para angel")
    for c in contexts:
        if c not in {"casa", "nosvers", "trabajo"}:
            raise ValueError(f"contexto inválido: {c}")
    # payload
    payload = {
        "jti": jti, "device": device_label, "iat": ..., "exp": ..., "sub": autor,
        "available_contexts": contexts,
    }
    ...

def check_context(payload: dict, requested: str) -> bool:
    """True si el JWT autoriza el contexto solicitado."""
    if not payload: return False
    requested = (requested or "").strip().lower()
    if requested not in {"casa", "nosvers", "trabajo"}: return False
    if requested == "trabajo" and payload.get("sub") != "angel": return False
    available = payload.get("available_contexts") or CONTEXTS_DEFAULT
    return requested in available
```

#### `voz/intent_router.py` — extensión

```python
def route_intent(
    text: str,
    autor: str,
    contexts_permitidos: set[str] | None = None,  # NUEVO
    threshold: float = 0.6,
    timeout: float = 4.0,
) -> IntentResult:
    """Si contexts_permitidos es None, asume ALLOWED_TOOLS completo (retro-compat)."""
    if contexts_permitidos is None:
        contexts_permitidos = ALLOWED_TOOLS
    # prompt se construye con la intersección
    tools_visibles = sorted(ALLOWED_TOOLS & contexts_permitidos)
    prompt = _build_prompt(tools_visibles)
    ...
    # tras decisión Haiku, validar:
    if decision.tool not in contexts_permitidos:
        decision.fallback = True
        decision.tool = "dia_capturar"
```

Mapping:
```python
TOOLS_POR_CONTEXTO = {
    "casa": ALLOWED_TOOLS_FASE1,                            # 22 + dia_capturar
    "nosvers": {"claudio_contexto", "claudio_recordar",     # consulta + capturar
                "documentos_buscar", "dia_capturar"},
    "trabajo": {"chantier_listar", "chantier_crear",
                "chantier_evento", "chantier_estado",
                "equipe_listar", "equipe_anotar",
                "devis_anotar", "ppsps_crear",
                "documento_trabajo_archivar",
                "chantier_documento_listar",
                "dia_capturar"},
}
```

#### `voz/rest.py` — extensión `dictado_procesar_handler`

Solo cambia 3 líneas en este handler:

```python
async def dictado_procesar_handler(request):
    payload = await _autenticar(request)
    if not payload: return _json({"error": "auth_invalido"}, 401)
    autor = payload.get("sub", "angel")
    ctx = request.headers.get("x-claudio-context", "casa").lower()
    from .auth import check_context
    if not check_context(payload, ctx):
        return _json({"error": "context_no_autorizado"}, 403)
    contexts_permitidos = TOOLS_POR_CONTEXTO.get(ctx, set())
    body = await request.json()
    transcript = (body or {}).get("transcript", "").strip()
    if not transcript: return _json({"error": "input_vacio"}, 400)
    intent = await route_intent(transcript, autor, contexts_permitidos=contexts_permitidos)
    # resto idéntico a Fase 2
    ...
```

#### `claudio_tools/trabajo.py` — esqueleto

```python
"""Tools MCP del contexto Trabajo (DI Environnement)."""
from pathlib import Path
from datetime import datetime, date
import yaml
import re

from .common import normalize_author, slugify, append_md, log_jsonl, vault_root

TRABAJO_ROOT = lambda: vault_root() / "trabajo"

def _ensure_skeleton():
    root = TRABAJO_ROOT()
    for sub in ("chantiers", "equipe", "documents/ppsps",
                "documents/plans-retrait", "documents/devis",
                "documents/certificats", "documents/diag-amiante",
                "clients", "materiel", "normes", "formations"):
        (root / sub).mkdir(parents=True, exist_ok=True)
    (root / "chantiers/INDEX.md").touch(exist_ok=True)

def chantier_listar(estado: str = "activos") -> str:
    ...

def chantier_crear(nombre, direccion, cliente, devis_eur, equipe_ids,
                   fecha_inicio, fecha_fin_prev) -> str:
    ...

# ... 8 funciones más
```

Cada tool:
- Llama `_ensure_skeleton()` al inicio (idempotente).
- Usa `slugify` de `claudio_tools.common`.
- Loguea `log_jsonl("trabajo", tool=..., args=..., result=...)`.

#### `tablero/v2/workers/trabajo.py`

```python
"""Worker que publica snapshot del dominio trabajo cada 60 s."""
import asyncio
from pathlib import Path
from datetime import datetime
import yaml

CHANNEL = "trabajo"
INTERVAL = 60.0

async def run(broker):
    while True:
        snapshot = _build_snapshot()
        await broker.publish(CHANNEL, snapshot)
        await asyncio.sleep(INTERVAL)

def _build_snapshot() -> dict:
    root = Path("/home/nosvers/public_html/knowledge_base/trabajo")
    if not root.exists():
        return {"empty": True, "ts": datetime.utcnow().isoformat()}
    # leer chantiers activos, último evento, alertas
    ...
```

#### `tablero/v2/api_trabajo.py`

```python
from starlette.routing import Route
from starlette.responses import JSONResponse
from voz.auth import validar_token, check_context

async def chantiers_handler(request):
    payload = _auth(request)
    if not check_context(payload, "trabajo"):
        return JSONResponse({"error": "scope"}, 403)
    estado = request.query_params.get("estado", "activos")
    # leer vault trabajo/chantiers/INDEX.md
    return JSONResponse({"chantiers": [...], "total": n})

# Routes:
routes_v3 = [
    Route("/tablero/api/v3/trabajo/chantiers", chantiers_handler, methods=["GET"]),
    Route("/tablero/api/v3/trabajo/chantier/{slug}", chantier_detail_handler),
    Route("/tablero/api/v3/trabajo/equipe", equipe_handler),
    Route("/tablero/api/v3/trabajo/documents", documents_handler),
]
```

### Frontend

#### `tablero/web-claudio/package.json`

```json
{
  "name": "claudio-pwa",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview",
    "test": "vitest run"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "framer-motion": "^11.0.0",
    "lucide-react": "^0.400.0",
    "@fontsource/inter": "^5.0.0",
    "@fontsource/playfair-display": "^5.0.0",
    "@fontsource/dm-sans": "^5.0.0",
    "@fontsource/dm-serif-display": "^5.0.0"
  },
  "devDependencies": {
    "vite": "^5.0.0",
    "@vitejs/plugin-react": "^4.3.0",
    "typescript": "^5.4.0",
    "tailwindcss": "^3.4.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0",
    "vitest": "^1.6.0",
    "@testing-library/react": "^16.0.0",
    "jsdom": "^24.0.0"
  }
}
```

#### `tablero/web-claudio/src/lib/context.ts`

```ts
type Context = "casa" | "nosvers" | "trabajo";

interface ContextState {
  current: Context;
  available: Context[];
  setContext: (c: Context) => void;
}

// Provider lee available del JWT decoded en cliente (sin verificar firma —
// backend valida; cliente solo necesita saber qué mostrar).
// localStorage.setItem("claudio.context", c) persiste.
// Aplica data-context al <html> root.
```

#### `tablero/web-claudio/src/components/PTTOverlay.tsx`

State machine: `idle | recording | sending | thinking | speaking`.

```ts
type Phase = "idle" | "recording" | "sending" | "thinking" | "speaking";
```

Gestos via `pointerdown/move/up/cancel` en el FAB, no `touchstart` (mejor
soporte cross-device).

---

## Caddy vhost (FR-L)

Añadir al final de `/etc/caddy/Caddyfile`:

```caddy
# ── PWA Claudio (3 contextos) ───────────────────────────────────────
claudio.72.61.160.108.nip.io {
    encode gzip

    @sw path /sw.js
    header @sw Cache-Control "no-cache, no-store, must-revalidate"

    @manifest path /manifest.json
    header @manifest Cache-Control "no-cache"

    @ws {
        header Connection *Upgrade*
        header Upgrade websocket
    }
    handle @ws {
        reverse_proxy localhost:8766 {
            transport http {
                versions h1
            }
        }
    }

    handle /tablero/api/* {
        reverse_proxy localhost:8766
    }
    handle /voz/api/* {
        reverse_proxy localhost:8766
    }

    handle {
        root * /home/nosvers/tablero/web-claudio/dist
        try_files {path} /index.html
        file_server
    }

    request_body {
        max_size 20MB
    }
}
```

Reload Caddy: `systemctl reload caddy`.

---

## Plan de ejecución (orden)

1. **Spec Kit files** — ya está (spec.md, clarify.md, este plan.md, tasks.md).
2. **Backend foundation**:
   - `voz/auth.py` extender (15 min).
   - `voz/intent_router.py` añadir `contexts_permitidos` (15 min).
   - `voz/rest.py` lectura header (10 min).
   - `claudio_tools/trabajo.py` + tests unit ligeros (45 min).
   - `mcp_server.py` registrar 10 tools (20 min).
3. **Vault trabajo** — `_ensure_skeleton()` corre la primera vez que se
   usa cualquier tool. Crear `README.md`, `INDEX.md` stubs, normes stubs
   manualmente vía script (10 min).
4. **Tablero**:
   - `tablero/v2/api_trabajo.py` con handlers (30 min).
   - `tablero/v2/workers/trabajo.py` (20 min).
   - Extender `ws.py` (+1 canal) (5 min).
   - Extender endpoints v2 con `?context=` (10 min, soft filter — no
     romper).
5. **Caddy** — añadir vhost (5 min). NO reload aún (esperar al build).
6. **PWA scaffold**:
   - `tablero/web-claudio/` mkdir.
   - `package.json`, `vite.config.ts`, `tailwind.config.ts`,
     `tsconfig.json`, `postcss.config.js`, `index.html`, `public/`.
   - `npm install` (~3-5 min de descarga).
   - `src/main.tsx`, `App.tsx`, `styles/index.css`.
   - `manifest.json` + `sw.js`.
   - Empty `dist/` build OK.
7. **PWA layers**:
   - `lib/auth.ts`, `lib/api.ts`, `lib/context.ts`, `lib/ws.ts`, `lib/audio.ts`.
   - Home (3 cards) + ContextSwitcher.
   - Casa shell + tabs (skeleton + 1-2 widgets reales).
   - NosVers shell + tabs (skeleton).
   - Trabajo shell + tabs (mayor detalle estético).
   - PTTOverlay + Waveform + NeuralGraph.
8. **Build + deploy**:
   - `npm run build` → `dist/`.
   - Reload Caddy.
   - Smoke con curl + browser test (URL principal).
9. **Tests**:
   - Pytest scope JWT (extiende `tests/test_intent_router.py`).
   - Vitest smoke (3 contextos render OK).
10. **Docs**:
    - `knowledge_base/claudio/PWA_CONTEXTOS.md`.
    - Commits agrupados (~8 conventional).

---

## Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| `npm install` lento o falla sin red | `npm install --prefer-offline` si hay cache; aceptar 5 min |
| Bundle > 2 MB | tree-shake icons (uso explícito), lazy import contexts, gzip |
| `MediaRecorder` Opus no en iOS | feature detect; fallback `audio/mp4`; iOS no es objetivo principal |
| Service Worker actualizaciones bloqueadas | `skipWaiting()`+`clientsClaim()` + bumpear CACHE_NAME por build |
| Tablero v2 broker no levanta canal trabajo si no hay cliente | crear suscriptor de test que confirma canal disponible |
| Anthropic API fuera de presupuesto en tests | tests router monkeypatch requests.post, cero llamadas reales |

---

*Plan NosVers Claudio Fase 7 — 2026-05-14*
