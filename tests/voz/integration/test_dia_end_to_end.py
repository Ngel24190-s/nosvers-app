"""T021 — Test de integración end-to-end de dia_capturar + dia_buscar.

Flujo:
  1. Llamar dia_capturar_impl con varios textos
  2. Verificar archivo del día creado con frontmatter correcto
  3. Llamar dia_buscar_impl y comprobar que encuentra las notas
"""
from __future__ import annotations

from datetime import date

import pytest

from voz.buscar import dia_buscar_impl
from voz.capturar import dia_capturar_impl
from voz.vault_io import leer_dia, path_dia


def test_capturar_luego_buscar(vault_temporal, clasif_off, clean_idem_cache):
    # 1. Capturar 3 notas
    r1 = dia_capturar_impl(
        texto="Pedir fotos a África para Instagram",
        ts_iso="2026-05-12T09:00:00+02:00",
        etiqueta="nosvers",
        origen="texto_directo",
        device_label="test-e2e", client_uuid="uuid-1",
    )
    r2 = dia_capturar_impl(
        texto="Revisar conftest pytest",
        ts_iso="2026-05-12T10:00:00+02:00",
        etiqueta="trabajo",
        origen="texto_directo",
        device_label="test-e2e", client_uuid="uuid-2",
    )
    r3 = dia_capturar_impl(
        texto="Compromiso: cena con familia el viernes",
        ts_iso="2026-05-12T11:00:00+02:00",
        etiqueta="familia",
        origen="texto_directo",
        device_label="test-e2e", client_uuid="uuid-3",
    )
    assert all(r["ok"] for r in (r1, r2, r3))

    # 2. Verificar archivo
    archivo = path_dia(date(2026, 5, 12))
    assert archivo.exists()
    contenido = archivo.read_text(encoding="utf-8")
    # Frontmatter YAML con campos requeridos
    assert "ts:" in contenido
    assert "etiqueta:" in contenido
    assert "origen:" in contenido
    assert "clasificador_modelo:" in contenido
    # 3 bloques de notas
    assert contenido.count("---") >= 6  # 3 notas × 2 delimitadores

    # 3. Lectura programática
    notas = leer_dia(date(2026, 5, 12))
    assert len(notas) == 3
    etiquetas = {n.etiqueta for n in notas}
    assert etiquetas == {"nosvers", "trabajo", "familia"}

    # 4. dia_buscar encuentra las notas
    res_busqueda = dia_buscar_impl(query="fotos", desde="2026-05-12", hasta="2026-05-12")
    assert res_busqueda["ok"] is True
    assert res_busqueda["total"] >= 1
    assert any("fotos" in r["fragmento"].lower() or "fotos" in r.get("texto", "").lower()
               for r in res_busqueda["resultados"])

    # 5. Filtro por etiqueta
    res_familia = dia_buscar_impl(query="cena", etiqueta="familia",
                                   desde="2026-05-12", hasta="2026-05-12")
    assert res_familia["ok"] is True
    assert res_familia["total"] == 1
    assert res_familia["resultados"][0]["etiqueta"] == "familia"


def test_idempotencia_no_duplica_en_vault(vault_temporal, clasif_off, clean_idem_cache):
    kwargs = dict(
        texto="Único",
        ts_iso="2026-05-13T09:00:00+02:00",
        etiqueta="otro",
        origen="texto_directo",
        device_label="test-idem", client_uuid="uuid-same",
    )
    dia_capturar_impl(**kwargs)
    dia_capturar_impl(**kwargs)
    dia_capturar_impl(**kwargs)

    notas = leer_dia(date(2026, 5, 13))
    assert len(notas) == 1
