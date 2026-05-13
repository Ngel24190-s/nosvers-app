"""Tests para tablero.v2.slug_resolver (T008 / D-002, D-012)."""
from __future__ import annotations

from pathlib import Path

from tablero.v2.slug_resolver import (
    construir_indice_slug,
    normalizar_slug,
    resolver,
    slug_de_archivo,
)


def test_slug_de_archivo_quita_prefijo_fecha():
    assert slug_de_archivo(Path("dia/2026-05-13-lombrithé.md")) == "lombrithé"


def test_slug_de_archivo_sin_prefijo():
    assert slug_de_archivo(Path("proyectos/tienda.md")) == "tienda"


def test_normalizar_slug_lowercase():
    assert normalizar_slug("Lombrithé") == "lombrithe"


def test_normalizar_slug_quita_acentos():
    assert normalizar_slug("café") == "cafe"
    assert normalizar_slug("CAFÉ") == "cafe"


def test_construir_indice_basico(tmp_path: Path):
    (tmp_path / "dia").mkdir()
    (tmp_path / "dia" / "2026-05-13-lombrithé.md").write_text("contenido", encoding="utf-8")
    (tmp_path / "dia" / "2026-05-14-otra.md").write_text("x", encoding="utf-8")
    indice = construir_indice_slug(tmp_path)
    assert "lombrithe" in indice
    assert "otra" in indice


def test_construir_indice_excluye_archivo(tmp_path: Path):
    (tmp_path / "dia").mkdir()
    (tmp_path / "dia" / "viva.md").write_text("x", encoding="utf-8")
    (tmp_path / "dia" / "archivo").mkdir()
    (tmp_path / "dia" / "archivo" / "muerta.md").write_text("x", encoding="utf-8")
    indice = construir_indice_slug(tmp_path)
    assert "viva" in indice
    assert "muerta" not in indice


def test_resolver_unico_match(tmp_path: Path):
    (tmp_path / "x.md").write_text("x", encoding="utf-8")
    indice = construir_indice_slug(tmp_path)
    path, n = resolver("x", indice)
    assert path == tmp_path / "x.md"
    assert n == 1


def test_resolver_insensible_a_acentos(tmp_path: Path):
    archivo = tmp_path / "café.md"
    archivo.write_text("x", encoding="utf-8")
    indice = construir_indice_slug(tmp_path)
    path, n = resolver("CAFE", indice)
    assert path == archivo
    assert n == 1


def test_resolver_prefijo_fecha_se_ignora(tmp_path: Path):
    (tmp_path / "dia").mkdir()
    archivo = tmp_path / "dia" / "2026-01-01-lombrithé.md"
    archivo.write_text("x", encoding="utf-8")
    indice = construir_indice_slug(tmp_path)
    path, n = resolver("lombrithé", indice)
    assert path == archivo
    assert n == 1


def test_resolver_homonimos_devuelve_mas_reciente(tmp_path: Path):
    import time
    viejo = tmp_path / "viejo.md"
    viejo.write_text("v", encoding="utf-8")
    viejo_path_misma_slug = tmp_path / "subcarpeta"
    viejo_path_misma_slug.mkdir()
    nuevo = viejo_path_misma_slug / "viejo.md"
    time.sleep(0.05)  # asegurar mtime distinto
    nuevo.write_text("n", encoding="utf-8")

    indice = construir_indice_slug(tmp_path)
    path, n = resolver("viejo", indice)
    assert path == nuevo
    assert n == 2


def test_resolver_sin_match(tmp_path: Path):
    indice = construir_indice_slug(tmp_path)
    path, n = resolver("inexistente", indice)
    assert path is None
    assert n == 0
