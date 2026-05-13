"""
voz.rest — Endpoints REST sobre el binario MCP para servir a la PWA.

Comparte el proceso del MCP server. Se monta sobre FastMCP usando su
servidor HTTP subyacente (Starlette). Auth Bearer vía voz.auth.
"""
from __future__ import annotations

import json
import logging
from typing import Any

from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

from .auth import validar_token
from .capturar import dia_capturar_impl
from .contexto import dia_contexto_impl
from .buscar import dia_buscar_impl

log = logging.getLogger("voz.rest")

ALLOWED_ORIGIN = "https://voz.nosvers.com"
MAX_AUDIO_BYTES = 5 * 1024 * 1024  # 5 MB


def _cors_headers() -> dict:
    return {
        "Access-Control-Allow-Origin": ALLOWED_ORIGIN,
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Authorization, Content-Type, X-Request-Id",
        "Access-Control-Max-Age": "86400",
    }


def _json(data: dict, status: int = 200) -> JSONResponse:
    return JSONResponse(data, status_code=status, headers=_cors_headers())


async def _autenticar(request: Request) -> dict | None:
    auth = request.headers.get("authorization", "")
    if not auth.lower().startswith("bearer "):
        return None
    token = auth[7:].strip()
    return validar_token(token)


async def options_handler(request: Request) -> Response:
    return Response(status_code=204, headers=_cors_headers())


async def capturar_handler(request: Request) -> JSONResponse:
    payload = await _autenticar(request)
    if not payload:
        return _json({"ok": False, "error": "auth_invalido"}, 401)
    device = payload.get("device", "desconocido")
    # autor (BRIEF §14) viene del JWT `sub`; fallback a "angel" si no presente
    autor_jwt = payload.get("sub") or payload.get("autor") or "angel"

    ctype = request.headers.get("content-type", "").lower()
    kwargs: dict[str, Any] = {"device_label": device, "autor": autor_jwt}

    if "multipart/form-data" in ctype:
        form = await request.form()
        meta_raw = form.get("meta", "")
        if hasattr(meta_raw, "read"):  # FileLike
            meta_raw = (await meta_raw.read()).decode("utf-8")
        try:
            meta = json.loads(meta_raw) if meta_raw else {}
        except json.JSONDecodeError:
            return _json({"ok": False, "error": "parametro_invalido", "detalle": "meta no es JSON"}, 400)
        audio_field = form.get("audio")
        if audio_field is None:
            return _json({"ok": False, "error": "input_vacio"}, 400)
        audio_bytes = await audio_field.read()
        if len(audio_bytes) > MAX_AUDIO_BYTES:
            return _json({"ok": False, "error": "payload_too_large"}, 413)
        kwargs.update({
            "audio_bytes": audio_bytes,
            "texto": meta.get("texto", ""),
            "ts_iso": meta.get("ts_iso", ""),
            "etiqueta": meta.get("etiqueta", "auto"),
            "origen": meta.get("origen", "voz_movil"),
            "client_uuid": meta.get("client_uuid", ""),
        })
        # autor del meta sólo si el JWT lo permite (mismo autor o override autorizado)
        if meta.get("autor") and meta.get("autor") == autor_jwt:
            kwargs["autor"] = meta["autor"]
    elif "application/json" in ctype:
        try:
            data = await request.json()
        except json.JSONDecodeError:
            return _json({"ok": False, "error": "parametro_invalido", "detalle": "body no JSON"}, 400)
        kwargs.update({
            "texto": data.get("texto", ""),
            "audio_b64": data.get("audio_b64", ""),
            "ts_iso": data.get("ts_iso", ""),
            "etiqueta": data.get("etiqueta", "auto"),
            "origen": data.get("origen", "otro"),
            "client_uuid": data.get("client_uuid", ""),
        })
        if data.get("autor") and data.get("autor") == autor_jwt:
            kwargs["autor"] = data["autor"]
    else:
        return _json({"ok": False, "error": "unsupported_media_type"}, 415)

    result = dia_capturar_impl(**kwargs)
    status = 200 if result.get("ok") else 400
    return _json(result, status)


async def contexto_handler(request: Request) -> JSONResponse:
    payload = await _autenticar(request)
    if not payload:
        return _json({"ok": False, "error": "auth_invalido"}, 401)
    qp = request.query_params
    result = dia_contexto_impl(
        rango_dias=int(qp.get("dias", 7)),
        incluir_calendario=qp.get("calendario", "1") in ("1", "true", "yes"),
        incluir_estado_agentes=qp.get("agentes", "1") in ("1", "true", "yes"),
        etiquetas_filtro=qp.get("etiquetas", ""),
        autor=qp.get("autor", ""),
    )
    return _json(result)


async def buscar_handler(request: Request) -> JSONResponse:
    payload = await _autenticar(request)
    if not payload:
        return _json({"ok": False, "error": "auth_invalido"}, 401)
    qp = request.query_params
    result = dia_buscar_impl(
        query=qp.get("q", ""),
        desde=qp.get("desde", ""),
        hasta=qp.get("hasta", ""),
        limite=int(qp.get("limite", 20)),
        etiqueta=qp.get("etiqueta", ""),
        autor=qp.get("autor", ""),
    )
    status = 200 if result.get("ok") else 400
    return _json(result, status)


async def health_handler(request: Request) -> JSONResponse:
    return _json({"ok": True, "service": "voz", "version": "1.0.0"})


ROUTES = [
    Route("/voz/api/capturar", capturar_handler, methods=["POST"]),
    Route("/voz/api/capturar", options_handler, methods=["OPTIONS"]),
    Route("/voz/api/contexto", contexto_handler, methods=["GET"]),
    Route("/voz/api/contexto", options_handler, methods=["OPTIONS"]),
    Route("/voz/api/buscar", buscar_handler, methods=["GET"]),
    Route("/voz/api/buscar", options_handler, methods=["OPTIONS"]),
    Route("/voz/api/health", health_handler, methods=["GET"]),
]


def montar_en_fastmcp(mcp_app) -> None:
    """Monta las rutas REST en el HTTP app de FastMCP.

    FastMCP 3.x expone su Starlette app vía .http_app() o atributo similar.
    Esta función es defensiva: si la API cambia entre versiones, loguea
    un warning pero no rompe el arranque.
    """
    try:
        # FastMCP 3.x — http_app es una propiedad/método
        candidates = [
            getattr(mcp_app, "http_app", None),
            getattr(mcp_app, "_http_app", None),
            getattr(mcp_app, "app", None),
        ]
        app = None
        for c in candidates:
            if c is None:
                continue
            app = c() if callable(c) else c
            if app and hasattr(app, "router"):
                break
        if app is None or not hasattr(app, "router"):
            log.warning("No pude localizar app HTTP de FastMCP — REST no montado")
            return
        for r in ROUTES:
            app.router.routes.append(r)
        log.info(f"REST montado: {len(ROUTES)} rutas bajo /voz/api/")
    except Exception as e:
        log.exception(f"Error montando REST: {e}")
