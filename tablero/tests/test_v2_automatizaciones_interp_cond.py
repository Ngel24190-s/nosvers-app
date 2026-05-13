"""Tests interpolation + condicional DSL."""
from __future__ import annotations

import pytest

from tablero.v2.automatizaciones.condicional import evaluar
from tablero.v2.automatizaciones.interpolation import resolve, resolve_dict


CTX = {
    "trigger": {"amount": 150, "customer": "x@y.com", "texto": "hola URGENTE mundo"},
    "paso_1": {"respuesta": "OK perfecto"},
}


def test_resolve_simple():
    assert resolve("Total {{trigger.amount}}€", CTX) == "Total 150€"


def test_resolve_paso_n():
    assert resolve("Tras paso 1: {{paso_1.respuesta}}", CTX) == "Tras paso 1: OK perfecto"


def test_resolve_now_today():
    out = resolve("{{today}}", CTX)
    assert len(out) >= 8


def test_resolve_missing_devuelve_vacio():
    assert resolve("X={{trigger.nope}}.", CTX) == "X=."


def test_resolve_env_whitelist(monkeypatch):
    monkeypatch.setenv("ANGEL_CHAT_ID", "12345")
    assert resolve("chat: {{env.ANGEL_CHAT_ID}}", CTX) == "chat: 12345"


def test_resolve_env_no_whitelist(monkeypatch):
    monkeypatch.setenv("SECRET_LEAK", "boom")
    # SECRET_LEAK no está en whitelist
    assert resolve("X={{env.SECRET_LEAK}}", CTX) == "X="


def test_resolve_dict_recursivo():
    obj = {"a": "Total: {{trigger.amount}}", "b": ["{{trigger.customer}}", 1]}
    out = resolve_dict(obj, CTX)
    assert out["a"] == "Total: 150"
    assert out["b"][0] == "x@y.com"


def test_condicional_basico_gt():
    assert evaluar("{{trigger.amount}} > 100", CTX) is True
    assert evaluar("{{trigger.amount}} > 200", CTX) is False


def test_condicional_eq_string():
    assert evaluar('{{trigger.customer}} == "x@y.com"', CTX) is True


def test_condicional_contains():
    assert evaluar('{{trigger.texto}} contains "URGENTE"', CTX) is True
    assert evaluar('{{trigger.texto}} contains "ZZZ"', CTX) is False


def test_condicional_matches():
    assert evaluar(r'{{trigger.customer}} matches "@y\.com$"', CTX) is True


def test_condicional_injection_rechazado():
    with pytest.raises(ValueError):
        evaluar("__import__('os').system('echo hack')", CTX)
    with pytest.raises(ValueError):
        evaluar("exec('boom')", CTX)


def test_condicional_demasiado_largo():
    with pytest.raises(ValueError):
        evaluar("x" * 600, CTX)
