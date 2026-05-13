"""T053 — Tests de contrato de dia_buscar."""
from __future__ import annotations

from datetime import date

import pytest

from voz.buscar import dia_buscar_impl
from voz.vault_io import Nota, escribir_nota


def _seed_nota(ts: str, texto: str, etiqueta: str = "nosvers", autor: str = "angel") -> None:
    escribir_nota(Nota(
        ts=ts, autor=autor, etiqueta=etiqueta, origen="texto_directo",
        audio=None, clasificador_confianza=1.0, clasificador_modelo="manual",
        texto=texto,
    ))


def test_buscar_con_match(vault_temporal):
    _seed_nota("2026-05-10T09:00:00+02:00", "Pedir fotos a África para Instagram")
    _seed_nota("2026-05-11T10:00:00+02:00", "Sembrar tomates en el potager")

    res = dia_buscar_impl(query="fotos")
    assert res["ok"] is True
    assert len(res["resultados"]) == 1
    assert "fotos" in res["resultados"][0].get("texto", "").lower() or \
           "fotos" in res["resultados"][0].get("fragmento", "").lower()


def test_buscar_sin_match(vault_temporal):
    _seed_nota("2026-05-10T09:00:00+02:00", "Algo cualquiera")
    res = dia_buscar_impl(query="xyz-no-existe")
    assert res["ok"] is True
    assert res["resultados"] == [] or len(res["resultados"]) == 0


def test_buscar_con_rango_fechas(vault_temporal):
    _seed_nota("2026-04-01T09:00:00+02:00", "Marzo abril nota")
    _seed_nota("2026-05-15T09:00:00+02:00", "Mayo nota con fotos")

    # Solo mayo
    res = dia_buscar_impl(query="nota", desde="2026-05-01", hasta="2026-05-31")
    assert res["ok"] is True
    fechas = {r.get("fecha") for r in res["resultados"]}
    assert "2026-04-01" not in fechas


def test_buscar_filtro_etiqueta(vault_temporal):
    _seed_nota("2026-05-10T09:00:00+02:00", "nota familiar", etiqueta="familia")
    _seed_nota("2026-05-10T10:00:00+02:00", "nota de trabajo", etiqueta="trabajo")

    res = dia_buscar_impl(query="nota", etiqueta="familia")
    assert res["ok"] is True
    for r in res["resultados"]:
        assert r.get("etiqueta") == "familia"


def test_buscar_normalizacion_diacriticos(vault_temporal):
    _seed_nota("2026-05-10T09:00:00+02:00", "Pedir fotos a Africa sin tilde")
    _seed_nota("2026-05-11T09:00:00+02:00", "Para África con tilde sí")

    # Buscar sin tilde debe encontrar ambas
    res = dia_buscar_impl(query="africa")
    assert res["ok"] is True
    assert len(res["resultados"]) == 2


def test_buscar_query_vacia(vault_temporal):
    _seed_nota("2026-05-10T09:00:00+02:00", "algo")
    res = dia_buscar_impl(query="")
    # Comportamiento contractual: query vacía debe dar error o resultados vacíos
    assert (res["ok"] is False) or (res.get("resultados") == [])


def test_buscar_limite_aplicado(vault_temporal):
    for i in range(15):
        _seed_nota(f"2026-05-10T{9+i:02d}:00:00+02:00", f"nota numero {i}")
    res = dia_buscar_impl(query="nota", limite=5)
    assert res["ok"] is True
    assert len(res["resultados"]) <= 5


def test_buscar_devuelve_autor_en_resultados(vault_temporal):
    """BRIEF §14: cada resultado lleva campo `autor`."""
    _seed_nota("2026-05-13T09:00:00+02:00", "potager esta semana", autor="africa")
    res = dia_buscar_impl(query="potager")
    assert res["ok"] is True
    assert len(res["resultados"]) == 1
    assert res["resultados"][0]["autor"] == "africa"


def test_buscar_filtro_autor_solo_africa(vault_temporal):
    """Filtro por autor='africa' excluye notas de Angel."""
    _seed_nota("2026-05-13T08:00:00+02:00", "reunion bordeaux", autor="angel", etiqueta="trabajo")
    _seed_nota("2026-05-13T09:00:00+02:00", "lecho 3 cosecha", autor="africa", etiqueta="nosvers")
    _seed_nota("2026-05-13T10:00:00+02:00", "comprar bombillas", autor="angel", etiqueta="trabajo")

    res = dia_buscar_impl(query="o", autor="africa")  # 'o' matchea ambas pero filtra por autor
    assert res["ok"] is True
    autores = {r["autor"] for r in res["resultados"]}
    assert autores == {"africa"}
    assert res["filtro_autor"] == "africa"


def test_buscar_filtro_autor_default_devuelve_ambos(vault_temporal):
    """Sin filtro autor explícito (o vacío), devuelve notas de ambos."""
    _seed_nota("2026-05-13T08:00:00+02:00", "tema comun A", autor="angel")
    _seed_nota("2026-05-13T09:00:00+02:00", "tema comun F", autor="africa")
    res = dia_buscar_impl(query="comun")
    assert res["ok"] is True
    assert len(res["resultados"]) == 2
    assert {r["autor"] for r in res["resultados"]} == {"angel", "africa"}
    assert res["filtro_autor"] is None


def test_buscar_filtro_autor_invalido_se_ignora(vault_temporal):
    """Autor desconocido se ignora silenciosamente (filtro vacío)."""
    _seed_nota("2026-05-13T09:00:00+02:00", "una nota", autor="angel")
    res = dia_buscar_impl(query="nota", autor="invalido")
    assert res["ok"] is True
    assert res["filtro_autor"] is None
    assert len(res["resultados"]) == 1
