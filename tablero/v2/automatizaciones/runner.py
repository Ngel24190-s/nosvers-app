"""Runner: ejecuta una cadena de acciones secuencialmente."""
from __future__ import annotations

import asyncio
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable

from tablero.v2.automatizaciones.actions import execute_action
from tablero.v2.automatizaciones.models import Automation

log = logging.getLogger("tablero.v2.automatizaciones.runner")


async def run_chain(
    automation: Automation,
    trigger_payload: dict,
    dry_run: bool = False,
    broadcast: Callable[[dict], Awaitable[None]] | None = None,
    autor_trigger: str | None = None,
) -> dict:
    """Ejecuta la cadena. Devuelve ExecutionLog dict.

    `broadcast` es invocado con dicts de eventos:
      {event: started|step|finished|toast, ...}
    """
    execution_id = uuid.uuid4().hex[:12]
    ctx: dict[str, Any] = {
        "trigger": trigger_payload,
        "automation": {"id": automation.id, "nombre": automation.nombre},
    }
    started_at = datetime.now(timezone.utc)
    t0 = time.perf_counter()

    if broadcast:
        await broadcast({
            "event": "started",
            "execution_id": execution_id,
            "automation_id": automation.id,
            "automation_nombre": automation.nombre,
            "trigger": {"tipo": automation.trigger.tipo, "payload": trigger_payload},
        })

    steps: list[dict] = []
    overall_ok = True
    any_fail = False

    for n, action in enumerate(automation.acciones, start=1):
        step_t0 = time.perf_counter()
        try:
            res = await execute_action(action, ctx, dry_run=dry_run, broadcast=broadcast, default_autor=automation.autor)
        except Exception as e:
            log.exception(f"action {n} crashed: {e}")
            res = {"ok": False, "error": str(e)[:300], "duration_ms": int((time.perf_counter() - step_t0) * 1000)}

        step = {
            "n": n,
            "action_tipo": action.tipo,
            "ok": bool(res.get("ok", False)),
            "duration_ms": int(res.get("duration_ms", 0)),
        }
        if "error" in res:
            step["error"] = res["error"]
        if "output" in res:
            step["output"] = res["output"]
        if "would_do" in res:
            step["would_do"] = res["would_do"]
        steps.append(step)

        if step["ok"]:
            ctx[f"paso_{n}"] = res.get("output") or res.get("would_do") or {}
        else:
            any_fail = True

        if broadcast:
            await broadcast({
                "event": "step",
                "execution_id": execution_id,
                "automation_id": automation.id,
                "n": n,
                "action_tipo": action.tipo,
                "ok": step["ok"],
                "duration_ms": step["duration_ms"],
            })

    ended_at = datetime.now(timezone.utc)
    duration_ms = int((time.perf_counter() - t0) * 1000)
    if all(s["ok"] for s in steps):
        status = "ok"
    elif any(s["ok"] for s in steps) and any_fail:
        status = "partial"
        overall_ok = False
    else:
        status = "error"
        overall_ok = False

    log_entry = {
        "execution_id": execution_id,
        "automation_id": automation.id,
        "automation_nombre": automation.nombre,
        "trigger": {"tipo": automation.trigger.tipo, "payload": trigger_payload},
        "autor_trigger": autor_trigger or "system",
        "autor_automation": automation.autor,
        "started_at": started_at.isoformat(),
        "ended_at": ended_at.isoformat(),
        "duration_ms": duration_ms,
        "status": status,
        "dry_run": dry_run,
        "steps": steps,
    }

    if broadcast:
        await broadcast({
            "event": "finished",
            "execution_id": execution_id,
            "automation_id": automation.id,
            "status": status,
            "duration_ms": duration_ms,
        })

    return log_entry
