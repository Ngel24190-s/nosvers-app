"""tablero.v2.capturar — POST /tablero/api/v2/capturar (US1).

Wrapper fino sobre `voz.capturar.dia_capturar_impl` (D-001 import in-process).
Infers `autor` del JWT sub. Tras la escritura exitosa, actualiza el wiki_index.
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime

sys.path.insert(0, "/home/nosvers")

from starlette.requests import Request
from starlette.responses import JSONResponse

from voz.capturar import dia_capturar_impl  # noqa: E402  D-001 in-process MCP call
from voz.vault_io import ETIQUETAS_VALIDAS, VAULT_BASE  # noqa: E402

from tablero.log import get_logger  # noqa: E402
from tablero.v2.wiki_index import get_index  # noqa: E402


log = get_logger("tablero.v2.capturar")

MAX_BODY_BYTES = 1 * 1024 * 1024  # 1 MB (FR / edge case spec)


async def capturar_handler(request: Request, autenticador, cors_headers, log_line) -> JSONResponse:
    """Handler reusable. Pasamos autenticador, cors_headers, log_line desde rest.py
    para no duplicar utilities."""
    t0 = time.perf_counter()
    rid = request.headers.get("x-request-id") or "anon"
    payload = await autenticador(request)
    if not payload:
        log_line(rid, "", "v2/capturar", 401, (time.perf_counter() - t0) * 1000)
        return JSONResponse({"ok": False, "error": "auth_invalido"}, status_code=401, headers=cors_headers())

    sub = str(payload.get("sub", ""))

    try:
        body_bytes = await request.body()
    except Exception:
        return JSONResponse({"ok": False, "error": "body_unreadable"}, status_code=400, headers=cors_headers())
    if len(body_bytes) > MAX_BODY_BYTES:
        log_line(rid, sub, "v2/capturar", 400, (time.perf_counter() - t0) * 1000, "body_too_large")
        return JSONResponse({"ok": False, "error": "body_too_large", "max_bytes": MAX_BODY_BYTES}, status_code=400, headers=cors_headers())

    try:
        body = json.loads(body_bytes or b"{}")
    except json.JSONDecodeError:
        return JSONResponse({"ok": False, "error": "json_invalido"}, status_code=400, headers=cors_headers())

    titulo = (body.get("titulo") or "").strip()
    cuerpo = (body.get("cuerpo") or "").strip()
    etiquetas = body.get("etiquetas") or []

    if not cuerpo:
        return JSONResponse({"ok": False, "error": "input_vacio", "detalle": "cuerpo requerido"}, status_code=400, headers=cors_headers())
    if len(cuerpo.encode("utf-8")) > MAX_BODY_BYTES:
        return JSONResponse({"ok": False, "error": "body_too_large"}, status_code=400, headers=cors_headers())

    # Validar etiquetas (subset de ETIQUETAS_VALIDAS)
    if not isinstance(etiquetas, list):
        return JSONResponse({"ok": False, "error": "etiquetas_invalido"}, status_code=400, headers=cors_headers())
    etiquetas_validas = [e for e in etiquetas if isinstance(e, str) and e in ETIQUETAS_VALIDAS]
    if etiquetas and not etiquetas_validas:
        return JSONResponse({"ok": False, "error": "etiqueta_invalida", "detalle": f"validas: {sorted(ETIQUETAS_VALIDAS)}"}, status_code=400, headers=cors_headers())

    etiqueta_principal = etiquetas_validas[0] if etiquetas_validas else "auto"

    texto_completo = cuerpo
    if titulo:
        # Prepende título como heading H2 al cuerpo (no campo aparte; convención simple)
        texto_completo = f"## {titulo}\n\n{cuerpo}"

    try:
        resultado = dia_capturar_impl(
            texto=texto_completo,
            etiqueta=etiqueta_principal,
            origen="otro",
            autor=sub,
            device_label=f"tablero-{sub}",
            client_uuid="",  # idempotencia desactivada para captura por dashboard
        )
    except Exception as e:  # noqa: BLE001
        log.exception(f"rid={rid} v2/capturar 500: {e}")
        return JSONResponse({"ok": False, "error": "interno", "detalle": str(e)}, status_code=500, headers=cors_headers())

    if not resultado.get("ok"):
        status = 400 if resultado.get("error") in {"input_vacio", "parametro_invalido"} else 500
        log_line(rid, sub, "v2/capturar", status, (time.perf_counter() - t0) * 1000, str(resultado))
        return JSONResponse(resultado, status_code=status, headers=cors_headers())

    # Actualizar wiki_index (D-004 write-through)
    try:
        ts_str = resultado["ts"]
        fecha_iso = datetime.fromisoformat(ts_str).date().isoformat()
        archivo_dia = VAULT_BASE / "dia" / f"{fecha_iso}.md"
        if archivo_dia.exists():
            contenido = archivo_dia.read_text(encoding="utf-8")
            get_index().actualizar_nota(archivo_dia, contenido)
    except Exception:
        log.exception("rid=%s wiki_index update falló (no fatal)", rid)

    # Path canónico de la entrada (fecha#ts)
    ts_str = resultado["ts"]
    fecha_iso = datetime.fromisoformat(ts_str).date().isoformat()
    response = {
        "ok": True,
        "path": f"dia/{fecha_iso}.md#{ts_str}",
        "fecha": fecha_iso,
        "ts": ts_str,
        "autor": resultado["autor"],
        "etiqueta": resultado["etiqueta_aplicada"],
        "concurrency_token": ts_str,  # primera captura: token = ts
    }
    log_line(rid, sub, "v2/capturar", 201, (time.perf_counter() - t0) * 1000, f"ts={ts_str}")
    return JSONResponse(response, status_code=201, headers=cors_headers())
