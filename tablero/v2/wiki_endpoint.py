"""tablero.v2.wiki_endpoint — GET /tablero/api/v2/wiki-index (US7).

Expone el dict {target_slug: [BacklinkEntry, ...]} construido en startup
por tablero.v2.wiki_index. Soporta filtro por ?target=<slug>.
"""
from __future__ import annotations

import time
from dataclasses import asdict

from starlette.requests import Request
from starlette.responses import JSONResponse

from tablero.log import get_logger
from tablero.v2.wiki_index import get_index

log = get_logger("tablero.v2.wiki_endpoint")


async def wiki_index_handler(request: Request, autenticador, cors_headers, log_line) -> JSONResponse:
    t0 = time.perf_counter()
    rid = request.headers.get("x-request-id") or "anon"
    payload = await autenticador(request)
    if not payload:
        log_line(rid, "", "v2/wiki-index", 401, (time.perf_counter() - t0) * 1000)
        return JSONResponse({"ok": False, "error": "auth_invalido"}, status_code=401, headers=cors_headers())

    sub = str(payload.get("sub", ""))

    target = request.query_params.get("target", "").strip()
    idx = get_index()

    if target:
        backlinks = [asdict(b) for b in idx.backlinks_de(target)]
        body = {
            "ok": True,
            "target": target,
            "backlinks": backlinks,
            "generated_at": idx.generated_at,
        }
    else:
        completo = {
            t: [asdict(b) for b in bucket]
            for t, bucket in idx.indice_completo().items()
        }
        body = {
            "ok": True,
            "index": completo,
            "generated_at": idx.generated_at,
        }

    log_line(rid, sub, "v2/wiki-index", 200, (time.perf_counter() - t0) * 1000,
             f"target={target!r}" if target else "full")
    return JSONResponse(body, headers=cors_headers())
