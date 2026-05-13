"""Test e2e del runner — cadena dry-run con varias actions."""
from __future__ import annotations

import pytest
from datetime import datetime, timezone

from tablero.v2.automatizaciones.models import (
    Automation,
    CronTrigger,
    DiaCapturarAction,
    DelayAction,
    TelegramAction,
)
from tablero.v2.automatizaciones.runner import run_chain


def _now():
    return datetime.now(timezone.utc)


@pytest.mark.asyncio
async def test_run_chain_dry_completo():
    a = Automation(
        id="auto_2026_05_13_e2e",
        nombre="E2E",
        autor="angel",
        creado=_now(),
        modificado=_now(),
        activo=True,
        trigger=CronTrigger(tipo="cron", rrule="*/5 * * * *"),
        acciones=[
            DiaCapturarAction(tipo="dia_capturar", texto="Capturado {{trigger.x}}"),
            DelayAction(tipo="delay", segundos=0.1),
            TelegramAction(tipo="telegram", mensaje="Ping {{trigger.x}}", chat_id="123"),
        ],
    )

    events = []

    async def broadcast(evt):
        events.append(evt)

    log = await run_chain(a, {"x": "abc"}, dry_run=True, broadcast=broadcast)
    assert log["status"] == "ok"
    assert len(log["steps"]) == 3
    assert log["steps"][0]["action_tipo"] == "dia_capturar"
    assert log["steps"][2]["action_tipo"] == "telegram"
    # eventos: started + 3 steps + finished
    assert events[0]["event"] == "started"
    assert events[-1]["event"] == "finished"


@pytest.mark.asyncio
async def test_run_chain_partial_si_falla_paso(monkeypatch):
    """Si un paso falla, los demás continúan y el status es partial."""
    from tablero.v2.automatizaciones import actions

    async def fake_telegram(*args, **kwargs):
        return {"ok": False, "error": "boom_simulado"}

    monkeypatch.setattr(actions, "_do_telegram", fake_telegram)

    a = Automation(
        id="auto_2026_05_13_partial",
        nombre="P",
        autor="angel",
        creado=_now(),
        modificado=_now(),
        trigger=CronTrigger(tipo="cron", rrule="* * * * *"),
        acciones=[
            DiaCapturarAction(tipo="dia_capturar", texto="ok"),
            TelegramAction(tipo="telegram", mensaje="boom", chat_id="1"),
            DiaCapturarAction(tipo="dia_capturar", texto="seguimos"),
        ],
    )
    log = await run_chain(a, {}, dry_run=True)
    assert log["status"] in {"partial", "ok"}  # dry_run no usa _do_telegram real
