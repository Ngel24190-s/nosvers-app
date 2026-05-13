"""
tablero.rest — Starlette REST routes for the Second Brain Dashboard.

Mounted on the same uvicorn process as `voz.rest` (see `mcp_server.py`). All routes
are GET (Constitution VI / FR-014: read-only Fase A). JWT validation reuses voz.auth.

Routes (all under /tablero/api/):
  GET  /health           — liveness (no auth)
  GET  /whoami           — decode current JWT
  GET  /timeline         — list notes (default last 30d, both authors)
  GET  /buscar           — full-text search proxy over voz.buscar.dia_buscar_impl
  GET  /nota             — single note detail (markdown body + frontmatter)
  OPTIONS *              — CORS preflight
"""
from __future__ import annotations

import os
import sys
import time
import uuid
from datetime import date
from typing import Optional

from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route, WebSocketRoute

sys.path.insert(0, "/home/nosvers")

from voz.auth import validar_token  # noqa: E402
from voz.buscar import dia_buscar_impl  # noqa: E402
from voz.vault_io import AUTORES_VALIDOS, ETIQUETAS_VALIDAS  # noqa: E402

from tablero.log import alert_critical, get_logger  # noqa: E402
from tablero.nota import NotaNotFound, PathUnsafe, leer_nota  # noqa: E402
from tablero.timeline import listar_timeline  # noqa: E402

# Fase B+C handlers (v2 prefix, D-014)
from tablero.v2.capturar import capturar_handler as _v2_capturar  # noqa: E402
from tablero.v2.editar import editar_handler as _v2_editar  # noqa: E402
from tablero.v2.archivar import (  # noqa: E402
    archivar_handler as _v2_archivar,
    restaurar_handler as _v2_restaurar,
)
from tablero.v2.proyectos import (  # noqa: E402
    actualizar_handler as _v2_proyectos_patch,
    listar_handler as _v2_proyectos_list,
)
from tablero.v2.vault_tree import vault_tree_handler as _v2_vault_tree  # noqa: E402
from tablero.v2.wiki_endpoint import wiki_index_handler as _v2_wiki_index  # noqa: E402
from tablero.v2.infra import infra_handler as _v2_infra  # noqa: E402
from tablero.v2.agentes import (  # noqa: E402
    agentes_handler as _v2_agentes,
    catalogo_handler as _v2_agentes_catalogo,
)

# Fase D Cockpit (WS + health)
from tablero.v2.health import health_handler as _v2_health  # noqa: E402
from tablero.v2.ws import ws_main_handler as _v2_ws_main  # noqa: E402

log = get_logger("tablero.rest")

VERSION = "0.2.0"
_PROD_ORIGIN = "https://tablero.nosvers.com"
_DEV_ORIGIN = "http://localhost:5173"


def _allowed_origin() -> str:
    return _DEV_ORIGIN if os.getenv("TABLERO_DEV") == "1" else _PROD_ORIGIN


def _cors_headers() -> dict:
    return {
        "Access-Control-Allow-Origin": _allowed_origin(),
        "Access-Control-Allow-Methods": "GET, POST, PATCH, OPTIONS",
        "Access-Control-Allow-Headers": "Authorization, Content-Type, X-Request-Id, If-Match",
        "Access-Control-Max-Age": "86400",
        "Vary": "Origin",
    }


def _json(data: dict, status: int = 200) -> JSONResponse:
    return JSONResponse(data, status_code=status, headers=_cors_headers())


def _err(code: str, status: int, detalle: Optional[str] = None) -> JSONResponse:
    payload: dict = {"ok": False, "error": code}
    if detalle:
        payload["detalle"] = detalle
    return _json(payload, status)


async def _autenticar(request: Request) -> dict | None:
    auth = request.headers.get("authorization", "")
    if not auth.lower().startswith("bearer "):
        return None
    token = auth[7:].strip()
    payload = validar_token(token)
    if not payload:
        return None
    sub = payload.get("sub", "")
    if sub not in AUTORES_VALIDOS:
        return None
    return payload


async def options_handler(request: Request) -> Response:
    return Response(status_code=204, headers=_cors_headers())


def _req_id(request: Request) -> str:
    return request.headers.get("x-request-id") or uuid.uuid4().hex[:12]


def _log_line(rid: str, sub: str, route: str, status: int, latency_ms: float, extra: str = "") -> None:
    msg = f"rid={rid} sub={sub or '-'} route={route} status={status} latency_ms={latency_ms:.1f}"
    if extra:
        msg += f" {extra}"
    log.info(msg)


async def health_handler(request: Request) -> JSONResponse:
    return _json({"ok": True, "service": "tablero", "version": VERSION})


async def whoami_handler(request: Request) -> JSONResponse:
    t0 = time.perf_counter()
    rid = _req_id(request)
    payload = await _autenticar(request)
    if not payload:
        _log_line(rid, "", "whoami", 401, (time.perf_counter() - t0) * 1000)
        return _err("auth_invalido", 401)
    body = {
        "ok": True,
        "identidad": {
            "sub": payload.get("sub", ""),
            "device": payload.get("device", ""),
            "jti": payload.get("jti", ""),
            "exp": int(payload.get("exp", 0)),
        },
    }
    _log_line(rid, payload.get("sub", ""), "whoami", 200, (time.perf_counter() - t0) * 1000)
    return _json(body)


def _parse_date_q(qp, name: str) -> date | None:
    raw = qp.get(name, "").strip()
    if not raw:
        return None
    try:
        return date.fromisoformat(raw)
    except ValueError:
        raise ValueError(f"{name} no es ISO date (YYYY-MM-DD)")


async def timeline_handler(request: Request) -> JSONResponse:
    t0 = time.perf_counter()
    rid = _req_id(request)
    payload = await _autenticar(request)
    if not payload:
        _log_line(rid, "", "timeline", 401, (time.perf_counter() - t0) * 1000)
        return _err("auth_invalido", 401)

    qp = request.query_params
    try:
        desde = _parse_date_q(qp, "desde")
        hasta = _parse_date_q(qp, "hasta")
    except ValueError as e:
        _log_line(rid, payload.get("sub", ""), "timeline", 400, (time.perf_counter() - t0) * 1000, str(e))
        return _err("parametro_invalido", 400, str(e))

    autor = qp.get("autor", "ambos").strip().lower() or "ambos"
    etiqueta = qp.get("etiqueta", "").strip().lower()
    if autor not in AUTORES_VALIDOS and autor != "ambos":
        return _err("parametro_invalido", 400, f"autor inválido: {autor!r}")
    if etiqueta and etiqueta not in ETIQUETAS_VALIDAS:
        return _err("parametro_invalido", 400, f"etiqueta inválida: {etiqueta!r}")
    try:
        limit = int(qp.get("limit", "200"))
        offset = int(qp.get("offset", "0"))
    except ValueError:
        return _err("parametro_invalido", 400, "limit/offset deben ser enteros")
    if desde and hasta and desde > hasta:
        return _err("parametro_invalido", 400, "hasta < desde")

    try:
        result = listar_timeline(desde=desde, hasta=hasta, autor=autor, etiqueta=etiqueta, limit=limit, offset=offset)
    except ValueError as e:
        _log_line(rid, payload.get("sub", ""), "timeline", 400, (time.perf_counter() - t0) * 1000, str(e))
        return _err("parametro_invalido", 400, str(e))
    except Exception as e:  # noqa: BLE001
        log.exception(f"rid={rid} timeline 500: {e}")
        alert_critical("timeline_500", f"{type(e).__name__}: {e}")
        _log_line(rid, payload.get("sub", ""), "timeline", 500, (time.perf_counter() - t0) * 1000)
        return _err("internal_error", 500)

    _log_line(rid, payload.get("sub", ""), "timeline", 200, (time.perf_counter() - t0) * 1000,
              f"total={result['total']}")
    return _json(result)


async def buscar_handler(request: Request) -> JSONResponse:
    t0 = time.perf_counter()
    rid = _req_id(request)
    payload = await _autenticar(request)
    if not payload:
        _log_line(rid, "", "buscar", 401, (time.perf_counter() - t0) * 1000)
        return _err("auth_invalido", 401)

    qp = request.query_params
    q = qp.get("q", "").strip()
    if not q:
        _log_line(rid, payload.get("sub", ""), "buscar", 400, (time.perf_counter() - t0) * 1000, "q vacío")
        return _err("input_vacio", 400, "query vacío")

    try:
        limite = int(qp.get("limite", "20"))
    except ValueError:
        return _err("parametro_invalido", 400, "limite debe ser entero")
    autor = qp.get("autor", "").strip().lower()
    etiqueta = qp.get("etiqueta", "").strip().lower()
    desde = qp.get("desde", "").strip()
    hasta = qp.get("hasta", "").strip()

    try:
        result = dia_buscar_impl(
            query=q,
            desde=desde,
            hasta=hasta,
            limite=limite,
            etiqueta=etiqueta,
            autor=autor,
        )
    except Exception as e:  # noqa: BLE001
        log.exception(f"rid={rid} buscar 500: {e}")
        alert_critical("buscar_500", f"{type(e).__name__}: {e}")
        _log_line(rid, payload.get("sub", ""), "buscar", 500, (time.perf_counter() - t0) * 1000)
        return _err("internal_error", 500)

    status = 200 if result.get("ok") else 400
    _log_line(rid, payload.get("sub", ""), "buscar", status, (time.perf_counter() - t0) * 1000,
              f"q={q!r} total={result.get('total', '?')}")
    return _json(result, status)


async def nota_handler(request: Request) -> JSONResponse:
    t0 = time.perf_counter()
    rid = _req_id(request)
    payload = await _autenticar(request)
    if not payload:
        _log_line(rid, "", "nota", 401, (time.perf_counter() - t0) * 1000)
        return _err("auth_invalido", 401)

    path = request.query_params.get("path", "").strip()
    if not path:
        return _err("parametro_invalido", 400, "path requerido")

    try:
        nota = leer_nota(path)
    except PathUnsafe as e:
        _log_line(rid, payload.get("sub", ""), "nota", 400, (time.perf_counter() - t0) * 1000, "path_unsafe")
        return _err("path_unsafe", 400, str(e))
    except ValueError as e:
        _log_line(rid, payload.get("sub", ""), "nota", 400, (time.perf_counter() - t0) * 1000, "param_inv")
        return _err("parametro_invalido", 400, str(e))
    except NotaNotFound as e:
        _log_line(rid, payload.get("sub", ""), "nota", 404, (time.perf_counter() - t0) * 1000, "not_found")
        return _err("not_found", 404, str(e))
    except Exception as e:  # noqa: BLE001
        log.exception(f"rid={rid} nota 500: {e}")
        alert_critical("nota_500", f"{type(e).__name__}: {e}")
        _log_line(rid, payload.get("sub", ""), "nota", 500, (time.perf_counter() - t0) * 1000)
        return _err("internal_error", 500)

    _log_line(rid, payload.get("sub", ""), "nota", 200, (time.perf_counter() - t0) * 1000)
    return _json({"ok": True, "nota": nota})


# -----------------------------------------------------------------------------
# Fase B+C wrappers — inyectan dependencies sin acoplar los handlers a este módulo
# -----------------------------------------------------------------------------
async def v2_capturar_handler(request: Request) -> JSONResponse:
    return await _v2_capturar(request, _autenticar, _cors_headers, _log_line)


async def v2_editar_handler(request: Request) -> JSONResponse:
    return await _v2_editar(request, _autenticar, _cors_headers, _log_line)


async def v2_archivar_handler(request: Request) -> JSONResponse:
    return await _v2_archivar(request, _autenticar, _cors_headers, _log_line)


async def v2_restaurar_handler(request: Request) -> JSONResponse:
    return await _v2_restaurar(request, _autenticar, _cors_headers, _log_line)


async def v2_proyectos_get_handler(request: Request) -> JSONResponse:
    return await _v2_proyectos_list(request, _autenticar, _cors_headers, _log_line)


async def v2_proyectos_patch_handler(request: Request) -> JSONResponse:
    return await _v2_proyectos_patch(request, _autenticar, _cors_headers, _log_line)


async def v2_vault_tree_handler(request: Request) -> JSONResponse:
    return await _v2_vault_tree(request, _autenticar, _cors_headers, _log_line)


async def v2_wiki_index_handler(request: Request) -> JSONResponse:
    return await _v2_wiki_index(request, _autenticar, _cors_headers, _log_line)


async def v2_infra_handler(request: Request) -> JSONResponse:
    return await _v2_infra(request, _autenticar, _cors_headers, _log_line)


async def v2_agentes_handler(request: Request) -> JSONResponse:
    return await _v2_agentes(request, _autenticar, _cors_headers, _log_line)


async def v2_agentes_catalogo_handler(request: Request) -> JSONResponse:
    return await _v2_agentes_catalogo(request, _autenticar, _cors_headers, _log_line)


def _startup_wiki_index() -> None:
    """Inicializa el wiki_index al arrancar el proceso. D-004."""
    try:
        from tablero.v2.wiki_index import get_index
        idx = get_index()
        idx.build()
        log.info(f"wiki_index built: {idx.stats()}")
    except Exception as e:  # noqa: BLE001
        log.exception(f"wiki_index startup failed: {e}")


ROUTES = [
    Route("/tablero/api/health", health_handler, methods=["GET"]),
    Route("/tablero/api/whoami", whoami_handler, methods=["GET"]),
    Route("/tablero/api/whoami", options_handler, methods=["OPTIONS"]),
    Route("/tablero/api/timeline", timeline_handler, methods=["GET"]),
    Route("/tablero/api/timeline", options_handler, methods=["OPTIONS"]),
    Route("/tablero/api/buscar", buscar_handler, methods=["GET"]),
    Route("/tablero/api/buscar", options_handler, methods=["OPTIONS"]),
    Route("/tablero/api/nota", nota_handler, methods=["GET"]),
    Route("/tablero/api/nota", options_handler, methods=["OPTIONS"]),
    # ── Fase B+C (D-014 prefijo /v2/) ────────────────────────────────────────
    # US1 capturar
    Route("/tablero/api/v2/capturar", v2_capturar_handler, methods=["POST"]),
    Route("/tablero/api/v2/capturar", options_handler, methods=["OPTIONS"]),
    # US2 editar
    Route("/tablero/api/v2/nota", v2_editar_handler, methods=["PATCH"]),
    Route("/tablero/api/v2/nota", options_handler, methods=["OPTIONS"]),
    # US3 archivar / restaurar
    Route("/tablero/api/v2/nota/archivar", v2_archivar_handler, methods=["POST"]),
    Route("/tablero/api/v2/nota/archivar", options_handler, methods=["OPTIONS"]),
    Route("/tablero/api/v2/nota/restaurar", v2_restaurar_handler, methods=["POST"]),
    Route("/tablero/api/v2/nota/restaurar", options_handler, methods=["OPTIONS"]),
    # US6 proyectos kanban
    Route("/tablero/api/v2/proyectos", v2_proyectos_get_handler, methods=["GET"]),
    Route("/tablero/api/v2/proyectos", v2_proyectos_patch_handler, methods=["PATCH"]),
    Route("/tablero/api/v2/proyectos", options_handler, methods=["OPTIONS"]),
    # US7 wiki-index
    Route("/tablero/api/v2/wiki-index", v2_wiki_index_handler, methods=["GET"]),
    Route("/tablero/api/v2/wiki-index", options_handler, methods=["OPTIONS"]),
    # US8 vault tree
    Route("/tablero/api/v2/vault/tree", v2_vault_tree_handler, methods=["GET"]),
    Route("/tablero/api/v2/vault/tree", options_handler, methods=["OPTIONS"]),
    # US10 infra status
    Route("/tablero/api/v2/infra/status", v2_infra_handler, methods=["GET"]),
    Route("/tablero/api/v2/infra/status", options_handler, methods=["OPTIONS"]),
    # US11 agentes
    Route("/tablero/api/v2/agentes/catalogo", v2_agentes_catalogo_handler, methods=["GET"]),
    Route("/tablero/api/v2/agentes/ejecutar", v2_agentes_handler, methods=["POST"]),
    Route("/tablero/api/v2/agentes/ejecutar", options_handler, methods=["OPTIONS"]),
    Route("/tablero/api/v2/agentes/catalogo", options_handler, methods=["OPTIONS"]),
    # Fase D — Cockpit Mission Control
    Route("/tablero/api/v2/health", _v2_health, methods=["GET"]),
    Route("/tablero/api/v2/health", options_handler, methods=["OPTIONS"]),
    WebSocketRoute("/tablero/api/v2/ws", _v2_ws_main),
]


def _startup_cockpit_workers() -> None:
    """Arranca workers asyncio del cockpit. Llamado desde montar_en_fastmcp."""
    try:
        import asyncio as _asyncio
        from tablero.v2.workers import register_all, start_activity_worker
        from tablero.v2.ws import start_all_workers
        register_all()

        async def _spawn():
            await start_all_workers()
            start_activity_worker()

        try:
            loop = _asyncio.get_event_loop()
            if loop.is_running():
                _asyncio.create_task(_spawn())
            else:
                loop.create_task(_spawn())
        except RuntimeError:
            # No event loop yet — usaremos un startup hook al app si está disponible
            log.info("cockpit workers diferidos: no event loop activo (se lanzarán en app startup)")
    except Exception as e:  # noqa: BLE001
        log.exception(f"cockpit workers startup error: {e}")


def montar_en_fastmcp(mcp_app) -> None:
    """Mount the tablero routes on FastMCP's underlying HTTP app.

    Mirrors `voz.rest.montar_en_fastmcp`. Defensive: logs and continues on any error.
    """
    try:
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
            log.warning("No pude localizar app HTTP de FastMCP — tablero REST no montado")
            return
        for r in ROUTES:
            app.router.routes.append(r)
        log.info(f"tablero/REST montado: {len(ROUTES)} rutas bajo /tablero/api/")

        # Registrar cockpit workers en el lifespan/startup de la app si soporta el hook
        try:
            from tablero.v2.workers import register_all, start_activity_worker
            from tablero.v2.ws import start_all_workers
            register_all()

            async def _on_startup() -> None:
                try:
                    await start_all_workers()
                    start_activity_worker()
                    log.info("cockpit workers arrancados (startup hook)")
                except Exception as _err:  # noqa: BLE001
                    log.exception(f"cockpit workers startup falló: {_err}")

            if hasattr(app, "router") and hasattr(app.router, "on_startup"):
                app.router.on_startup.append(_on_startup)
                log.info("cockpit workers: startup hook registrado")
            elif hasattr(app, "on_event"):
                app.on_event("startup")(_on_startup)
                log.info("cockpit workers: on_event('startup') registrado")
            else:
                log.warning("cockpit workers: no encontré hook startup — usar _startup_cockpit_workers() manual")
        except Exception as _e:  # noqa: BLE001
            log.exception(f"cockpit workers no registrados: {_e}")
    except Exception as e:  # noqa: BLE001
        log.exception(f"Error montando tablero/REST: {e}")
