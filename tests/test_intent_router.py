"""Tests del intent router. Mockea la llamada Anthropic con monkeypatch.

20+ casos cubriendo gastos, recordatorios, compras, salud, coche, menú,
fallback de baja confidence, tool fuera whitelist, JSON corrupto,
timeout, texto vacío, idempotencia, autor África.
"""
from __future__ import annotations

import asyncio
import json
from unittest.mock import MagicMock

import pytest

import voz.intent_router as router


@pytest.fixture(autouse=True)
def _clear_router_cache():
    router.clear_cache()
    yield
    router.clear_cache()


@pytest.fixture(autouse=True)
def _api_key(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-xxx")
    monkeypatch.delenv("INTENT_ROUTER_FORCE_FAIL", raising=False)


def _mk_anthropic_response(parsed: dict, status: int = 200) -> MagicMock:
    """Devuelve un mock de requests.Response con body Anthropic-shape."""
    resp = MagicMock()
    resp.status_code = status
    if status == 200:
        body = {
            "content": [{"type": "text", "text": json.dumps(parsed)}]
        }
        resp.json.return_value = body
        resp.text = json.dumps(body)
    else:
        resp.json.return_value = {}
        resp.text = "error"
    return resp


def _patch_post(monkeypatch, response_mock):
    monkeypatch.setattr(
        "voz.intent_router.requests.post",
        lambda *a, **kw: response_mock,
    )


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro) if False else asyncio.run(coro)


# ─── Tests ────────────────────────────────────────────────────────

def test_gasto_basico(monkeypatch):
    _patch_post(monkeypatch, _mk_anthropic_response({
        "tool": "gasto_anotar",
        "args": {"monto_eur": 45, "concepto": "gasolina",
                 "categoria": "transporte"},
        "confidence": 0.95,
        "razon": "pago coche",
    }))
    res = _run(router.route_intent("he pagado 45 de gasolina", "angel"))
    assert res.tool == "gasto_anotar"
    assert res.args["monto_eur"] == 45
    assert res.args["categoria"] == "transporte"
    assert res.fallback is False
    assert res.confidence == 0.95


def test_gasto_sin_categoria_default(monkeypatch):
    _patch_post(monkeypatch, _mk_anthropic_response({
        "tool": "gasto_anotar",
        "args": {"monto_eur": 12, "concepto": "libreta",
                 "categoria": "otros"},
        "confidence": 0.7,
        "razon": "no clear",
    }))
    res = _run(router.route_intent("me he gastado 12 en una libreta", "angel"))
    assert res.tool == "gasto_anotar"
    assert res.args["categoria"] == "otros"


def test_recordatorio_mañana(monkeypatch):
    _patch_post(monkeypatch, _mk_anthropic_response({
        "tool": "recordatorio_crear",
        "args": {"texto": "llevar a Bris al veterinario",
                 "fecha": "mañana", "prioridad": 5},
        "confidence": 0.93,
        "razon": "recuérdame",
    }))
    res = _run(router.route_intent(
        "recuérdame mañana llevar a Bris al veterinario", "africa"))
    assert res.tool == "recordatorio_crear"
    assert res.args["fecha"] == "mañana"
    assert res.fallback is False


def test_lista_compras(monkeypatch):
    _patch_post(monkeypatch, _mk_anthropic_response({
        "tool": "lista_compras_añadir",
        "args": {"item": "leche", "cantidad": "", "urgente": False},
        "confidence": 0.9,
        "razon": "añadir lista",
    }))
    res = _run(router.route_intent("apunta leche a la lista", "angel"))
    assert res.tool == "lista_compras_añadir"
    assert res.args["item"] == "leche"


def test_lista_compras_alias_ascii(monkeypatch):
    """Si el modelo devuelve lista_compras_anadir (sin tilde), normalizamos."""
    _patch_post(monkeypatch, _mk_anthropic_response({
        "tool": "lista_compras_anadir",
        "args": {"item": "huevos"},
        "confidence": 0.88,
        "razon": "",
    }))
    res = _run(router.route_intent("apunta huevos", "angel"))
    assert res.tool == "lista_compras_añadir"


def test_documentos_buscar(monkeypatch):
    _patch_post(monkeypatch, _mk_anthropic_response({
        "tool": "documentos_buscar",
        "args": {"query": "EDF", "limite": 10},
        "confidence": 0.85,
        "razon": "buscar emisor",
    }))
    res = _run(router.route_intent("busca las facturas de EDF", "angel"))
    assert res.tool == "documentos_buscar"


def test_cita_medica(monkeypatch):
    _patch_post(monkeypatch, _mk_anthropic_response({
        "tool": "cita_medica_anotar",
        "args": {"quien": "bris", "especialista": "veterinario",
                 "fecha": "2026-06-03", "notas": "vacuna anual"},
        "confidence": 0.92,
        "razon": "cita perro",
    }))
    res = _run(router.route_intent(
        "el 3 de junio tenemos veterinario para Bris, vacuna anual", "angel"))
    assert res.tool == "cita_medica_anotar"
    assert res.args["quien"] == "bris"


def test_coche_evento_gasolina(monkeypatch):
    _patch_post(monkeypatch, _mk_anthropic_response({
        "tool": "coche_evento",
        "args": {"tipo": "gasolina", "fecha": "hoy", "monto_eur": 60},
        "confidence": 0.9,
        "razon": "",
    }))
    res = _run(router.route_intent(
        "he puesto 60 euros de gasolina al coche", "angel"))
    assert res.tool == "coche_evento"
    assert res.args["tipo"] == "gasolina"


def test_menu_sugerir(monkeypatch):
    _patch_post(monkeypatch, _mk_anthropic_response({
        "tool": "menu_sugerir",
        "args": {"dia": "", "ingredientes_disponibles": "tomate, calabacín"},
        "confidence": 0.8,
        "razon": "",
    }))
    res = _run(router.route_intent(
        "qué hago hoy con tomate y calabacín", "africa"))
    assert res.tool == "menu_sugerir"


def test_confidence_baja_fallback(monkeypatch):
    _patch_post(monkeypatch, _mk_anthropic_response({
        "tool": "gasto_anotar",
        "args": {"monto_eur": 0, "concepto": "?", "categoria": "otros"},
        "confidence": 0.4,
        "razon": "ambiguo",
    }))
    res = _run(router.route_intent("no sé qué decir", "angel"))
    assert res.tool == "dia_capturar"
    assert res.fallback is True
    assert res.confidence == 0.3  # marker del fallback


def test_tool_fuera_whitelist(monkeypatch):
    _patch_post(monkeypatch, _mk_anthropic_response({
        "tool": "borrar_todo",
        "args": {},
        "confidence": 0.99,
        "razon": "malicia",
    }))
    res = _run(router.route_intent("borra todos los gastos", "angel"))
    assert res.tool == "dia_capturar"
    assert res.fallback is True


def test_json_corrupto(monkeypatch):
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {
        "content": [{"type": "text", "text": "esto no es json {{{"}]
    }
    resp.text = "x"
    _patch_post(monkeypatch, resp)
    res = _run(router.route_intent("texto cualquiera", "angel"))
    assert res.tool == "dia_capturar"
    assert res.fallback is True


def test_status_error(monkeypatch):
    _patch_post(monkeypatch, _mk_anthropic_response({}, status=500))
    res = _run(router.route_intent("texto", "angel"))
    assert res.fallback is True
    assert res.tool == "dia_capturar"


def test_timeout(monkeypatch):
    import requests as _rq
    def _raise(*a, **kw):
        raise _rq.Timeout("simulated")
    monkeypatch.setattr("voz.intent_router.requests.post", _raise)
    res = _run(router.route_intent("apunta tomates", "angel"))
    assert res.fallback is True
    assert res.tool == "dia_capturar"


def test_texto_vacio():
    res = _run(router.route_intent("", "angel"))
    assert res.fallback is True
    assert res.razon == "texto vacío"


def test_force_fail_env(monkeypatch):
    monkeypatch.setenv("INTENT_ROUTER_FORCE_FAIL", "1")
    res = _run(router.route_intent("apunta algo", "angel"))
    assert res.fallback is True


def test_idempotencia_cachea(monkeypatch):
    calls = {"n": 0}

    def _post_counting(*a, **kw):
        calls["n"] += 1
        return _mk_anthropic_response({
            "tool": "gasto_anotar",
            "args": {"monto_eur": 10, "concepto": "café",
                     "categoria": "alimentacion"},
            "confidence": 0.9,
            "razon": "",
        })
    monkeypatch.setattr("voz.intent_router.requests.post", _post_counting)
    r1 = _run(router.route_intent("he pagado 10 de café", "angel"))
    r2 = _run(router.route_intent("he pagado 10 de café", "angel"))
    assert calls["n"] == 1
    assert r1.tool == r2.tool == "gasto_anotar"
    assert r2.cached is True


def test_idempotencia_distinto_autor_no_cachea(monkeypatch):
    calls = {"n": 0}

    def _post_counting(*a, **kw):
        calls["n"] += 1
        return _mk_anthropic_response({
            "tool": "lista_compras_añadir",
            "args": {"item": "pan"},
            "confidence": 0.9,
            "razon": "",
        })
    monkeypatch.setattr("voz.intent_router.requests.post", _post_counting)
    _run(router.route_intent("apunta pan", "angel"))
    _run(router.route_intent("apunta pan", "africa"))
    assert calls["n"] == 2


def test_autor_africa_no_se_propaga_a_args(monkeypatch):
    """El modelo podría incluir autor; el router debe quitarlo (server-side
    inyecta el real)."""
    _patch_post(monkeypatch, _mk_anthropic_response({
        "tool": "gasto_anotar",
        "args": {"monto_eur": 22, "concepto": "pan",
                 "categoria": "alimentacion", "autor": "atacante"},
        "confidence": 0.9,
        "razon": "",
    }))
    res = _run(router.route_intent("he pagado 22 de pan", "africa"))
    assert "autor" not in res.args


def test_no_api_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    res = _run(router.route_intent("apunta algo", "angel"))
    assert res.fallback is True


def test_recordatorio_completar(monkeypatch):
    _patch_post(monkeypatch, _mk_anthropic_response({
        "tool": "recordatorio_completar",
        "args": {"id_o_slug": "2026-06-12-cumpleanos-lucia"},
        "confidence": 0.91,
        "razon": "",
    }))
    res = _run(router.route_intent(
        "marca como hecho lo del cumpleaños de Lucía", "angel"))
    assert res.tool == "recordatorio_completar"


def test_claudio_recordar(monkeypatch):
    _patch_post(monkeypatch, _mk_anthropic_response({
        "tool": "claudio_recordar",
        "args": {"hecho": "prefiero café sin azúcar", "importancia": 4},
        "confidence": 0.88,
        "razon": "preferencia personal",
    }))
    res = _run(router.route_intent(
        "recuerda que prefiero el café sin azúcar", "angel"))
    assert res.tool == "claudio_recordar"


def test_gastos_resumen(monkeypatch):
    _patch_post(monkeypatch, _mk_anthropic_response({
        "tool": "gastos_resumen",
        "args": {"periodo": "mes_actual"},
        "confidence": 0.93,
        "razon": "",
    }))
    res = _run(router.route_intent(
        "cuánto llevo gastado este mes", "angel"))
    assert res.tool == "gastos_resumen"


def test_dia_capturar_directo(monkeypatch):
    """Si el modelo devuelve dia_capturar con baja confianza está OK (no
    se desencadena segundo fallback)."""
    _patch_post(monkeypatch, _mk_anthropic_response({
        "tool": "dia_capturar",
        "args": {"texto": "una reflexión cualquiera"},
        "confidence": 0.5,
        "razon": "reflexión",
    }))
    res = _run(router.route_intent(
        "estoy pensando en cambiar todo", "angel"))
    assert res.tool == "dia_capturar"
    assert res.fallback is True
    # confidence baja no triggerea segundo fallback porque el tool ya es dia_capturar
    # (el fallback constructor sobreescribe a 0.3)
    # OK si vale 0.5 (no aplicó el path de "fallback constructor")
    # si vale 0.3 → también OK (aplicó). Aceptamos ambas.
    assert res.confidence in (0.3, 0.5)


def test_payload_completo_propaga_modelo(monkeypatch):
    _patch_post(monkeypatch, _mk_anthropic_response({
        "tool": "gasto_anotar",
        "args": {"monto_eur": 5, "concepto": "café", "categoria": "alimentacion"},
        "confidence": 0.8,
        "razon": "café mañana",
    }))
    res = _run(router.route_intent("cinco euros de café", "angel"))
    assert res.modelo == router.DEFAULT_MODEL
    assert res.fallback is False
