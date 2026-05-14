"""tablero.v2.agente_ejecutar — POST /tablero/api/v2/agente_ejecutar (010).

Endpoint fire-and-forget para los 14 agentes operativos NosVers.
Whitelist en `WHITELIST`. Lanza `subprocess.Popen` sin esperar al proceso
(devuelve PID + started_at en <100ms). stdout/stderr → append a
`/home/nosvers/logs/<nombre>.log` para que el worker `agentes` lo detecte
como `running` por mtime.

Diferencia con `/tablero/api/v2/agentes/ejecutar` (US11):
- US11 es BLOQUEANTE, 4 slugs, espera resultado hasta timeout.
- Este es NO-BLOQUEANTE, 14 nombres, dispara y vuelve.
"""
from __future__ import annotations

import asyncio
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from starlette.requests import Request
from starlette.responses import JSONResponse


WHITELIST: frozenset[str] = frozenset({
    "orchestrator",
    "agt01_visual",
    "agt02_instagram",
    "agt04_seo",
    "agt05_africa",
    "agt06_infoproduct",
    "agt07_diario",
    "agt07_youtube",
    "agt08_facebook",
    "agt00_intelligence",
    "agt_infra",
    "agt_eisenia",
    "agt_analyste",
    "agt_directeur",
})

AGENTS_ROOT = Path("/home/nosvers/agents")
LOGS_ROOT = Path("/home/nosvers/logs")


def _safe_name(name: str) -> bool:
    if not name or len(name) > 64:
        return False
    return all(c.isalnum() or c == "_" for c in name)


async def agente_ejecutar_handler(
    request: Request, autenticador, cors_headers, log_line
) -> JSONResponse:
    t0 = time.perf_counter()
    rid = request.headers.get("x-request-id") or "anon"
    payload = await autenticador(request)
    if not payload:
        log_line(rid, "", "v2/agente_ejecutar", 401, (time.perf_counter() - t0) * 1000)
        return JSONResponse(
            {"ok": False, "error": "auth_invalido"},
            status_code=401, headers=cors_headers(),
        )

    sub = str(payload.get("sub", ""))

    try:
        body = json.loads(await request.body() or b"{}")
    except json.JSONDecodeError:
        return JSONResponse(
            {"ok": False, "error": "json_invalido"},
            status_code=400, headers=cors_headers(),
        )

    nombre = str(body.get("nombre", "")).strip()
    if not _safe_name(nombre):
        return JSONResponse(
            {"ok": False, "error": "nombre_invalido"},
            status_code=400, headers=cors_headers(),
        )
    if nombre not in WHITELIST:
        return JSONResponse({
            "ok": False,
            "error": "not_in_whitelist",
            "detalle": f"nombres válidos: {sorted(WHITELIST)}",
        }, status_code=404, headers=cors_headers())

    script = AGENTS_ROOT / f"{nombre}.py"
    if not script.exists():
        return JSONResponse({
            "ok": False,
            "error": "script_missing",
            "detalle": str(script),
        }, status_code=500, headers=cors_headers())

    LOGS_ROOT.mkdir(parents=True, exist_ok=True)
    log_path = LOGS_ROOT / f"{nombre}.log"

    started_at = datetime.now().isoformat(timespec="seconds")
    # Fire-and-forget. Detached: no esperar al proceso.
    try:
        log_fh = log_path.open("ab")
        log_fh.write(
            f"\n--- run start {started_at} triggered_by={sub} ---\n".encode("utf-8")
        )
        log_fh.flush()
        proc = subprocess.Popen(
            [sys.executable, str(script)],
            stdout=log_fh,
            stderr=subprocess.STDOUT,
            cwd=str(AGENTS_ROOT.parent),
            start_new_session=True,
            close_fds=True,
        )
        # Cerrar el fh en el padre — el subprocess hereda su propio fd ya duplicado
        log_fh.close()
    except Exception as e:  # noqa: BLE001
        log_line(rid, sub, "v2/agente_ejecutar", 500, (time.perf_counter() - t0) * 1000,
                 f"nombre={nombre} spawn_error={e!r}")
        return JSONResponse({
            "ok": False,
            "error": "spawn_error",
            "detalle": f"{type(e).__name__}: {e}",
        }, status_code=500, headers=cors_headers())

    # Touch log file so worker `agentes` ve mtime fresca incluso si el subprocess
    # tarda un par de segundos en escribir.
    try:
        log_path.touch()
    except OSError:
        pass

    # No bloqueamos: damos al evento loop un tick para que cualquier output
    # inicial se vea reflejado, pero sin esperar al proceso.
    await asyncio.sleep(0)

    log_line(rid, sub, "v2/agente_ejecutar", 200, (time.perf_counter() - t0) * 1000,
             f"nombre={nombre} pid={proc.pid}")
    return JSONResponse({
        "ok": True,
        "nombre": nombre,
        "pid": proc.pid,
        "started_at": started_at,
        "triggered_by": sub,
        "log": str(log_path),
    }, status_code=200, headers=cors_headers())
