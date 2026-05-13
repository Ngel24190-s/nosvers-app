"""tablero.v2.editar — PATCH /tablero/api/v2/nota (US2).

Edita el cuerpo de una entrada (fecha, ts) preservando todo el frontmatter
inline. Concurrencia optimista por If-Match contra `concurrency_token`
(modified_at si existe, sino ts inmutable).

Body: {"path": "dia/<fecha>.md#<ts>", "cuerpo": "..."} ; opcionalmente
{"etiqueta": "...", "titulo": "..."}.

Header: If-Match: <concurrency_token>.
"""
from __future__ import annotations

import json
import sys
import time
from datetime import date, datetime

sys.path.insert(0, "/home/nosvers")

from starlette.requests import Request
from starlette.responses import JSONResponse

from voz.vault_io import ETIQUETAS_VALIDAS, VAULT_BASE  # noqa: E402

from tablero.log import get_logger  # noqa: E402
from tablero.v2.dia_io import (  # noqa: E402
    buscar_entrada,
    escribir_dia,
    leer_dia,
)
from tablero.v2.frontmatter import now_modified_at  # noqa: E402
from tablero.v2.wiki_index import get_index  # noqa: E402


log = get_logger("tablero.v2.editar")


def _parse_path(path: str) -> tuple[date, str] | None:
    """Convierte 'dia/2026-05-13.md#<ts>' → (date, ts)."""
    if "#" not in path:
        return None
    archivo, ts = path.split("#", 1)
    archivo = archivo.strip()
    ts = ts.strip()
    if not archivo.startswith("dia/") or not archivo.endswith(".md"):
        return None
    fecha_str = archivo[len("dia/"):-len(".md")]
    try:
        fecha = date.fromisoformat(fecha_str)
    except ValueError:
        return None
    return fecha, ts


async def editar_handler(request: Request, autenticador, cors_headers, log_line) -> JSONResponse:
    t0 = time.perf_counter()
    rid = request.headers.get("x-request-id") or "anon"
    payload = await autenticador(request)
    if not payload:
        log_line(rid, "", "v2/editar", 401, (time.perf_counter() - t0) * 1000)
        return JSONResponse({"ok": False, "error": "auth_invalido"}, status_code=401, headers=cors_headers())

    sub = str(payload.get("sub", ""))

    if_match = request.headers.get("If-Match", "").strip()
    if not if_match:
        return JSONResponse({"ok": False, "error": "missing_if_match"}, status_code=428, headers=cors_headers())

    try:
        body = json.loads(await request.body() or b"{}")
    except json.JSONDecodeError:
        return JSONResponse({"ok": False, "error": "json_invalido"}, status_code=400, headers=cors_headers())

    path = (body.get("path") or "").strip()
    if not path:
        return JSONResponse({"ok": False, "error": "path_requerido"}, status_code=400, headers=cors_headers())

    parsed = _parse_path(path)
    if parsed is None:
        return JSONResponse({"ok": False, "error": "path_invalido", "detalle": "esperaba dia/YYYY-MM-DD.md#<ts>"}, status_code=400, headers=cors_headers())
    fecha, ts = parsed

    nuevo_cuerpo = body.get("cuerpo")
    nueva_etiqueta = body.get("etiqueta")
    nuevo_titulo = body.get("titulo")
    if nuevo_cuerpo is None and nueva_etiqueta is None and nuevo_titulo is None:
        return JSONResponse({"ok": False, "error": "sin_cambios"}, status_code=400, headers=cors_headers())

    # Leer día completo
    entradas = leer_dia(VAULT_BASE, fecha)
    if not entradas:
        return JSONResponse({"ok": False, "error": "not_found", "detalle": "día sin entradas"}, status_code=404, headers=cors_headers())

    target = buscar_entrada(entradas, ts)
    if target is None:
        return JSONResponse({"ok": False, "error": "not_found", "detalle": "entrada no encontrada"}, status_code=404, headers=cors_headers())

    # Concurrencia optimista
    actual = target.concurrency_token
    if if_match != actual:
        return JSONResponse({
            "ok": False,
            "error": "stale_modified_at",
            "current_modified_at": actual,
        }, status_code=409, headers=cors_headers())

    # Aplicar cambios
    cambio = False
    if nuevo_cuerpo is not None:
        nuevo_cuerpo_str = str(nuevo_cuerpo).strip()
        if not nuevo_cuerpo_str:
            return JSONResponse({"ok": False, "error": "cuerpo_vacio"}, status_code=400, headers=cors_headers())
        # Si hay titulo, lo prependemos como heading
        if nuevo_titulo:
            target.texto = f"## {nuevo_titulo.strip()}\n\n{nuevo_cuerpo_str}"
        else:
            target.texto = nuevo_cuerpo_str
        cambio = True

    if nueva_etiqueta is not None:
        if nueva_etiqueta not in ETIQUETAS_VALIDAS:
            return JSONResponse({"ok": False, "error": "etiqueta_invalida"}, status_code=400, headers=cors_headers())
        target.meta["etiqueta"] = nueva_etiqueta
        cambio = True

    if cambio:
        target.meta["modified_at"] = now_modified_at()
        # Logging editor_sub para trazabilidad (US2 acceptance #5)
        if target.autor != sub:
            log.info(f"rid={rid} cross-author edit: autor={target.autor} editor_sub={sub} ts={ts}")
            target.meta["last_editor_sub"] = sub

    # Reescribir día atómicamente
    try:
        archivo = escribir_dia(VAULT_BASE, fecha, entradas)
    except Exception as e:  # noqa: BLE001
        log.exception(f"rid={rid} v2/editar 500: {e}")
        return JSONResponse({"ok": False, "error": "vault_write_failed", "detalle": str(e)}, status_code=500, headers=cors_headers())

    # Actualizar wiki_index (D-004)
    try:
        contenido = archivo.read_text(encoding="utf-8")
        get_index().actualizar_nota(archivo, contenido)
    except Exception:
        log.exception("rid=%s wiki_index update falló (no fatal)", rid)

    nuevo_token = target.concurrency_token
    response = {
        "ok": True,
        "path": path,
        "fecha": fecha.isoformat(),
        "ts": ts,
        "autor": target.autor,
        "etiqueta": target.etiqueta,
        "concurrency_token": nuevo_token,
        "modified_at": target.modified_at,
    }
    log_line(rid, sub, "v2/editar", 200, (time.perf_counter() - t0) * 1000, f"ts={ts}")
    return JSONResponse(response, status_code=200, headers=cors_headers())
