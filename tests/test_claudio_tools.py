"""Smoke tests para claudio_tools (proyecto 005).

Cada test usa un VAULT temporal (tmp_path) inyectado via env VAULT_PATH +
monkeypatch del módulo `common`. Verifica que cada tool:
- crea el archivo esperado
- devuelve un string razonable
- no rompe en edge cases típicos (vault vacío, autor inválido)
"""

from __future__ import annotations

import importlib
import os
from datetime import date, timedelta
from pathlib import Path

import pytest


@pytest.fixture
def vault_tmp(tmp_path, monkeypatch):
    """Crea estructura mínima en tmp_path y reinicia los módulos para que
    apunten al nuevo VAULT_PATH."""
    monkeypatch.setenv("VAULT_PATH", str(tmp_path))
    # Subdirs necesarios
    for sub in [
        "claudio/memorias/angel", "claudio/memorias/africa",
        "claudio/memorias/compartido", "claudio/logs",
        "familia/recordatorios", "familia",
        "finanzas/gastos",
        "compras/historico", "compras",
        "menus/recetas", "menus",
        "coche/gastos", "coche",
        "casa",
        "documentos/facturas", "documentos",
        "salud/citas", "salud",
    ]:
        (tmp_path / sub).mkdir(parents=True, exist_ok=True)

    # Re-importar módulos para que tomen el nuevo VAULT_PATH
    import claudio_tools.common
    import claudio_tools.identidad
    import claudio_tools.familia
    import claudio_tools.finanzas
    import claudio_tools.compras
    import claudio_tools.menus
    import claudio_tools.coche
    import claudio_tools.casa
    import claudio_tools.documentos
    import claudio_tools.salud
    for m in [claudio_tools.common, claudio_tools.identidad,
              claudio_tools.familia, claudio_tools.finanzas,
              claudio_tools.compras, claudio_tools.menus,
              claudio_tools.coche, claudio_tools.casa,
              claudio_tools.documentos, claudio_tools.salud]:
        importlib.reload(m)
    return tmp_path


# ── identidad ────────────────────────────────────────────────
def test_claudio_recordar_y_contexto(vault_tmp):
    from claudio_tools.identidad import claudio_recordar, claudio_contexto
    r = claudio_recordar("angel", "prefiere café sin azúcar", importancia=3)
    assert "Recordado" in r or "📝" in r
    files = list((vault_tmp / "claudio" / "memorias" / "angel").glob("*.md"))
    assert len(files) == 1

    r2 = claudio_recordar("africa", "Bris come a las 8h", importancia=7)
    assert "africa" in r2

    out = claudio_contexto("angel", "café")
    assert "café" in out or "cafe" in out.lower()


def test_claudio_recordar_autor_invalido(vault_tmp):
    from claudio_tools.identidad import claudio_recordar
    r = claudio_recordar("foo", "x")
    assert r.startswith("❌")


def test_claudio_contexto_vault_vacio(vault_tmp):
    from claudio_tools.identidad import claudio_contexto
    out = claudio_contexto("angel", "cualquier")
    assert "sin memorias" in out


# ── familia ──────────────────────────────────────────────────
def test_recordatorio_crear_y_listar(vault_tmp):
    from claudio_tools.familia import recordatorio_crear, recordatorios_listar
    hoy_iso = date.today().isoformat()
    r = recordatorio_crear("Llamar fontanero", hoy_iso, "angel", prioridad=8)
    assert "Recordatorio" in r or "⏰" in r
    out = recordatorios_listar("hoy")
    assert "fontanero" in out.lower()


def test_recordatorio_completar(vault_tmp):
    from claudio_tools.familia import recordatorio_crear, recordatorio_completar
    hoy_iso = date.today().isoformat()
    recordatorio_crear("Test completar", hoy_iso, "africa")
    slug = f"{hoy_iso}-test-completar"
    out = recordatorio_completar(slug)
    assert out.startswith("✅")
    completados = list((vault_tmp / "familia" / "recordatorios" / "completados").glob("*.md"))
    assert len(completados) == 1


def test_cumpleanos_listar(vault_tmp):
    (vault_tmp / "familia" / "cumpleanos.md").write_text(
        "# Cumpleaños\n\n- 06-12 · Lucía · sobrina\n- 01-15 · Carmen · madre\n"
    )
    from claudio_tools.familia import familia_cumpleanos_listar
    out = familia_cumpleanos_listar(meses=12)
    assert "Lucía" in out
    assert "Carmen" in out


# ── finanzas ─────────────────────────────────────────────────
def test_gasto_anotar_y_resumen(vault_tmp):
    from claudio_tools.finanzas import gasto_anotar, gastos_resumen
    r1 = gasto_anotar(45.0, "gasolina", "transporte", "angel")
    assert "45.00€" in r1
    r2 = gasto_anotar(12.5, "pan", "alimentacion", "africa")
    assert "12.50€" in r2

    out = gastos_resumen("mes_actual")
    assert "57.50" in out
    assert "transporte" in out
    assert "alimentacion" in out


def test_gasto_anotar_categoria_invalida_se_normaliza(vault_tmp):
    from claudio_tools.finanzas import gasto_anotar
    r = gasto_anotar(10.0, "x", "no_existe", "angel")
    assert "otros" in r or "10.00" in r


def test_recurrente_alertar_sin_items(vault_tmp):
    (vault_tmp / "finanzas" / "recurrentes.yaml").write_text("items: []\n")
    from claudio_tools.finanzas import recurrente_alertar
    out = recurrente_alertar(7)
    assert "sin recurrentes" in out.lower() or "(" in out


def test_recurrente_alertar_con_item(vault_tmp):
    hoy = date.today()
    manana = hoy + timedelta(days=1)
    (vault_tmp / "finanzas" / "recurrentes.yaml").write_text(
        f"items:\n"
        f"  - nombre: Netflix\n"
        f"    monto_eur: 17.99\n"
        f"    dia_mes: {manana.day}\n"
        f"    categoria: ocio\n"
        f"    autor: angel\n"
    )
    from claudio_tools.finanzas import recurrente_alertar
    out = recurrente_alertar(7)
    assert "Netflix" in out


# ── compras ──────────────────────────────────────────────────
def test_compras_flow(vault_tmp):
    from claudio_tools.compras import (
        lista_compras_añadir, lista_compras_ver, lista_compras_completar,
    )
    r = lista_compras_añadir("leche", "angel")
    assert "leche" in r.lower()
    r2 = lista_compras_añadir("leche", "africa")  # duplicado
    assert "Ya está" in r2 or "ya esta" in r2.lower() or "leche" in r2.lower()

    ver = lista_compras_ver()
    assert "leche" in ver.lower()

    comp = lista_compras_completar("leche")
    assert comp.startswith("✅")
    historico = list((vault_tmp / "compras" / "historico").glob("*.md"))
    assert len(historico) == 1


def test_despensa_estado(vault_tmp):
    (vault_tmp / "compras" / "despensa.yaml").write_text(
        "items:\n"
        "  - producto: lentejas\n"
        "    cantidad: 2kg\n"
        "    categoria: legumbres\n"
    )
    from claudio_tools.compras import despensa_estado
    out = despensa_estado()
    assert "lentejas" in out


# ── menús ────────────────────────────────────────────────────
def test_receta_guardar_y_sugerir(vault_tmp):
    from claudio_tools.menus import receta_guardar, menu_sugerir
    r = receta_guardar(
        "Tortilla de patatas",
        "patata, huevo, cebolla, sal",
        "1. Pelar y cortar\n2. Freír\n3. Cuajar",
        fuente="tradicion",
    )
    assert "Tortilla" in r
    files = list((vault_tmp / "menus" / "recetas").glob("*.md"))
    assert len(files) == 1

    out = menu_sugerir(ingredientes_disponibles="patata, huevo")
    assert "Tortilla" in out


def test_menu_sugerir_sin_recetas(vault_tmp):
    from claudio_tools.menus import menu_sugerir
    out = menu_sugerir()
    assert "sin recetas" in out.lower() or "receta_guardar" in out


# ── coche ────────────────────────────────────────────────────
def test_coche_estado_sin_index(vault_tmp):
    from claudio_tools.coche import coche_estado
    out = coche_estado()
    assert "sin coche/INDEX.md" in out or "INDEX.md" in out


def test_coche_evento_actualiza_index(vault_tmp):
    # Crear INDEX inicial
    idx = vault_tmp / "coche" / "INDEX.md"
    idx.write_text(
        "---\n"
        "matricula: AB-123-CD\n"
        "modelo: Berlingo\n"
        "kilometros: 100000\n"
        "itv_proxima: 2026-08-12\n"
        "seguro_renovacion: 2026-11-22\n"
        "ultimo_mantenimiento: 2026-02-10\n"
        "ultima_actualizacion: 2026-05-14\n"
        "---\n\n# Coche\n"
    )
    from claudio_tools.coche import coche_evento, coche_estado
    r = coche_evento("mantenimiento", date.today().isoformat(), 250.0,
                     "cambio aceite", "angel")
    assert "mantenimiento" in r.lower()
    # INDEX debe haberse actualizado
    text = idx.read_text()
    assert "ultimo_mantenimiento:" in text
    assert date.today().isoformat() in text

    out = coche_estado()
    assert "AB-123-CD" in out
    assert "250.00€" in out


def test_coche_evento_tipo_invalido(vault_tmp):
    from claudio_tools.coche import coche_evento
    r = coche_evento("foo", "hoy", 0, "")
    assert r.startswith("❌")


# ── casa ─────────────────────────────────────────────────────
def test_casa_mantenimiento(vault_tmp):
    from claudio_tools.casa import casa_mantenimiento_anotar
    r = casa_mantenimiento_anotar(
        "Deshollinado chimenea", proximo="2027-09-01", autor="angel",
    )
    assert "🏠" in r or "Anotado" in r
    text = (vault_tmp / "casa" / "mantenimiento.md").read_text()
    assert "Deshollinado" in text
    assert "2027-09-01" in text


# ── documentos ───────────────────────────────────────────────
def test_documento_anotar_y_buscar(vault_tmp):
    from claudio_tools.documentos import documento_anotar, documentos_buscar
    r = documento_anotar(
        "factura", "Factura EDF mayo 87.32€", "2026-05-10", "EDF", "angel"
    )
    assert "factura" in r.lower()
    fac_dir = vault_tmp / "documentos" / "facturas" / "2026"
    files = list(fac_dir.glob("*.md"))
    assert len(files) == 1

    out = documentos_buscar("EDF")
    assert "EDF" in out

    out2 = documentos_buscar("inexistente_xyz")
    assert "sin matches" in out2.lower()


def test_documento_tipo_invalido(vault_tmp):
    from claudio_tools.documentos import documento_anotar
    r = documento_anotar("foo", "x", "2026-01-01", "Y", "angel")
    assert r.startswith("❌")


# ── salud ────────────────────────────────────────────────────
def test_cita_medica_requiere_autor(vault_tmp):
    from claudio_tools.salud import cita_medica_anotar
    r = cita_medica_anotar("bris", "veterinario", "2026-06-03", "vacuna", "")
    assert r.startswith("❌")


def test_cita_medica_ok(vault_tmp):
    from claudio_tools.salud import cita_medica_anotar
    r = cita_medica_anotar("bris", "veterinario", "2026-06-03",
                           "vacuna anual", autor="angel")
    assert "veterinario" in r.lower()
    files = list((vault_tmp / "salud" / "citas").glob("*.md"))
    assert len(files) == 1


def test_medicacion_sin_yaml(vault_tmp):
    from claudio_tools.salud import medicacion_recordar
    out = medicacion_recordar()
    assert "sin medicacion.yaml" in out


def test_medicacion_con_item_hoy(vault_tmp):
    hoy = date.today().isoformat()
    (vault_tmp / "salud" / "medicacion.yaml").write_text(
        f"items:\n"
        f"  - quien: bris\n"
        f"    medicamento: Milbemax\n"
        f"    dosis: 1 comprimido\n"
        f"    horas: ['08:00']\n"
        f"    cada_n_dias: 1\n"
        f"    desde: {hoy}\n"
    )
    from claudio_tools.salud import medicacion_recordar
    out = medicacion_recordar()
    assert "Milbemax" in out


# ── common ───────────────────────────────────────────────────
def test_parse_date_natural(vault_tmp):
    from claudio_tools.common import parse_date_natural
    f, resto = parse_date_natural("mañana llamar fontanero")
    assert f == date.today() + timedelta(days=1)
    assert "fontanero" in resto

    f2, resto2 = parse_date_natural("2026-06-12 cumpleaños")
    assert f2 == date(2026, 6, 12)
    assert "cumpleaños" in resto2

    f3, resto3 = parse_date_natural("hoy")
    assert f3 == date.today()
    assert resto3 == ""

    f4, _ = parse_date_natural("sin fecha")
    assert f4 is None


def test_slugify(vault_tmp):
    from claudio_tools.common import slugify
    assert slugify("Cumpleaños de Lucía") == "cumpleanos-de-lucia"
    assert slugify("") == "sin-titulo"
    assert slugify("¡¡¡!!!") == "sin-titulo"


def test_normalize_author(vault_tmp):
    from claudio_tools.common import normalize_author
    assert normalize_author("angel") == "angel"
    assert normalize_author("ÁFRICA") == "africa"
    with pytest.raises(ValueError):
        normalize_author("desconocido")
    with pytest.raises(ValueError):
        normalize_author("bris", allow_bris=False)
