"""Tests del dispatcher de actions — dry_run + ramas internas."""
from __future__ import annotations

import asyncio
import pytest

from tablero.v2.automatizaciones.actions import execute_action
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


@pytest.mark.asyncio
async def test_telegram_dry_run():
    a = TelegramAction(tipo="telegram", mensaje="Hola {{trigger.amount}}", chat_id="12345")
    r = await execute_action(a, {"trigger": {"amount": 99}}, dry_run=True)
    assert r["ok"] is True
    assert r["would_do"]["mensaje"] == "Hola 99"


@pytest.mark.asyncio
async def test_dia_capturar_dry_run():
    a = DiaCapturarAction(tipo="dia_capturar", texto="Hola {{trigger.x}}")
    r = await execute_action(a, {"trigger": {"x": "mundo"}}, dry_run=True, default_autor="angel")
    assert r["ok"] is True
    assert r["would_do"]["texto"] == "Hola mundo"
    assert r["would_do"]["autor"] == "angel"


@pytest.mark.asyncio
async def test_delay_action():
    a = DelayAction(tipo="delay", segundos=0.1)
    r = await execute_action(a, {})
    assert r["ok"] is True
    assert r["output"]["slept_s"] == 0.1


@pytest.mark.asyncio
async def test_cockpit_toast_dry_run():
    a = CockpitToastAction(tipo="cockpit_toast", level="ok", text="Hello")
    r = await execute_action(a, {}, dry_run=True)
    assert r["ok"] is True
    assert r["would_do"]["text"] == "Hello"


@pytest.mark.asyncio
async def test_webhook_call_dry_run():
    a = WebhookCallAction(
        tipo="webhook_call",
        url="https://example.com/{{trigger.x}}",
        method="POST",
        body_json={"v": 1},
    )
    r = await execute_action(a, {"trigger": {"x": "abc"}}, dry_run=True)
    assert r["ok"] is True
    assert r["would_do"]["url"] == "https://example.com/abc"


@pytest.mark.asyncio
async def test_ejecutar_agente_dry_run():
    a = EjecutarAgenteAction(tipo="ejecutar_agente", agente="agt05_africa", params={"q": "{{trigger.q}}"})
    r = await execute_action(a, {"trigger": {"q": "test"}}, dry_run=True)
    assert r["ok"] is True
    assert "agt05_africa" in str(r["would_do"]["cmd"])


@pytest.mark.asyncio
async def test_claude_prompt_dry_run():
    a = ClaudePromptAction(tipo="claude_prompt", prompt="Hola {{trigger.name}}", max_tokens=100)
    r = await execute_action(a, {"trigger": {"name": "Angel"}}, dry_run=True)
    assert r["ok"] is True


@pytest.mark.asyncio
async def test_email_enviar_sin_config():
    a = EmailEnviarAction(tipo="email_enviar", to="a@b.com", subject="x", body="y")
    r = await execute_action(a, {}, dry_run=False)
    assert r["ok"] is False
    assert "SMTP" in r["error"]


@pytest.mark.asyncio
async def test_wp_post_sin_config(monkeypatch):
    monkeypatch.delenv("WP_API", raising=False)
    a = WpPostAction(tipo="wp_post", titulo="X", contenido_html="<p>hi</p>")
    r = await execute_action(a, {}, dry_run=False)
    assert r["ok"] is False
    assert "WP_API" in r["error"]


@pytest.mark.asyncio
async def test_condicional_si():
    inner = TelegramAction(tipo="telegram", mensaje="grande", chat_id="1")
    other = TelegramAction(tipo="telegram", mensaje="chico", chat_id="1")
    a = CondicionalAction(
        tipo="condicional",
        expresion="{{trigger.amount}} > 100",
        acciones_si=[inner],
        acciones_no=[other],
    )
    r = await execute_action(a, {"trigger": {"amount": 150}}, dry_run=True)
    assert r["ok"] is True
    assert r["output"]["rama"] == "si"
    assert len(r["output"]["sub_results"]) == 1


@pytest.mark.asyncio
async def test_condicional_no():
    inner = TelegramAction(tipo="telegram", mensaje="grande", chat_id="1")
    other = TelegramAction(tipo="telegram", mensaje="chico", chat_id="1")
    a = CondicionalAction(
        tipo="condicional",
        expresion="{{trigger.amount}} > 100",
        acciones_si=[inner],
        acciones_no=[other],
    )
    r = await execute_action(a, {"trigger": {"amount": 50}}, dry_run=True)
    assert r["output"]["rama"] == "no"


@pytest.mark.asyncio
async def test_condicional_invalida():
    a = CondicionalAction(
        tipo="condicional",
        expresion="boom!",  # no parsea
        acciones_si=[TelegramAction(tipo="telegram", mensaje="x", chat_id="1")],
    )
    r = await execute_action(a, {}, dry_run=True)
    assert r["ok"] is False
    assert "condicional" in r["error"]
