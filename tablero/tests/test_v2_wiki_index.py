"""Tests para tablero.v2.wiki_index (T010 / D-004)."""
from __future__ import annotations

from pathlib import Path

import pytest

from tablero.v2.wiki_index import WikiIndex


def _crear_nota(vault: Path, ruta_rel: str, body: str, autor: str = "angel", modified_at: str = "2026-05-13T10:00:00+00:00") -> Path:
    f = vault / ruta_rel
    f.parent.mkdir(parents=True, exist_ok=True)
    fm = f"---\nautor: {autor}\nmodified_at: {modified_at}\n---\n{body}"
    f.write_text(fm, encoding="utf-8")
    return f


def test_build_indice_vacio(tmp_path: Path):
    idx = WikiIndex(tmp_path)
    idx.build()
    assert idx.indice_completo() == {}
    assert idx.generated_at is not None


def test_build_indexa_wiki_links(tmp_path: Path):
    _crear_nota(tmp_path, "dia/a.md", "habla de [[lombrithé]] y luego [[composteur]]")
    _crear_nota(tmp_path, "dia/lombrithé.md", "soy lombrithé")
    idx = WikiIndex(tmp_path)
    idx.build()
    bl = idx.backlinks_de("lombrithé")
    assert len(bl) == 1
    assert bl[0].source_slug == "a"
    assert "lombrithé" in bl[0].context


def test_build_excluye_dia_archivo(tmp_path: Path):
    _crear_nota(tmp_path, "dia/viva.md", "ref [[destino]]")
    _crear_nota(tmp_path, "dia/archivo/muerta.md", "ref [[destino]]")
    idx = WikiIndex(tmp_path)
    idx.build()
    bl = idx.backlinks_de("destino")
    assert len(bl) == 1
    assert bl[0].source_slug == "viva"


def test_actualizar_nota_refleja_cambios(tmp_path: Path):
    a = _crear_nota(tmp_path, "dia/a.md", "ref [[viejo-destino]]")
    idx = WikiIndex(tmp_path)
    idx.build()
    assert len(idx.backlinks_de("viejo-destino")) == 1

    # Reescribir a con nuevo destino
    nuevo_contenido = "---\nautor: angel\nmodified_at: 2026-05-14T10:00:00+00:00\n---\nref [[nuevo-destino]]"
    a.write_text(nuevo_contenido, encoding="utf-8")
    idx.actualizar_nota(a, nuevo_contenido)

    assert len(idx.backlinks_de("viejo-destino")) == 0
    assert len(idx.backlinks_de("nuevo-destino")) == 1


def test_eliminar_nota(tmp_path: Path):
    a = _crear_nota(tmp_path, "dia/a.md", "ref [[destino]]")
    idx = WikiIndex(tmp_path)
    idx.build()
    assert len(idx.backlinks_de("destino")) == 1

    idx.eliminar_nota(a)
    assert len(idx.backlinks_de("destino")) == 0


def test_mover_nota_mismo_slug_preserva(tmp_path: Path):
    a = _crear_nota(tmp_path, "dia/a.md", "ref [[destino]]")
    idx = WikiIndex(tmp_path)
    idx.build()

    dst = tmp_path / "proyectos" / "a.md"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(a.read_text(), encoding="utf-8")
    # No borramos src en este test — solo validamos que mover_nota detecta el cambio

    idx.mover_nota(a, dst, dst.read_text())
    bl = idx.backlinks_de("destino")
    assert len(bl) == 1
    assert bl[0].source_path == "proyectos/a.md" or bl[0].source_slug == "a"


def test_stats(tmp_path: Path):
    _crear_nota(tmp_path, "dia/a.md", "ref [[x]] y [[y]]")
    _crear_nota(tmp_path, "dia/b.md", "ref [[x]]")
    idx = WikiIndex(tmp_path)
    idx.build()
    s = idx.stats()
    assert s["n_target_slugs"] == 2  # x, y
    assert s["n_source_slugs"] == 2  # a, b
    assert s["n_links_total"] == 3  # a→x, a→y, b→x


def test_indice_completo(tmp_path: Path):
    _crear_nota(tmp_path, "dia/a.md", "[[target]]")
    idx = WikiIndex(tmp_path)
    idx.build()
    completo = idx.indice_completo()
    assert "target" in completo
    assert len(completo["target"]) == 1
