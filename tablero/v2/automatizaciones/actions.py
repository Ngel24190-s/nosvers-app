"""Dispatcher de actions.

`execute_action(action, ctx, dry_run) -> dict` aplica interpolación a strings,
ejecuta la acción con timeout, captura excepciones y devuelve dict con
`{ok, output?, error?, duration_ms}`.
"""
from __future__ import annotations

import asyncio
import base64
import json
import logging
import os
import subprocess
import sys
import time
from typing import Any

import httpx

from tablero.v2.automatizaciones.condicional import evaluar as evaluar_condicion
from tablero.v2.automatizaciones.interpolation import resolve, resolve_dict
from tablero.v2.automatizaciones.models import (
    ClaudePromptAction,
    CockpitToastAction,
    CondicionalAction,
    DelayAction,
    DiaCapturarAction,
    EjecutarAgenteAction,
    EmailEnviarAction,
    TelegramAction,
    WebhookCallAction,
    WpPostAction,
)

log = logging.getLogger("tablero.v2.automatizaciones.actions")

ACTION_TIMEOUT_S = 30
AGENTE_TIMEOUT_S = 60


# ── Implementaciones individuales ───────────────────────────────────────────

async def _do_telegram(action: TelegramAction, ctx: dict, dry_run: bool) -> dict:
    mensaje = resolve(action.mensaje, ctx)
    chat_id = action.chat_id or os.environ.get("ANGEL_CHAT_ID", "")
    if not chat_id:
        return {"ok": False, "error": "chat_id_missing"}
    if dry_run:
        return {"ok": True, "would_do": {"mensaje": mensaje, "chat_id": chat_id}}
    token = os.environ.get("TELEGRAM_TOKEN", "")
    if not token:
        return {"ok": False, "error": "TELEGRAM_TOKEN_missing"}
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    async with httpx.AsyncClient(timeout=10.0) as c:
        r = await c.post(url, json={"chat_id": chat_id, "text": mensaje, "parse_mode": "Markdown"})
        if r.status_code != 200:
            return {"ok": False, "error": f"telegram_{r.status_code}", "body": r.text[:200]}
        return {"ok": True, "message_id": r.json().get("result", {}).get("message_id")}


async def _do_dia_capturar(action: DiaCapturarAction, ctx: dict, dry_run: bool, default_autor: str) -> dict:
    texto = resolve(action.texto, ctx)
    etiqueta = action.etiqueta or "auto"
    autor = action.autor or default_autor
    if dry_run:
        return {"ok": True, "would_do": {"texto": texto, "etiqueta": etiqueta, "autor": autor}}
    # Import lazy para no romper si voz.capturar tiene side-effects al importar
    sys.path.insert(0, "/home/nosvers")
    from voz.capturar import dia_capturar_impl
    res = await asyncio.to_thread(
        dia_capturar_impl,
        texto=texto,
        etiqueta=etiqueta,
        origen="otro",
        autor=autor,
        device_label="automation_engine",
    )
    return {"ok": bool(res.get("ok", True)), "output": res}


async def _do_ejecutar_agente(action: EjecutarAgenteAction, ctx: dict, dry_run: bool) -> dict:
    agente = resolve(action.agente, ctx)
    params = resolve_dict(action.params, ctx)
    cmd = [
        sys.executable,
        "/home/nosvers/unified-agent/nosvers_agent.py",
        "--agente", agente,
        "--params", json.dumps(params),
    ]
    if dry_run:
        return {"ok": True, "would_do": {"cmd": cmd}}
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=AGENTE_TIMEOUT_S)
        except asyncio.TimeoutError:
            proc.kill()
            return {"ok": False, "error": "timeout"}
        return {
            "ok": proc.returncode == 0,
            "output": {
                "returncode": proc.returncode,
                "stdout_tail": stdout[-2000:].decode("utf-8", "replace") if stdout else "",
                "stderr_tail": stderr[-1000:].decode("utf-8", "replace") if stderr else "",
            },
        }
    except FileNotFoundError as e:
        return {"ok": False, "error": f"agente_no_disponible: {e}"}


async def _do_claude_prompt(action: ClaudePromptAction, ctx: dict, dry_run: bool) -> dict:
    prompt = resolve(action.prompt, ctx)
    system = resolve(action.system, ctx)
    if dry_run:
        return {"ok": True, "would_do": {"model": action.model, "prompt": prompt[:200]}}
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return {"ok": False, "error": "ANTHROPIC_API_KEY_missing"}
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)

        def _call():
            return client.messages.create(
                model=action.model,
                max_tokens=action.max_tokens,
                system=system or "Eres un asistente útil de NosVers.",
                messages=[{"role": "user", "content": prompt}],
            )
        resp = await asyncio.to_thread(_call)
        texto = resp.content[0].text if resp.content else ""
        return {"ok": True, "output": {"respuesta": texto}}
    except Exception as e:
        return {"ok": False, "error": str(e)[:300]}


async def _do_email_enviar(action: EmailEnviarAction, ctx: dict, dry_run: bool) -> dict:
    to = resolve(action.to, ctx)
    subject = resolve(action.subject, ctx)
    body = resolve(action.body, ctx)
    if dry_run:
        return {"ok": True, "would_do": {"to": to, "subject": subject}}
    smtp_host = os.environ.get("SMTP_HOST", "")
    if not smtp_host:
        return {"ok": False, "error": "SMTP_HOST_no_configurado"}
    # Stub real-send: para v1 no enviamos, solo log. Activable cuando SMTP_HOST exista.
    log.info(f"email_enviar (no implementado real): to={to} subject={subject}")
    return {"ok": False, "error": "email_no_implementado_v1"}


async def _do_webhook_call(action: WebhookCallAction, ctx: dict, dry_run: bool) -> dict:
    url = resolve(action.url, ctx)
    headers = {k: resolve(v, ctx) for k, v in action.headers.items()}
    body = resolve_dict(action.body_json or {}, ctx) if action.body_json is not None else None
    if dry_run:
        return {"ok": True, "would_do": {"url": url, "method": action.method, "headers": headers, "body": body}}
    try:
        async with httpx.AsyncClient(timeout=ACTION_TIMEOUT_S) as c:
            r = await c.request(
                action.method,
                url,
                headers=headers or None,
                json=body,
            )
            return {
                "ok": 200 <= r.status_code < 300,
                "output": {"status": r.status_code, "body_tail": r.text[:500]},
            }
    except Exception as e:
        return {"ok": False, "error": str(e)[:300]}


async def _do_cockpit_toast(action: CockpitToastAction, ctx: dict, dry_run: bool, broadcast) -> dict:
    text = resolve(action.text, ctx)
    if dry_run:
        return {"ok": True, "would_do": {"level": action.level, "text": text}}
    if broadcast is None:
        return {"ok": False, "error": "broadcast_no_disponible"}
    await broadcast({"event": "toast", "level": action.level, "text": text})
    return {"ok": True}


async def _do_wp_post(action: WpPostAction, ctx: dict, dry_run: bool) -> dict:
    titulo = resolve(action.titulo, ctx)
    contenido = resolve(action.contenido_html, ctx)
    if dry_run:
        return {"ok": True, "would_do": {"titulo": titulo, "status": action.status}}
    wp_api = os.environ.get("WP_API", "").rstrip("/")
    wp_user = os.environ.get("WP_USER", "")
    wp_pass = os.environ.get("WP_PASS", "")
    if not wp_api or not wp_user or not wp_pass:
        return {"ok": False, "error": "WP_API_no_configurado"}
    auth = base64.b64encode(f"{wp_user}:{wp_pass}".encode()).decode()
    try:
        async with httpx.AsyncClient(timeout=ACTION_TIMEOUT_S) as c:
            r = await c.post(
                f"{wp_api}/posts",
                headers={"Authorization": f"Basic {auth}", "Content-Type": "application/json"},
                json={"title": titulo, "content": contenido, "status": action.status},
            )
            if r.status_code not in (200, 201):
                return {"ok": False, "error": f"wp_{r.status_code}", "body": r.text[:300]}
            return {"ok": True, "output": {"id": r.json().get("id"), "link": r.json().get("link")}}
    except Exception as e:
        return {"ok": False, "error": str(e)[:300]}


async def _do_delay(action: DelayAction) -> dict:
    await asyncio.sleep(action.segundos)
    return {"ok": True, "output": {"slept_s": action.segundos}}


async def _do_condicional(
    action: CondicionalAction,
    ctx: dict,
    dry_run: bool,
    broadcast,
    default_autor: str,
) -> dict:
    try:
        truthy = evaluar_condicion(action.expresion, ctx)
    except Exception as e:
        return {"ok": False, "error": f"condicional_invalida: {e}"}
    rama = action.acciones_si if truthy else action.acciones_no
    resultados: list[dict] = []
    for i, sub in enumerate(rama, start=1):
        r = await execute_action(sub, ctx, dry_run, broadcast, default_autor)
        resultados.append(r)
        # Si una sub-acción falla, seguimos (igual que en la cadena principal).
    return {"ok": True, "output": {"rama": "si" if truthy else "no", "sub_results": resultados}}


# ── Dispatcher ──────────────────────────────────────────────────────────────

async def execute_action(
    action: Any,
    ctx: dict,
    dry_run: bool = False,
    broadcast=None,
    default_autor: str = "angel",
) -> dict:
    """Ejecuta una action. Devuelve dict con ok/output/error + duration_ms."""
    t0 = time.perf_counter()
    try:
        coro: Any
        if isinstance(action, TelegramAction):
            coro = _do_telegram(action, ctx, dry_run)
        elif isinstance(action, DiaCapturarAction):
            coro = _do_dia_capturar(action, ctx, dry_run, default_autor)
        elif isinstance(action, EjecutarAgenteAction):
            coro = _do_ejecutar_agente(action, ctx, dry_run)
        elif isinstance(action, ClaudePromptAction):
            coro = _do_claude_prompt(action, ctx, dry_run)
        elif isinstance(action, EmailEnviarAction):
            coro = _do_email_enviar(action, ctx, dry_run)
        elif isinstance(action, WebhookCallAction):
            coro = _do_webhook_call(action, ctx, dry_run)
        elif isinstance(action, CockpitToastAction):
            coro = _do_cockpit_toast(action, ctx, dry_run, broadcast)
        elif isinstance(action, WpPostAction):
            coro = _do_wp_post(action, ctx, dry_run)
        elif isinstance(action, DelayAction):
            coro = _do_delay(action)
        elif isinstance(action, CondicionalAction):
            coro = _do_condicional(action, ctx, dry_run, broadcast, default_autor)
        else:
            return {"ok": False, "error": f"action_desconocida: {type(action).__name__}"}
        try:
            timeout = AGENTE_TIMEOUT_S if isinstance(action, EjecutarAgenteAction) else ACTION_TIMEOUT_S + 5
            if isinstance(action, DelayAction):
                timeout = action.segundos + 5
            res = await asyncio.wait_for(coro, timeout=timeout)
        except asyncio.TimeoutError:
            res = {"ok": False, "error": "timeout"}
    except Exception as e:
        log.exception(f"execute_action error: {e}")
        res = {"ok": False, "error": str(e)[:300]}
    res["duration_ms"] = int((time.perf_counter() - t0) * 1000)
    return res
