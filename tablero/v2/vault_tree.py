"""tablero.v2.vault_tree — GET /tablero/api/v2/vault/tree (US8).

Listado lazy de hijos directos de una carpeta del vault. Path safety
estricto: nunca permite escapar de VAULT_BASE (Constitución X).
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, "/home/nosvers")

from starlette.requests import Request
from starlette.responses import JSONResponse

from voz.vault_io import VAULT_BASE  # noqa: E402

from tablero.log import get_logger  # noqa: E402

log = get_logger("tablero.v2.vault_tree")


def _resolver_seguro(rel: str) -> Path | None:
    """Resuelve rel relativo a VAULT_BASE rechazando traversal."""
    base = VAULT_BASE.resolve()
    if not rel:
        return base
    candidato = (base / rel).resolve()
    try:
        candidato.relative_to(base)
    except ValueError:
        return None
    return candidato


async def vault_tree_handler(request: Request, autenticador, cors_headers, log_line) -> JSONResponse:
    t0 = time.perf_counter()
    rid = request.headers.get("x-request-id") or "anon"
    payload = await autenticador(request)
    if not payload:
        log_line(rid, "", "v2/vault/tree", 401, (time.perf_counter() - t0) * 1000)
        return JSONResponse({"ok": False, "error": "auth_invalido"}, status_code=401, headers=cors_headers())

    sub = str(payload.get("sub", ""))
    rel = request.query_params.get("path", "").strip().strip("/")

    resolvido = _resolver_seguro(rel)
    if resolvido is None:
        return JSONResponse({"ok": False, "error": "path_unsafe"}, status_code=400, headers=cors_headers())
    if not resolvido.exists() or not resolvido.is_dir():
        return JSONResponse({"ok": False, "error": "not_found"}, status_code=404, headers=cors_headers())

    children = []
    try:
        for child in sorted(resolvido.iterdir(), key=lambda p: (p.is_file(), p.name.lower())):
            if child.name.startswith("."):
                continue
            entry: dict = {
                "name": child.name,
                "type": "folder" if child.is_dir() else "file",
            }
            if child.is_file():
                try:
                    st = child.stat()
                    entry["size"] = st.st_size
                    from datetime import datetime, timezone
                    entry["modified_at"] = datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat(timespec="seconds")
                except OSError:
                    pass
            children.append(entry)
    except OSError as e:
        return JSONResponse({"ok": False, "error": "read_failed", "detalle": str(e)}, status_code=500, headers=cors_headers())

    log_line(rid, sub, "v2/vault/tree", 200, (time.perf_counter() - t0) * 1000, f"n={len(children)}")
    return JSONResponse({"ok": True, "path": rel, "children": children}, headers=cors_headers())
