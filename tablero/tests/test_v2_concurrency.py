"""Tests para tablero.v2.concurrency (T009 / D-003)."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock

import pytest

from tablero.v2.concurrency import (
    StaleModifiedAt,
    leer_modified_at,
    verificar_if_match,
)


def _archivo_con_mod(path: Path, mod_at: str) -> None:
    path.write_text(f"---\nmodified_at: {mod_at}\n---\nbody\n", encoding="utf-8")


def test_leer_modified_at_archivo_existente(tmp_path: Path):
    f = tmp_path / "x.md"
    _archivo_con_mod(f, "2026-05-13T10:00:00+00:00")
    assert leer_modified_at(f) == "2026-05-13T10:00:00+00:00"


def test_leer_modified_at_archivo_inexistente(tmp_path: Path):
    assert leer_modified_at(tmp_path / "ghost.md") is None


def test_leer_modified_at_sin_frontmatter(tmp_path: Path):
    f = tmp_path / "x.md"
    f.write_text("solo body", encoding="utf-8")
    assert leer_modified_at(f) is None


def test_verificar_if_match_ok(tmp_path: Path):
    f = tmp_path / "x.md"
    _archivo_con_mod(f, "2026-05-13T10:00:00+00:00")
    req = Mock()
    req.headers = {"If-Match": "2026-05-13T10:00:00+00:00"}
    # No levanta excepción
    verificar_if_match(req, f)


def test_verificar_if_match_stale(tmp_path: Path):
    f = tmp_path / "x.md"
    _archivo_con_mod(f, "2026-05-13T10:00:00+00:00")
    req = Mock()
    req.headers = {"If-Match": "2026-05-13T09:00:00+00:00"}
    with pytest.raises(StaleModifiedAt) as exc_info:
        verificar_if_match(req, f)
    assert exc_info.value.current == "2026-05-13T10:00:00+00:00"


def test_verificar_if_match_missing_header(tmp_path: Path):
    f = tmp_path / "x.md"
    _archivo_con_mod(f, "2026-05-13T10:00:00+00:00")
    req = Mock()
    req.headers = {}
    with pytest.raises(StaleModifiedAt) as exc_info:
        verificar_if_match(req, f)
    assert exc_info.value.current is None


def test_verificar_if_match_archivo_sin_modified_at(tmp_path: Path):
    """Si el archivo no tiene modified_at, cualquier If-Match es aceptado."""
    f = tmp_path / "x.md"
    f.write_text("---\nautor: angel\n---\nbody\n", encoding="utf-8")
    req = Mock()
    req.headers = {"If-Match": "cualquier-cosa"}
    verificar_if_match(req, f)  # no raise
