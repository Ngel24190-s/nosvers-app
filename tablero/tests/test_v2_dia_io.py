"""Tests para tablero.v2.dia_io — IO a nivel de entrada en archivos-por-día."""
from __future__ import annotations

from datetime import date
from pathlib import Path

from tablero.v2.dia_io import (
    Entrada,
    buscar_entrada,
    escribir_dia,
    leer_dia,
    parsear_dia,
    serializar_dia,
)


_FIXTURE_DIA = """# Diario — 2026-05-13

---
ts: '2026-05-13T05:40:39.288550+00:00'
autor: angel
etiqueta: otro
origen: otro
audio: null
clasificador_confianza: 0.85
clasificador_modelo: claude-haiku-4-5
---

Primera entrada — test post-restart.

---
ts: '2026-05-13T10:15:22.111000+00:00'
autor: africa
etiqueta: nosvers
origen: otro
audio: null
clasificador_confianza: 0.92
clasificador_modelo: claude-haiku-4-5
modified_at: '2026-05-13T11:00:00+00:00'
---

Segunda entrada con modified_at — ya fue editada.
"""


def test_parsear_dia_dos_entradas():
    entradas = parsear_dia(_FIXTURE_DIA)
    assert len(entradas) == 2
    assert entradas[0].ts == "2026-05-13T05:40:39.288550+00:00"
    assert entradas[0].autor == "angel"
    assert entradas[0].etiqueta == "otro"
    assert "Primera entrada" in entradas[0].texto
    assert entradas[0].modified_at is None
    assert entradas[1].modified_at == "2026-05-13T11:00:00+00:00"


def test_parsear_dia_concurrency_token_usa_modified_at_si_existe():
    entradas = parsear_dia(_FIXTURE_DIA)
    assert entradas[0].concurrency_token == entradas[0].ts
    assert entradas[1].concurrency_token == "2026-05-13T11:00:00+00:00"


def test_parsear_dia_vacio():
    assert parsear_dia("") == []
    assert parsear_dia("\n\n") == []


def test_serializar_dia_roundtrip():
    entradas = parsear_dia(_FIXTURE_DIA)
    contenido = serializar_dia(date(2026, 5, 13), entradas)
    entradas2 = parsear_dia(contenido)
    assert len(entradas2) == 2
    # Frontmatter completo preservado
    assert entradas[0].meta == entradas2[0].meta
    assert entradas[0].texto == entradas2[0].texto
    assert entradas[1].meta == entradas2[1].meta
    # modified_at preservado en el roundtrip
    assert entradas2[1].modified_at == "2026-05-13T11:00:00+00:00"


def test_serializar_dia_preserva_campos_extra():
    """Si añadimos un campo nuevo al frontmatter (archived_at p.ej.), debe sobrevivir."""
    entrada = Entrada(
        ts="2026-05-13T05:00:00+00:00",
        meta={
            "ts": "2026-05-13T05:00:00+00:00",
            "autor": "angel",
            "etiqueta": "idea",
            "archived_at": "2026-05-14T10:00:00+00:00",
            "archive_reason": "duplicado",
        },
        texto="cuerpo",
    )
    contenido = serializar_dia(date(2026, 5, 13), [entrada])
    entradas2 = parsear_dia(contenido)
    assert entradas2[0].archived_at == "2026-05-14T10:00:00+00:00"
    assert entradas2[0].meta["archive_reason"] == "duplicado"


def test_escribir_y_leer_dia(tmp_path: Path):
    vault = tmp_path / "knowledge_base"
    (vault / "dia").mkdir(parents=True)
    entrada = Entrada(
        ts="2026-05-13T05:00:00+00:00",
        meta={"ts": "2026-05-13T05:00:00+00:00", "autor": "angel", "etiqueta": "idea", "origen": "otro"},
        texto="cuerpo de prueba",
    )
    escribir_dia(vault, date(2026, 5, 13), [entrada])
    entradas = leer_dia(vault, date(2026, 5, 13))
    assert len(entradas) == 1
    assert entradas[0].ts == entrada.ts
    assert entradas[0].texto == "cuerpo de prueba"


def test_leer_dia_inexistente(tmp_path: Path):
    assert leer_dia(tmp_path, date(2026, 1, 1)) == []


def test_buscar_entrada_match():
    entradas = parsear_dia(_FIXTURE_DIA)
    e = buscar_entrada(entradas, "2026-05-13T10:15:22.111000+00:00")
    assert e is not None
    assert e.autor == "africa"


def test_buscar_entrada_no_match():
    entradas = parsear_dia(_FIXTURE_DIA)
    assert buscar_entrada(entradas, "ghost-ts") is None


def test_serializar_ordena_por_ts(tmp_path: Path):
    e1 = Entrada(ts="2026-05-13T10:00:00+00:00", meta={"ts": "2026-05-13T10:00:00+00:00", "autor": "angel"}, texto="tarde")
    e2 = Entrada(ts="2026-05-13T05:00:00+00:00", meta={"ts": "2026-05-13T05:00:00+00:00", "autor": "angel"}, texto="temprano")
    contenido = serializar_dia(date(2026, 5, 13), [e1, e2])
    # Debe aparecer "temprano" antes que "tarde"
    pos_temprano = contenido.index("temprano")
    pos_tarde = contenido.index("tarde")
    assert pos_temprano < pos_tarde
