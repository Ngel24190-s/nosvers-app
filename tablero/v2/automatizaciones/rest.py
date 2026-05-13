"""REST handlers para /tablero/api/v2/automatizaciones/*."""
from __future__ import annotations

import json
import logging
import sys
import time
from datetime import datetime, timezone
from typing import Any

sys.path.insert(0, "/home/nosvers")

from pydantic import ValidationError
from starlette.requests import Request
from starlette.responses import JSONResponse

from tablero.v2.automatizaciones import storage
from tablero.v2.automatizaciones.catalogo import build_catalog
from tablero.v2.automatizaciones.logs import read_logs
from tablero.v2.automatizaciones.models import AutomationCreate
from tablero.v2.automatizaciones.motor import motor
from tablero.v2.automatizaciones.webhooks import verify_stripe_signature

log = logging.getLogger("tablero.v2.automatizaciones.rest")

WRITE_ROLES = {"angel", "africa"}


def _err(msg: str, status: int = 400, headers: dict | None = None) -> JSONResponse:
    return JSONResponse({"ok": False, "error": msg}, status_code=status, headers=headers or {})


def _validation_err(e: ValidationError, headers: dict | None = None) -> JSONResponse:
    return JSONResponse(
        {"ok": False, "error": "validacion", "errors": [
            {"loc": list(err.get("loc", [])), "msg": err.get("msg", ""), "type": err.get("type", "")}
            for err in e.errors()
        ]},
        status_code=422,
        headers=headers or {},
    )


async def _auth_or_401(request: Request, autenticador, cors_headers) -> tuple[dict | None, JSONResponse | None]:
    payload = await autenticador(request)
    if not payload:
        return None, _err("auth_invalido", 401, cors_headers())
    return payload, None


# ── Handlers ────────────────────────────────────────────────────────────────

async def list_handler(request: Request, autenticador, cors_headers, log_line) -> JSONResponse:
    t0 = time.perf_counter()
    p, err = await _auth_or_401(request, autenticador, cors_headers)
    if err:
        return err
    items, errores = storage.load_all()
    out = [storage.summary(a, motor.get_last_run(a.id)) for a in items]
    log_line("anon", p.get("sub", ""), "v2/automatizaciones", 200, (time.perf_counter() - t0) * 1000)
    return JSONResponse({"items": out, "corruptos": [f"{k}: {v}" for k, v in errores.items()]}, headers=cors_headers())


async def get_handler(request: Request, autenticador, cors_headers, log_line) -> JSONResponse:
    p, err = await _auth_or_401(request, autenticador, cors_headers)
    if err:
        return err
    id_ = request.path_params.get("id", "")
    a = storage.load_one(id_)
    if a is None:
        return _err("not_found", 404, cors_headers())
    return JSONResponse(a.model_dump(mode="json"), headers=cors_headers())


async def create_handler(request: Request, autenticador, cors_headers, log_line) -> JSONResponse:
    p, err = await _auth_or_401(request, autenticador, cors_headers)
    if err:
        return err
    sub = p.get("sub", "")
    if sub not in WRITE_ROLES:
        return _err("permiso_denegado", 403, cors_headers())
    try:
        body = json.loads(await request.body() or b"{}")
    except json.JSONDecodeError:
        return _err("json_invalido", 400, cors_headers())
    try:
        ac = AutomationCreate.model_validate(body)
    except ValidationError as e:
        return _validation_err(e, cors_headers())
    a = storage.create_from(ac, autor=sub)
    storage.save(a)
    motor.reload()
    return JSONResponse({"ok": True, "id": a.id}, status_code=201, headers=cors_headers())


async def update_handler(request: Request, autenticador, cors_headers, log_line) -> JSONResponse:
    p, err = await _auth_or_401(request, autenticador, cors_headers)
    if err:
        return err
    sub = p.get("sub", "")
    if sub not in WRITE_ROLES:
        return _err("permiso_denegado", 403, cors_headers())
    id_ = request.path_params.get("id", "")
    try:
        body = json.loads(await request.body() or b"{}")
    except json.JSONDecodeError:
        return _err("json_invalido", 400, cors_headers())
    try:
        ac = AutomationCreate.model_validate(body)
    except ValidationError as e:
        return _validation_err(e, cors_headers())
    a = storage.update(id_, ac)
    if a is None:
        return _err("not_found", 404, cors_headers())
    motor.reload()
    return JSONResponse({"ok": True}, headers=cors_headers())


async def delete_handler(request: Request, autenticador, cors_headers, log_line) -> JSONResponse:
    p, err = await _auth_or_401(request, autenticador, cors_headers)
    if err:
        return err
    sub = p.get("sub", "")
    if sub not in WRITE_ROLES:
        return _err("permiso_denegado", 403, cors_headers())
    id_ = request.path_params.get("id", "")
    dest = storage.delete(id_)
    if dest is None:
        return _err("not_found", 404, cors_headers())
    motor.reload()
    return JSONResponse({"ok": True, "archived_path": str(dest)}, headers=cors_headers())


async def run_handler(request: Request, autenticador, cors_headers, log_line) -> JSONResponse:
    p, err = await _auth_or_401(request, autenticador, cors_headers)
    if err:
        return err
    sub = p.get("sub", "")
    id_ = request.path_params.get("id", "")
    try:
        body = json.loads(await request.body() or b"{}")
    except json.JSONDecodeError:
        body = {}
    trigger_payload = body.get("trigger_payload") or {"manual": True, "by": sub}
    res = await motor.run_one(id_, trigger_payload, dry_run=False, autor_trigger=sub)
    if res.get("error") == "not_found":
        return _err("not_found", 404, cors_headers())
    return JSONResponse(res, headers=cors_headers())


async def test_handler(request: Request, autenticador, cors_headers, log_line) -> JSONResponse:
    p, err = await _auth_or_401(request, autenticador, cors_headers)
    if err:
        return err
    sub = p.get("sub", "")
    id_ = request.path_params.get("id", "")
    try:
        body = json.loads(await request.body() or b"{}")
    except json.JSONDecodeError:
        body = {}
    trigger_payload = body.get("trigger_payload") or {"test": True, "by": sub}
    res = await motor.run_one(id_, trigger_payload, dry_run=True, autor_trigger=sub)
    if res.get("error") == "not_found":
        return _err("not_found", 404, cors_headers())
    return JSONResponse(res, headers=cors_headers())


async def logs_handler(request: Request, autenticador, cors_headers, log_line) -> JSONResponse:
    p, err = await _auth_or_401(request, autenticador, cors_headers)
    if err:
        return err
    id_ = request.path_params.get("id", "")
    date = request.query_params.get("date") or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    items = read_logs(date, automation_id=id_)
    return JSONResponse({"date": date, "items": items}, headers=cors_headers())


async def catalogo_handler(request: Request, autenticador, cors_headers, log_line) -> JSONResponse:
    p, err = await _auth_or_401(request, autenticador, cors_headers)
    if err:
        return err
    return JSONResponse(build_catalog(), headers=cors_headers())


async def reload_handler(request: Request, autenticador, cors_headers, log_line) -> JSONResponse:
    p, err = await _auth_or_401(request, autenticador, cors_headers)
    if err:
        return err
    res = motor.reload()
    return JSONResponse({"ok": True, **res}, headers=cors_headers())


async def webhook_stripe_handler(request: Request, autenticador, cors_headers, log_line) -> JSONResponse:
    """No requiere JWT — autentica con firma Stripe."""
    body_bytes = await request.body()
    sig = request.headers.get("stripe-signature", "")
    secret = __import__("os").environ.get("STRIPE_WEBHOOK_SECRET", "")
    if not secret:
        return JSONResponse({"ok": False, "error": "stripe_no_configurado"}, status_code=503)
    if not verify_stripe_signature(body_bytes, sig, secret):
        return JSONResponse({"ok": False, "error": "firma_invalida"}, status_code=401)
    try:
        payload = json.loads(body_bytes)
    except json.JSONDecodeError:
        return JSONResponse({"ok": False, "error": "json_invalido"}, status_code=400)
    res = await motor.fire_webhook_stripe(payload)
    return JSONResponse({"received": True, **res})
