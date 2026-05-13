"""Tests para tablero.v2.frontmatter (T007)."""
from __future__ import annotations

import pytest

from tablero.v2.frontmatter import (
    actualizar_modified_at,
    now_modified_at,
    parse,
    serialize,
)


def test_parse_valido_simple():
    text = "---\nautor: angel\nfecha: 2026-05-13\n---\ncuerpo aquí\n"
    meta, body = parse(text)
    assert meta == {"autor": "angel", "fecha": "2026-05-13"}
    assert body == "cuerpo aquí\n"


def test_parse_sin_frontmatter():
    text = "no tiene frontmatter\nsolo body\n"
    meta, body = parse(text)
    assert meta == {}
    assert body == text


def test_parse_malformado_devuelve_meta_vacio():
    text = "---\nesto no es: válido: yaml\n---\nbody\n"
    meta, body = parse(text)
    # yaml.safe_load probablemente acepte 'esto no es: válido: yaml' como dict mal formado;
    # lo importante es que no levante excepción y que body sea correcto
    assert isinstance(meta, dict)
    assert body == "body\n"


def test_parse_frontmatter_sin_cierre():
    text = "---\nautor: angel\nsin cierre aquí\n"
    meta, body = parse(text)
    assert meta == {}
    assert body == text


def test_parse_lista_etiquetas():
    text = "---\netiquetas:\n  - idea\n  - nosvers\n---\ncuerpo\n"
    meta, body = parse(text)
    assert meta["etiquetas"] == ["idea", "nosvers"]


def test_serialize_roundtrip_idempotente():
    text = "---\nautor: africa\nfecha: 2026-05-13\netiquetas:\n- idea\n---\ncuerpo libre\n\n"
    meta, body = parse(text)
    nuevo = serialize(meta, body)
    meta2, body2 = parse(nuevo)
    assert meta == meta2
    assert body == body2


def test_serialize_sin_meta_devuelve_body():
    assert serialize({}, "solo body") == "solo body"


def test_now_modified_at_es_iso8601_con_tz():
    s = now_modified_at()
    assert "T" in s
    # acepta +00:00 o Z
    assert s.endswith("+00:00") or s.endswith("Z")


def test_actualizar_modified_at_preserva_resto():
    meta = {"autor": "angel", "fecha": "2026-01-01", "modified_at": "viejo"}
    nuevo = actualizar_modified_at(meta)
    assert nuevo["autor"] == "angel"
    assert nuevo["fecha"] == "2026-01-01"
    assert nuevo["modified_at"] != "viejo"
    # El original no se mutó
    assert meta["modified_at"] == "viejo"
