"""Tests para tablero.v2.atomic_write (T006 / D-013)."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from tablero.v2.atomic_write import escribir_atomico, mover_atomico


def test_escribir_nuevo_archivo(tmp_path: Path):
    dst = tmp_path / "nuevo.md"
    escribir_atomico(dst, "hola")
    assert dst.read_text() == "hola"


def test_escribir_sobrescribe(tmp_path: Path):
    dst = tmp_path / "x.md"
    dst.write_text("viejo")
    escribir_atomico(dst, "nuevo")
    assert dst.read_text() == "nuevo"


def test_escribir_bytes(tmp_path: Path):
    dst = tmp_path / "raw.md"
    escribir_atomico(dst, b"bytes-content")
    assert dst.read_bytes() == b"bytes-content"


def test_escribir_crea_carpeta_padre(tmp_path: Path):
    dst = tmp_path / "sub" / "carpeta" / "archivo.md"
    escribir_atomico(dst, "ok")
    assert dst.exists() and dst.read_text() == "ok"


def test_escribir_limpia_tmp_si_falla(tmp_path: Path, monkeypatch):
    dst = tmp_path / "x.md"
    dst.write_text("original")

    # Simular fallo en os.replace
    def fake_replace(src, dst):
        raise OSError("simulated")

    monkeypatch.setattr(os, "replace", fake_replace)
    with pytest.raises(OSError):
        escribir_atomico(dst, "nuevo")

    # El destino conserva lo original
    assert dst.read_text() == "original"
    # No deben quedar tmp files con nuestro patrón
    tmps = list(tmp_path.glob(".x.md.tmp.*"))
    assert tmps == []


def test_mover_atomico_simple(tmp_path: Path):
    src = tmp_path / "a.md"
    dst = tmp_path / "subdir" / "b.md"
    src.write_text("data")
    mover_atomico(src, dst)
    assert not src.exists()
    assert dst.read_text() == "data"


def test_mover_atomico_dst_existe_falla(tmp_path: Path):
    src = tmp_path / "a.md"
    dst = tmp_path / "b.md"
    src.write_text("a")
    dst.write_text("b")
    with pytest.raises(FileExistsError):
        mover_atomico(src, dst)
    assert src.exists() and dst.read_text() == "b"


def test_mover_atomico_src_inexistente(tmp_path: Path):
    src = tmp_path / "ghost.md"
    dst = tmp_path / "anywhere.md"
    with pytest.raises(FileNotFoundError):
        mover_atomico(src, dst)
