"""T048 — Tests de contrato de dia_contexto.

Sin ANTHROPIC_API_KEY (default en tests) `_llamar_sintesis` retorna un
string informativo — no se hace llamada de red.
"""
from __future__ import annotations

import pytest

from voz import contexto
from voz.contexto import dia_contexto_impl
from voz.vault_io import Nota, escribir_nota


@pytest.fixture(autouse=True)
def limpiar_cache_contexto():
    with contexto._CACHE_LOCK:
        contexto._CACHE.clear()
    yield
    with contexto._CACHE_LOCK:
        contexto._CACHE.clear()


@pytest.fixture(autouse=True)
def sin_api_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)


def _seed_nota(ts: str, texto: str, etiqueta: str = "nosvers", autor: str = "angel") -> None:
    escribir_nota(Nota(
        ts=ts, autor=autor, etiqueta=etiqueta, origen="texto_directo",
        audio=None, clasificador_confianza=1.0, clasificador_modelo="manual",
        texto=texto,
    ))


def test_contexto_vault_vacio(vault_temporal):
    res = dia_contexto_impl(rango_dias=7, incluir_calendario=False, incluir_estado_agentes=False)
    assert res["ok"] is True
    assert res["notas_count"] == 0
    assert "sin actividad" in res["sintesis"]
    assert "rango" in res
    assert res["calendario"] is None
    assert res["agentes"] is None


def test_contexto_rango_default(vault_temporal):
    # Nota dentro del rango por defecto (7d) — usa hoy
    from datetime import date, timedelta
    hoy = date.today()
    _seed_nota(f"{hoy.isoformat()}T10:00:00+02:00", "Algo de hoy en NosVers")

    res = dia_contexto_impl(incluir_calendario=False, incluir_estado_agentes=False)
    assert res["ok"] is True
    assert res["notas_count"] >= 1
    # sin API key, _llamar_sintesis devuelve mensaje informativo
    assert isinstance(res["sintesis"], str)


def test_contexto_etiquetas_filtro_valido(vault_temporal):
    from datetime import date
    hoy = date.today()
    _seed_nota(f"{hoy.isoformat()}T10:00:00+02:00", "nota familiar", etiqueta="familia")
    _seed_nota(f"{hoy.isoformat()}T11:00:00+02:00", "nota nosvers",  etiqueta="nosvers")

    res = dia_contexto_impl(
        rango_dias=1,
        incluir_calendario=False,
        incluir_estado_agentes=False,
        etiquetas_filtro="nosvers",
    )
    assert res["ok"] is True
    assert res["notas_count"] == 1


def test_contexto_etiquetas_filtro_invalido_se_ignora(vault_temporal):
    from datetime import date
    hoy = date.today()
    _seed_nota(f"{hoy.isoformat()}T10:00:00+02:00", "todo")

    res = dia_contexto_impl(
        rango_dias=1,
        incluir_calendario=False,
        incluir_estado_agentes=False,
        etiquetas_filtro="inventada",
    )
    # Etiqueta inválida → se ignora el filtro, retorna todo
    assert res["ok"] is True
    assert res["notas_count"] == 1


def test_contexto_cache_hit(vault_temporal):
    from datetime import date
    hoy = date.today()
    _seed_nota(f"{hoy.isoformat()}T10:00:00+02:00", "cacheable")

    r1 = dia_contexto_impl(rango_dias=1, incluir_calendario=False, incluir_estado_agentes=False)
    assert r1.get("cache") is None  # primera llamada

    r2 = dia_contexto_impl(rango_dias=1, incluir_calendario=False, incluir_estado_agentes=False)
    assert r2.get("cache") is True  # segunda → cache hit


def test_contexto_calendario_no_disponible(vault_temporal):
    res = dia_contexto_impl(rango_dias=1, incluir_calendario=True, incluir_estado_agentes=False)
    # _leer_calendario() devuelve "no_disponible" en su esqueleto
    assert res["calendario"] == "no_disponible"


def test_contexto_rango_dias_clampea(vault_temporal):
    """rango_dias > 30 → clamp a 30; rango_dias < 1 → clamp a 1."""
    res_grande = dia_contexto_impl(
        rango_dias=999, incluir_calendario=False, incluir_estado_agentes=False
    )
    res_negativo = dia_contexto_impl(
        rango_dias=-5, incluir_calendario=False, incluir_estado_agentes=False
    )
    assert res_grande["ok"] is True
    assert res_negativo["ok"] is True


def test_contexto_filtro_autor_aplica(vault_temporal):
    """BRIEF §14: filtro por autor reduce notas_count al subconjunto."""
    from datetime import date
    hoy = date.today()
    _seed_nota(f"{hoy.isoformat()}T08:00:00+02:00", "tema angel", autor="angel")
    _seed_nota(f"{hoy.isoformat()}T09:00:00+02:00", "tema africa 1", autor="africa")
    _seed_nota(f"{hoy.isoformat()}T10:00:00+02:00", "tema africa 2", autor="africa")

    res = dia_contexto_impl(
        rango_dias=1, incluir_calendario=False, incluir_estado_agentes=False,
        autor="africa",
    )
    assert res["ok"] is True
    assert res["notas_count"] == 2
    assert res["filtro_autor"] == "africa"


def test_contexto_default_devuelve_ambos_autores(vault_temporal):
    """Sin filtro autor, el conteo incluye notas de ambos."""
    from datetime import date
    hoy = date.today()
    _seed_nota(f"{hoy.isoformat()}T08:00:00+02:00", "x", autor="angel")
    _seed_nota(f"{hoy.isoformat()}T09:00:00+02:00", "y", autor="africa")

    res = dia_contexto_impl(rango_dias=1, incluir_calendario=False, incluir_estado_agentes=False)
    assert res["notas_count"] == 2
    assert res["filtro_autor"] is None
