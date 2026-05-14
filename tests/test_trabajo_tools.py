"""Tests claudio_tools.trabajo — 10 tools del contexto Trabajo (007).

Aísla el vault con `VAULT_PATH=/tmp/test_007_vault`.
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path

import pytest

VAULT_TEST = Path("/tmp/test_007_vault")
os.environ["VAULT_PATH"] = str(VAULT_TEST)


@pytest.fixture(autouse=True)
def _clean_vault():
    shutil.rmtree(VAULT_TEST, ignore_errors=True)
    VAULT_TEST.mkdir(parents=True, exist_ok=True)
    # Seed equipe yaml mínima
    eq_dir = VAULT_TEST / "trabajo" / "equipe"
    eq_dir.mkdir(parents=True, exist_ok=True)
    (eq_dir / "operateurs.yaml").write_text(
        "operateurs:\n"
        "  - id: angel\n"
        "    nombre: Angel\n"
        "    rol: chef-d-equipe\n"
        "    activo: true\n",
        encoding="utf-8",
    )
    yield
    shutil.rmtree(VAULT_TEST, ignore_errors=True)


def test_chantier_listar_vacio():
    from claudio_tools import trabajo as t
    out = t.chantier_listar("activos")
    assert "Sin chantiers" in out or "0 chantier" in out


def test_chantier_crear_y_listar():
    from claudio_tools import trabajo as t
    msg = t.chantier_crear(
        "Bordeaux Nord", "12 rue x", "Mairie Bordeaux",
        84500, "angel,jose", "2026-05-20", "2026-08-15", "angel",
    )
    assert "Chantier creado" in msg
    out = t.chantier_listar("activos")
    assert "bordeaux-nord" in out


def test_chantier_evento_journal():
    from claudio_tools import trabajo as t
    t.chantier_crear("Chantier X", "rue x", "Cli", 1000, "angel",
                     "2026-01-01", "", "angel")
    out = t.chantier_evento("chantier-x", "avance", "Hecho zona 1", "angel")
    assert "Anotado" in out
    # Verificar journal escrito
    journals = list((VAULT_TEST / "trabajo" / "chantiers" / "chantier-x"
                     / "journal").glob("*.md"))
    assert len(journals) == 1
    assert "Hecho zona 1" in journals[0].read_text(encoding="utf-8")


def test_chantier_evento_no_existe():
    from claudio_tools import trabajo as t
    out = t.chantier_evento("ghost-slug", "avance", "x", "angel")
    assert "no encontrado" in out or "no existe" in out


def test_chantier_estado_snapshot():
    from claudio_tools import trabajo as t
    t.chantier_crear("Chant Z", "rue z", "Cli Z", 500, "angel",
                     "2026-01-01", "2026-02-01", "angel")
    t.chantier_evento("chant-z", "avance", "Avance día 1", "angel")
    out = t.chantier_estado("chant-z")
    assert "Cli Z" in out
    assert "Avance día 1" in out or "avance" in out.lower()


def test_chantier_resolve_fuzzy():
    from claudio_tools import trabajo as t
    t.chantier_crear("Bordeaux Sud", "rue", "Cli", 1, "angel", "2026-01-01", "", "angel")
    # keyword "sud" debe resolver al único match
    out = t.chantier_evento("sud", "journal", "ok", "angel")
    assert "Anotado" in out


def test_equipe_listar():
    from claudio_tools import trabajo as t
    out = t.equipe_listar()
    assert "angel" in out.lower()
    assert "chef" in out.lower()


def test_equipe_anotar():
    from claudio_tools import trabajo as t
    out = t.equipe_anotar("Jose", "Renovation SS3 OK", "2026-05-10")
    assert "formación de jose" in out.lower() or "jose" in out.lower()
    f = VAULT_TEST / "trabajo" / "equipe" / "formations" / "jose" / "2026.md"
    assert f.exists()
    assert "Renovation SS3 OK" in f.read_text(encoding="utf-8")


def test_devis_anotar():
    from claudio_tools import trabajo as t
    out = t.devis_anotar("Mairie Bordeaux", 84500.0, "bordeaux-nord")
    assert "Devis" in out
    f = VAULT_TEST / "trabajo" / "documents" / "devis" / "mairie-bordeaux.md"
    assert f.exists()
    assert "84,500" in f.read_text(encoding="utf-8")


def test_ppsps_crear():
    from claudio_tools import trabajo as t
    out = t.ppsps_crear("bordeaux-nord", "v1", "Observación clave")
    assert "PPSPS creado" in out
    f = VAULT_TEST / "trabajo" / "documents" / "ppsps" / "bordeaux-nord-v1.md"
    assert f.exists()
    text = f.read_text(encoding="utf-8")
    assert "Observación clave" in text
    assert "1. Objet" in text


def test_documento_trabajo_archivar():
    from claudio_tools import trabajo as t
    out = t.documento_trabajo_archivar(
        "certificat", "Certificat de capacité SS3", "bordeaux-nord",
    )
    assert "archivado" in out.lower()
    sub = VAULT_TEST / "trabajo" / "documents" / "certificats"
    matches = list(sub.glob("bordeaux-nord-*.md"))
    assert len(matches) == 1


def test_chantier_documento_listar():
    from claudio_tools import trabajo as t
    t.chantier_crear("Chant Y", "rue", "Cli", 1, "angel", "2026-01-01", "", "angel")
    t.ppsps_crear("chant-y", "v1", "")
    t.devis_anotar("Cli", 100.0, "chant-y")
    out = t.chantier_documento_listar("chant-y", "ppsps")
    assert "chant-y" in out
    assert "ppsps" in out
