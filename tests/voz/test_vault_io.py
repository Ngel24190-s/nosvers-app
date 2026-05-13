"""T013 — Tests unitarios de voz.vault_io."""
from __future__ import annotations

from datetime import date, datetime, timezone

import pytest

from voz.vault_io import (
    Nota,
    escribir_nota,
    leer_dia,
    listar_dias,
    parsear_dia,
    path_dia,
)


def _nota(ts: str, texto: str, etiqueta: str = "nosvers", autor: str = "angel") -> Nota:
    return Nota(
        ts=ts,
        autor=autor,
        etiqueta=etiqueta,
        origen="texto_directo",
        audio=None,
        clasificador_confianza=1.0,
        clasificador_modelo="manual",
        texto=texto,
    )


def test_leer_dia_inexistente_devuelve_lista_vacia(vault_temporal):
    assert leer_dia(date(2099, 1, 1)) == []


def test_escribir_y_releer_nota(vault_temporal):
    n = _nota("2026-05-12T09:00:00+02:00", "Pedir fotos a África")
    archivo = escribir_nota(n)
    assert archivo == path_dia(date(2026, 5, 12))
    assert archivo.exists()

    leidas = leer_dia(date(2026, 5, 12))
    assert len(leidas) == 1
    assert leidas[0].texto == "Pedir fotos a África"
    assert leidas[0].etiqueta == "nosvers"


def test_varias_notas_reordenadas_por_ts(vault_temporal):
    # Escritas fuera de orden temporal
    escribir_nota(_nota("2026-05-12T15:00:00+02:00", "Tercera"))
    escribir_nota(_nota("2026-05-12T08:00:00+02:00", "Primera"))
    escribir_nota(_nota("2026-05-12T12:00:00+02:00", "Segunda"))

    notas = leer_dia(date(2026, 5, 12))
    textos = [n.texto for n in notas]
    assert textos == ["Primera", "Segunda", "Tercera"]


def test_listar_dias_rango(vault_temporal):
    escribir_nota(_nota("2026-05-10T09:00:00+02:00", "a"))
    escribir_nota(_nota("2026-05-12T09:00:00+02:00", "b"))
    escribir_nota(_nota("2026-05-14T09:00:00+02:00", "c"))

    todos = listar_dias()
    assert date(2026, 5, 10) in todos
    assert date(2026, 5, 12) in todos
    assert date(2026, 5, 14) in todos

    rango = listar_dias(desde=date(2026, 5, 11), hasta=date(2026, 5, 13))
    assert rango == [date(2026, 5, 12)]


def test_parsear_dia_respeta_frontmatter_estricto(vault_temporal):
    # Si no hay frontmatter, no es una "nota válida" y se ignora.
    archivo = path_dia(date(2026, 5, 12))
    archivo.parent.mkdir(parents=True, exist_ok=True)
    archivo.write_text("contenido sin frontmatter\n", encoding="utf-8")
    assert leer_dia(date(2026, 5, 12)) == []


def test_lock_persistente_no_corrompe(vault_temporal):
    """Dos escrituras secuenciales deben preservar ambas notas — el flock
    serializa internamente. (Para test de contención real, ver
    test_dia_end_to_end.py)."""
    escribir_nota(_nota("2026-05-12T10:00:00+02:00", "uno"))
    escribir_nota(_nota("2026-05-12T10:05:00+02:00", "dos"))
    notas = leer_dia(date(2026, 5, 12))
    assert len(notas) == 2
    assert {n.texto for n in notas} == {"uno", "dos"}


def test_pool_comun_angel_y_africa_en_el_mismo_dia(vault_temporal):
    """BRIEF §14.2: el mismo archivo del día contiene notas de ambos autores."""
    escribir_nota(_nota("2026-05-13T08:00:00+02:00", "Reunión Bordeaux", autor="angel"))
    escribir_nota(_nota("2026-05-13T08:30:00+02:00", "Lecho 3 con cosecha alta", autor="africa", etiqueta="nosvers"))
    escribir_nota(_nota("2026-05-13T15:00:00+02:00", "Comprar bombillas", autor="angel", etiqueta="trabajo"))

    notas = leer_dia(date(2026, 5, 13))
    assert len(notas) == 3
    autores = [n.autor for n in notas]
    assert autores == ["angel", "africa", "angel"]
    # Verifica que el frontmatter persiste el campo autor
    contenido = path_dia(date(2026, 5, 13)).read_text(encoding="utf-8")
    assert "autor: angel" in contenido
    assert "autor: africa" in contenido


def test_autor_default_para_notas_legacy(vault_temporal):
    """Notas sin campo `autor` en el frontmatter (pre-§14) → default 'angel'."""
    archivo = path_dia(date(2026, 5, 1))
    archivo.parent.mkdir(parents=True, exist_ok=True)
    archivo.write_text(
        "# Diario — 2026-05-01\n\n"
        "---\n"
        "ts: '2026-05-01T10:00:00+02:00'\n"
        "etiqueta: nosvers\n"
        "origen: texto_directo\n"
        "audio: null\n"
        "clasificador_confianza: 1.0\n"
        "clasificador_modelo: manual\n"
        "---\n\n"
        "nota legacy sin autor\n",
        encoding="utf-8",
    )
    notas = leer_dia(date(2026, 5, 1))
    assert len(notas) == 1
    assert notas[0].autor == "angel"
    assert notas[0].texto == "nota legacy sin autor"


def test_audio_path_lleva_sufijo_autor(vault_temporal):
    """guardar_audio_opus añade _{autor} al nombre del archivo."""
    from voz.vault_io import guardar_audio_opus, ruta_audio_relativa

    fp_angel = guardar_audio_opus(b"opusbytes_a", date(2026, 5, 13), "09-30-00", "angel")
    fp_africa = guardar_audio_opus(b"opusbytes_f", date(2026, 5, 13), "10-15-22", "africa")
    assert fp_angel.name == "09-30-00_angel.opus"
    assert fp_africa.name == "10-15-22_africa.opus"
    rel = ruta_audio_relativa(fp_angel)
    assert rel.endswith("dia/audio/2026-05-13/09-30-00_angel.opus")
