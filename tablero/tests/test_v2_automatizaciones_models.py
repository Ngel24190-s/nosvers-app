"""Tests Pydantic models para Automation Engine (proyecto 004)."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from tablero.v2.automatizaciones.models import (
    Automation,
    AutomationCreate,
    CronTrigger,
    DiaCapturarAction,
    EmailMatchTrigger,
    TelegramAction,
    VozKeywordTrigger,
    VpsThresholdTrigger,
    WebhookStripeTrigger,
    CondicionalAction,
    ClaudePromptAction,
)


def _now():
    return datetime.now(timezone.utc)


def test_automation_round_trip_cron_telegram():
    a = Automation(
        id="auto_2026_05_13_test_ok",
        nombre="Test",
        autor="angel",
        creado=_now(),
        modificado=_now(),
        activo=True,
        trigger=CronTrigger(tipo="cron", rrule="*/5 * * * *"),
        acciones=[
            DiaCapturarAction(tipo="dia_capturar", texto="hola {{now}}"),
            TelegramAction(tipo="telegram", mensaje="ping"),
        ],
    )
    data = a.model_dump(mode="json")
    a2 = Automation.model_validate(data)
    assert a2.id == a.id
    assert a2.trigger.tipo == "cron"
    assert len(a2.acciones) == 2


def test_cron_rrule_invalida():
    with pytest.raises(ValidationError):
        CronTrigger(tipo="cron", rrule="no es una cron")


def test_id_pattern_rechazado():
    with pytest.raises(ValidationError):
        Automation(
            id="malformado",
            nombre="x",
            autor="angel",
            creado=_now(),
            modificado=_now(),
            trigger=CronTrigger(tipo="cron", rrule="* * * * *"),
            acciones=[DiaCapturarAction(tipo="dia_capturar", texto="x")],
        )


def test_extras_rechazados():
    with pytest.raises(ValidationError):
        AutomationCreate.model_validate({
            "nombre": "x",
            "extra_field": "boom",
            "trigger": {"tipo": "cron", "rrule": "* * * * *"},
            "acciones": [{"tipo": "dia_capturar", "texto": "x"}],
        })


def test_webhook_stripe_filtros_opcionales():
    t = WebhookStripeTrigger(tipo="webhook_stripe")
    assert t.evento == "payment_intent.succeeded"
    assert t.filtros == {}


def test_voz_keyword_requiere_lista():
    with pytest.raises(ValidationError):
        VozKeywordTrigger(tipo="voz_keyword", keywords=[])


def test_vps_threshold_validators():
    with pytest.raises(ValidationError):
        VpsThresholdTrigger(tipo="vps_threshold", metrica="cpu", umbral_pct=150, comparador="gt")


def test_email_match_filtros_dict():
    t = EmailMatchTrigger(tipo="email_match", filtros={"from_regex": ".*@stripe.com"})
    assert t.filtros["from_regex"] == ".*@stripe.com"


def test_condicional_anidado():
    a = CondicionalAction(
        tipo="condicional",
        expresion="{{trigger.amount}} > 100",
        acciones_si=[TelegramAction(tipo="telegram", mensaje="grande")],
        acciones_no=[TelegramAction(tipo="telegram", mensaje="pequeño")],
    )
    assert len(a.acciones_si) == 1
    assert len(a.acciones_no) == 1


def test_claude_prompt_defaults():
    a = ClaudePromptAction(tipo="claude_prompt", prompt="Hola")
    assert a.model == "claude-haiku-4-5-20251001"
    assert a.max_tokens == 2000


def test_automation_create_genera_a_partir_de_yaml_simple():
    body = {
        "nombre": "X",
        "trigger": {"tipo": "cron", "rrule": "0 9 * * 1"},
        "acciones": [{"tipo": "dia_capturar", "texto": "lunes"}],
    }
    ac = AutomationCreate.model_validate(body)
    assert ac.trigger.tipo == "cron"
    assert ac.acciones[0].tipo == "dia_capturar"
