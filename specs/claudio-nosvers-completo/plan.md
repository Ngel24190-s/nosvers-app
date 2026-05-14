# Plan — Claudio PWA NosVers Completo (010)

> /speckit-plan · 2026-05-14

## Estrategia

Ataque en 5 fases secuenciales. Backend primero (workers + canales + endpoint), después tipos TS, después widgets/tabs, build, deploy. Sin breaking change para Casa/Trabajo/PTT porque sólo:
- Añadimos archivos en `tablero/v2/workers/` y los registramos.
- Añadimos rutas en `tablero/rest.py` (sin mutar las existentes).
- Añadimos canales a `VALID_CHANNELS`.
- Reemplazamos contenido interior del directorio `tablero/web-claudio/src/components/nosvers/tabs/`.
- Reescribimos `NosVersShell.tsx` (sigue exportando el mismo componente).

## Fase 0 — Inventario (durante /specify)

- Workers existentes a reusar: `huerto_estado`, `pedidos_stripe`, `agentes`, `aegis`, `health`, `revenue`, `recordatorios`, `clima_neuvic`.
- Endpoint REST existente bloqueante: `/tablero/api/v2/agentes/ejecutar` (4 slugs, sigue ahí).
- Patrón ws.py: añadir canal a `VALID_CHANNELS`; ningún scope nuevo.
- Bug telegram: ningún worker hace `telegram_enviar`.
- 14 agentes BRIEF: incluyen `agt07_diario` y `agt00_intelligence` que pueden no existir como `.py`; el endpoint debe gestionar gracefully (`script_missing` 500) y el widget mostrar estado `missing`.

## Fase 1 — Backend workers (13 archivos nuevos)

Patrón estándar (basado en `huerto_estado.py`):

```python
"""Worker <name>: lee <fuente> o publica mock realista."""
from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from claudio_tools.common import vault   # o parse_frontmatter si aplica

log = logging.getLogger("tablero.v2.workers.<name>")


def _mock() -> dict:
    return { ... }


async def <name>_tick() -> dict | None:
    try:
        # 1. intentar leer vault
        # 2. si no existe o falla, return _mock()
        ...
    except Exception as e:
        log.debug(f"<name>: {e}")
        return _mock()
```

Cada worker debe tener `ts: datetime.now().isoformat(timespec="seconds")` en el snapshot para que el broker detecte cambios.

Intervalos según naturaleza del dato (definidos en spec §4).

Después de crear los archivos, editar `tablero/v2/workers/__init__.py`:
- Importar `<name>_tick` arriba.
- Registrar `register_worker(Worker(name="<canal>", interval_s=N, tick=<name>_tick))` en `register_all()`.

## Fase 2 — Canales en ws.py

Editar `tablero/v2/ws.py` línea 38-49 (`VALID_CHANNELS`): añadir los 13 nuevos canales en bloque etiquetado `# 010 — NosVers completo`.

Ningún scope JWT — el contexto NosVers es base.

## Fase 3 — Endpoint POST /tablero/api/v2/agente_ejecutar

Crear `tablero/v2/agente_ejecutar.py` (nuevo módulo). Implementa:

```python
WHITELIST = {
    "orchestrator", "agt01_visual", "agt02_instagram", "agt04_seo",
    "agt05_africa", "agt06_infoproduct", "agt07_diario", "agt07_youtube",
    "agt08_facebook", "agt00_intelligence", "agt_infra", "agt_eisenia",
    "agt_analyste", "agt_directeur",
}

AGENTS_ROOT = Path("/home/nosvers/agents")
LOGS_ROOT = Path("/home/nosvers/logs")

async def agente_ejecutar_handler(request, autenticador, cors_headers, log_line):
    # auth → parse body → check whitelist → check script exists → spawn → return
    # subprocess.Popen no-bloqueante, stdout/stderr → append a logs/<nombre>.log
```

Registrar la ruta en `tablero/rest.py` cerca de los demás `/tablero/api/v2/agentes/*`.

## Fase 4 — Frontend (tipos + widgets + tabs)

### 4.1 Tipos

Extender `src/lib/api-types.ts` con las 13 interfaces nuevas listadas en spec §6.

### 4.2 Componentes nuevos

```
src/components/nosvers/widgets/
  ├── BotonEnlaceExterno.tsx
  └── WidgetAgenteCard.tsx
```

`BotonEnlaceExterno`: anchor con `target="_blank" rel="noopener noreferrer"`, icono `ExternalLink`, estilo Card.

`WidgetAgenteCard`: recibe `{nombre, estado, last_run_ts, last_status, onRun}`. Muestra emoji-avatar (mapeo nombre→emoji), label legible, badge color por estado, fecha relativa última run, botón ▶ que llama `agente_ejecutar`. Estado del request: idle/running/done/error mostrado durante 3s.

### 4.3 Tabs

Crear `tabs/Hoy.tsx`, `Granja.tsx`, `Web.tsx`, `Mails.tsx`, `Agentes.tsx`. Cada uno con widgets in-file (siguiendo patrón HoyGranja.tsx).

Borrar `tabs/HoyGranja.tsx`, `Huerto.tsx`, `Tienda.tsx`, `AAPPMA.tsx`, `CockpitMini.tsx`.

### 4.4 Shell

Reescribir `NosVersShell.tsx`:

```tsx
const TABS: Tab[] = [
  { id: 'hoy',      label: 'Hoy',      Icon: Sunrise },
  { id: 'granja',   label: 'Granja',   Icon: Sprout },
  { id: 'web',      label: 'Web',      Icon: Globe },
  { id: 'mails',    label: 'Mails',    Icon: Mail },
  { id: 'agentes',  label: 'Agentes',  Icon: Bot },
];
```

Switch que importa los 5 componentes nuevos.

## Fase 5 — Build, smoke, restart, commit

1. `cd /home/nosvers/tablero/web-claudio && npm run build`.
2. Verificar tamaño del bundle JS (grep `dist/assets/index-*.js` + `gzip -c | wc -c`).
3. Smoke local: `curl -s http://localhost:8766/tablero/api/health`.
4. Restart `dev_server.py` (mata pid actual, relanza con el mismo env).
5. `curl -sI https://claudio.72.61.160.108.nip.io | head -3` espera 200.
6. `git add -A`, `git commit`, `git push origin main`.

## Riesgos & mitigaciones

| Riesgo | Mitigación |
|--------|------------|
| Workers nuevos que esperen vault inexistente | Cada worker tiene `_mock()` y try/except → siempre publica |
| Botón ▶ ejecuta script que tarda 5min y bloquea endpoint | `subprocess.Popen` fire-and-forget; endpoint retorna en <100ms |
| Bundle > 250 KB | Tabs son code-light (mayormente JSX simple); si crece, lazy-load tabs con `lazy()` |
| Agentes whitelist incluye scripts que no existen | Endpoint devuelve 500 `script_missing` + worker `agentes` marca `missing` |
| Restart dev_server bloquea PTT en curso | Restart es instant (≈3s) y la PWA reconecta WS automáticamente |
| `agt07_diario` no existe → widget muestra error | Estado `missing` está manejado; UX: badge gris "no instalado" |

## Estimación

- Fase 1: 1.5h (13 workers cortos, mucho boilerplate idéntico)
- Fase 2: 5min
- Fase 3: 30min
- Fase 4: 2.5h (5 tabs + 2 componentes + tipos)
- Fase 5: 30min (build + restart + commit)

**Total: 5–6h** consistente con BRIEF.
