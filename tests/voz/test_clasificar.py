"""T015 — Tests unitarios de voz.clasificar."""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from voz import clasificar


def test_fallback_force_fail(vault_temporal, clasif_off):
    res = clasificar.clasificar("Pedir fotos a África")
    assert res["etiqueta"] == "otro"
    assert res["modelo"] == "fallback"
    assert res["confianza"] == 0.0
    assert "CLASIFICADOR_FORCE_FAIL" in res.get("razon", "")


def test_texto_vacio_devuelve_fallback(vault_temporal):
    res = clasificar.clasificar("")
    assert res["etiqueta"] == "otro"
    assert res["modelo"] == "fallback"


def test_sin_api_key_fallback(vault_temporal, monkeypatch):
    monkeypatch.delenv("CLASIFICADOR_FORCE_FAIL", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    res = clasificar.clasificar("texto cualquiera")
    assert res["etiqueta"] == "otro"
    assert res["modelo"] == "fallback"


def test_respuesta_valida_haiku(vault_temporal, monkeypatch):
    """Mock de la respuesta Haiku con JSON correcto."""
    monkeypatch.delenv("CLASIFICADOR_FORCE_FAIL", raising=False)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-fake-test")

    fake_resp = MagicMock()
    fake_resp.status_code = 200
    fake_resp.json.return_value = {
        "content": [{"text": json.dumps({
            "etiqueta": "nosvers",
            "confianza": 0.92,
            "razon": "menciona la ferme",
        })}]
    }

    with patch.object(clasificar.requests, "post", return_value=fake_resp) as post:
        res = clasificar.clasificar("Pedir fotos a África para Instagram NosVers")
        assert res["etiqueta"] == "nosvers"
        assert res["confianza"] == pytest.approx(0.92)
        assert res["modelo"].startswith("claude-")
        assert post.called


def test_json_malformado_fallback(vault_temporal, monkeypatch):
    monkeypatch.delenv("CLASIFICADOR_FORCE_FAIL", raising=False)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-fake-test")

    fake_resp = MagicMock()
    fake_resp.status_code = 200
    fake_resp.json.return_value = {"content": [{"text": "no soy json válido {{{"}]}
    fake_resp.text = "no soy json válido"

    with patch.object(clasificar.requests, "post", return_value=fake_resp):
        res = clasificar.clasificar("texto")
        assert res["etiqueta"] == "otro"
        assert res["modelo"] == "fallback"
        assert "parse" in res.get("razon", "")


def test_etiqueta_invalida_se_normaliza(vault_temporal, monkeypatch):
    monkeypatch.delenv("CLASIFICADOR_FORCE_FAIL", raising=False)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-fake-test")

    fake_resp = MagicMock()
    fake_resp.status_code = 200
    fake_resp.json.return_value = {
        "content": [{"text": json.dumps({"etiqueta": "invento", "confianza": 0.8})}]
    }
    with patch.object(clasificar.requests, "post", return_value=fake_resp):
        res = clasificar.clasificar("texto")
        # Etiqueta no en ETIQUETAS_VALIDAS → normalizada a "otro" pero el modelo es real
        assert res["etiqueta"] == "otro"


def test_timeout_red_fallback(vault_temporal, monkeypatch):
    monkeypatch.delenv("CLASIFICADOR_FORCE_FAIL", raising=False)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-fake-test")

    with patch.object(clasificar.requests, "post",
                      side_effect=clasificar.requests.exceptions.Timeout("timed out")):
        res = clasificar.clasificar("texto")
        assert res["etiqueta"] == "otro"
        assert res["modelo"] == "fallback"
        assert "Timeout" in res.get("razon", "") or "red" in res.get("razon", "")
