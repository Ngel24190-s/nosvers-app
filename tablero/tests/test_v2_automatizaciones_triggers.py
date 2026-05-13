"""Tests matchers de triggers."""
from __future__ import annotations

from datetime import datetime, timezone

from tablero.v2.automatizaciones.triggers import (
    cron_should_fire,
    matches_aegis_alerta,
    matches_agente_terminado,
    matches_email,
    matches_nota_capturada,
    matches_voz_keyword,
    matches_vps_threshold,
    matches_webhook_stripe,
)


def test_nota_capturada_filtros():
    f = {"autor": "angel", "etiqueta": "huerto"}
    ev = {"autor": "angel", "etiqueta": "huerto", "texto": "Sembrar"}
    ok, _ = matches_nota_capturada(f, ev)
    assert ok
    ok, _ = matches_nota_capturada(f, {"autor": "africa", "etiqueta": "huerto"})
    assert not ok


def test_nota_contenido_regex():
    f = {"contenido_regex": "regad?(a|o|os)"}
    ev = {"texto": "regado de la mañana"}
    ok, _ = matches_nota_capturada(f, ev)
    assert ok


def test_agente_terminado():
    ok, _ = matches_agente_terminado({"nombre_agente": "agt05_africa", "estado": "success"},
                                     {"nombre": "agt05_africa", "estado": "success"})
    assert ok
    ok, _ = matches_agente_terminado({"estado": "error"}, {"nombre": "agt05_africa", "estado": "success"})
    assert not ok


def test_aegis():
    ok, _ = matches_aegis_alerta({"severidad": "critical"}, {"severidad": "critical"})
    assert ok
    ok, _ = matches_aegis_alerta({"severidad": "critical"}, {"severidad": "info"})
    assert not ok


def test_voz_keyword():
    ok, _ = matches_voz_keyword(["urgente"], {"origen": "voz", "texto": "Esto es URGENTE"})
    assert ok
    ok, _ = matches_voz_keyword(["urgente"], {"origen": "voz", "texto": "Tranquilo"})
    assert not ok


def test_vps_threshold_gt():
    ok, _ = matches_vps_threshold("cpu", 80.0, "gt", {"cpu_pct": 90})
    assert ok
    ok, _ = matches_vps_threshold("cpu", 80.0, "gt", {"cpu_pct": 50})
    assert not ok


def test_webhook_stripe_filtro_amount():
    payload = {
        "type": "payment_intent.succeeded",
        "data": {"object": {"amount": 15000, "customer_email": "a@b.com"}},
    }
    ok, norm = matches_webhook_stripe("payment_intent.succeeded", {"amount_gte_eur": 100}, payload)
    assert ok
    assert norm["amount"] == 150.0
    ok, _ = matches_webhook_stripe("payment_intent.succeeded", {"amount_gte_eur": 200}, payload)
    assert not ok


def test_email_match():
    ok, _ = matches_email({"from_regex": ".*@stripe.com"}, {"from": "noreply@stripe.com", "subject": "ping"})
    assert ok
    ok, _ = matches_email({"from_regex": ".*@stripe.com"}, {"from": "spam@elsewhere.io"})
    assert not ok


def test_cron_should_fire():
    # rrule cada minuto — el now actual debe disparar dentro de la ventana 30s
    now = datetime.now(timezone.utc)
    assert cron_should_fire("* * * * *", now, ventana_s=60.0)
    # rrule a las 4:00am del día 1 de enero — no debe dispararse en mayo
    assert not cron_should_fire("0 4 1 1 *", now, ventana_s=60.0)
