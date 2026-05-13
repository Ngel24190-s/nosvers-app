"""tablero.v2.agentes — POST /tablero/api/v2/agentes/ejecutar (US11).

Invoca un agente del catálogo whitelist por subprocess. Timeout
configurable (default 60s). Si excede el timeout, devuelve 504
"timeout" sin colgar la conexión.

D-001 in-process MCP: en lugar de llamar al MCP server externo,
ejecutamos el script Python del agente directamente. Esto evita
race conditions y el bug conocido de telegram_enviar stall.
"""
from __future__ import annotations

import asyncio
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, "/home/nosvers")

from starlette.requests import Request
from starlette.responses import JSONResponse

from tablero.log import get_logger

log = get_logger("tablero.v2.agentes")


# Catálogo whitelist público (FR-032)
CATALOGO = {
    "agt05_africa": {"label": "Procesar emails de África", "timeout_s": 60, "script": "agt05_africa.py"},
    "agt07_diario": {"label": "Briefing diario", "timeout_s": 90, "script": "agt07_diario.py"},
    "agt_eisenia": {"label": "Auditoría composteur", "timeout_s": 60, "script": "agt_eisenia.py"},
    "orchestrator": {"label": "Pulse cron status", "timeout_s": 30, "script": "orchestrator.py"},
}

AGENTS_ROOT = Path("/home/nosvers/agents")


async def _ejecutar_subprocess(script_path: Path, timeout_s: float) -> tuple[bool, str, float]:
    """Lanza el script en subprocess Python, captura stdout y stderr.
    Devuelve (timed_out_flag_inverso, output, duration_s)."""
    t0 = time.perf_counter()
    proc = await asyncio.create_subprocess_exec(
        sys.executable, str(script_path),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        cwd=str(AGENTS_ROOT.parent),
    )
    try:
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout_s)
    except asyncio.TimeoutError:
        try:
            proc.kill()
            await proc.wait()
        except Exception:
            pass
        return False, "[MCP_STALL_AGENTE] timeout excedido", time.perf_counter() - t0
    return True, stdout.decode("utf-8", errors="replace"), time.perf_counter() - t0


async def agentes_handler(request: Request, autenticador, cors_headers, log_line) -> JSONResponse:
    t0 = time.perf_counter()
    rid = request.headers.get("x-request-id") or "anon"
    payload = await autenticador(request)
    if not payload:
        log_line(rid, "", "v2/agentes", 401, (time.perf_counter() - t0) * 1000)
        return JSONResponse({"ok": False, "error": "auth_invalido"}, status_code=401, headers=cors_headers())

    sub = str(payload.get("sub", ""))

    try:
        body = json.loads(await request.body() or b"{}")
    except json.JSONDecodeError:
        return JSONResponse({"ok": False, "error": "json_invalido"}, status_code=400, headers=cors_headers())

    slug = str(body.get("slug", "")).strip()
    if slug not in CATALOGO:
        return JSONResponse({
            "ok": False,
            "error": "not_in_catalog",
            "detalle": f"slugs válidos: {sorted(CATALOGO.keys())}",
        }, status_code=404, headers=cors_headers())

    config = CATALOGO[slug]
    script = AGENTS_ROOT / config["script"]
    if not script.exists():
        return JSONResponse({"ok": False, "error": "script_missing", "detalle": str(script)}, status_code=500, headers=cors_headers())

    timeout_s = float(body.get("timeout_s", config["timeout_s"]))

    log.info(f"rid={rid} v2/agentes ejecutar slug={slug} triggered_by={sub} timeout={timeout_s}s")
    ok, output, duration = await _ejecutar_subprocess(script, timeout_s)

    if not ok:
        log_line(rid, sub, "v2/agentes", 504, (time.perf_counter() - t0) * 1000, f"slug={slug} MCP_STALL")
        return JSONResponse({
            "ok": False,
            "error": "agente_stall",
            "slug": slug,
            "output": output,
            "duration_s": round(duration, 2),
            "triggered_by": sub,
        }, status_code=504, headers=cors_headers())

    log_line(rid, sub, "v2/agentes", 200, (time.perf_counter() - t0) * 1000, f"slug={slug} dur={duration:.1f}s")
    return JSONResponse({
        "ok": True,
        "slug": slug,
        "output": output,
        "duration_s": round(duration, 2),
        "triggered_by": sub,
    }, status_code=200, headers=cors_headers())


async def catalogo_handler(request: Request, autenticador, cors_headers, log_line) -> JSONResponse:
    """GET /tablero/api/v2/agentes/catalogo — devuelve la lista pública."""
    t0 = time.perf_counter()
    rid = request.headers.get("x-request-id") or "anon"
    payload = await autenticador(request)
    if not payload:
        log_line(rid, "", "v2/agentes/catalogo", 401, (time.perf_counter() - t0) * 1000)
        return JSONResponse({"ok": False, "error": "auth_invalido"}, status_code=401, headers=cors_headers())

    sub = str(payload.get("sub", ""))
    items = [
        {"slug": slug, "label": cfg["label"], "timeout_s": cfg["timeout_s"]}
        for slug, cfg in CATALOGO.items()
    ]
    log_line(rid, sub, "v2/agentes/catalogo", 200, (time.perf_counter() - t0) * 1000)
    return JSONResponse({"ok": True, "agentes": items}, headers=cors_headers())
