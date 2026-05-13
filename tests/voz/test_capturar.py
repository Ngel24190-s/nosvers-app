"""T020 — Test de contrato MCP de dia_capturar.

Cubre:
  - llamada con texto válido (CLASIFICADOR_FORCE_FAIL → fallback)
  - sin input → error 'input_vacio'
  - reintento mismo client_uuid → idempotente ('duplicado_ignorado')
  - audio_b64 inválido → error 'parametro_invalido'
  - origen normalizado a 'otro' si valor inválido
  - etiqueta manual válida vs inválida
"""
from __future__ import annotations

import base64
from datetime import date
from pathlib import Path

import pytest

from voz.capturar import dia_capturar_impl
from voz.vault_io import leer_dia, path_dia


def test_captura_texto_basica(vault_temporal, clasif_off, clean_idem_cache):
    res = dia_capturar_impl(
        texto="Probando captura por texto",
        ts_iso="2026-05-12T10:00:00+02:00",
        origen="texto_directo",
        device_label="test-device",
        client_uuid="uuid-A",
    )
    assert res["ok"] is True
    assert res["etiqueta_aplicada"] == "otro"  # FORCE_FAIL fuerza fallback
    assert res["modelo"] == "fallback"
    assert "archivo" in res
    assert "latencia_ms" in res

    notas = leer_dia(date(2026, 5, 12))
    assert len(notas) == 1
    assert notas[0].texto == "Probando captura por texto"
    assert notas[0].origen == "texto_directo"


def test_input_vacio_error(vault_temporal, clasif_off, clean_idem_cache):
    res = dia_capturar_impl(texto="", device_label="d", client_uuid="uuid-vacio")
    assert res["ok"] is False
    assert res["error"] == "input_vacio"


def test_idempotencia_mismo_uuid(vault_temporal, clasif_off, clean_idem_cache):
    kwargs = dict(
        texto="Idempotencia",
        ts_iso="2026-05-12T11:00:00+02:00",
        origen="texto_directo",
        device_label="dev-idem",
        client_uuid="uuid-mismo",
    )
    primero = dia_capturar_impl(**kwargs)
    assert primero["ok"] is True

    segundo = dia_capturar_impl(**kwargs)
    assert segundo["ok"] is True
    assert segundo.get("nota") == "duplicado_ignorado"
    # No se duplica en el vault
    notas = leer_dia(date(2026, 5, 12))
    assert len(notas) == 1


def test_audio_b64_invalido(vault_temporal, clasif_off, clean_idem_cache):
    res = dia_capturar_impl(
        audio_b64="$$$ no es base64 $$$",
        device_label="d", client_uuid="uuid-bad-b64",
    )
    assert res["ok"] is False
    assert res["error"] == "parametro_invalido"


def test_etiqueta_manual_valida(vault_temporal, clasif_off, clean_idem_cache):
    res = dia_capturar_impl(
        texto="Esto es claramente NosVers",
        etiqueta="nosvers",
        ts_iso="2026-05-12T12:00:00+02:00",
        origen="texto_directo",
        device_label="d", client_uuid="uuid-etiqueta-manual",
    )
    assert res["ok"] is True
    assert res["etiqueta_aplicada"] == "nosvers"
    assert res["modelo"] == "manual"
    assert res["confianza"] == 1.0


def test_etiqueta_manual_invalida_fallback(vault_temporal, clasif_off, clean_idem_cache):
    res = dia_capturar_impl(
        texto="texto",
        etiqueta="categoria-que-no-existe",
        ts_iso="2026-05-12T13:00:00+02:00",
        origen="texto_directo",
        device_label="d", client_uuid="uuid-etiqueta-bad",
    )
    assert res["ok"] is True
    # etiqueta inválida y != "auto" → fallback "otro"
    assert res["etiqueta_aplicada"] == "otro"


def test_origen_invalido_se_normaliza(vault_temporal, clasif_off, clean_idem_cache):
    res = dia_capturar_impl(
        texto="texto",
        ts_iso="2026-05-12T14:00:00+02:00",
        origen="inventado",
        device_label="d", client_uuid="uuid-origen-bad",
    )
    assert res["ok"] is True
    notas = leer_dia(date(2026, 5, 12))
    assert any(n.origen == "otro" for n in notas)


def test_sin_ts_iso_usa_ahora(vault_temporal, clasif_off, clean_idem_cache):
    res = dia_capturar_impl(
        texto="sin ts",
        origen="texto_directo",
        device_label="d", client_uuid="uuid-no-ts",
    )
    assert res["ok"] is True
    assert "ts" in res


def test_autor_se_persiste_en_frontmatter(vault_temporal, clasif_off, clean_idem_cache):
    """BRIEF §14: el campo autor llega al frontmatter y se devuelve en la respuesta."""
    res = dia_capturar_impl(
        texto="Comprado abono",
        autor="africa",
        ts_iso="2026-05-13T11:00:00+02:00",
        origen="voz_movil",
        device_label="movil-africa",
        client_uuid="uuid-afr-1",
    )
    assert res["ok"] is True
    assert res["autor"] == "africa"
    notas = leer_dia(date(2026, 5, 13))
    assert len(notas) == 1
    assert notas[0].autor == "africa"


def test_autor_invalido_se_normaliza_a_angel(vault_temporal, clasif_off, clean_idem_cache):
    """Autor desconocido cae al default 'angel' (políticamente acordado en CLAUDE.md)."""
    res = dia_capturar_impl(
        texto="autor extraño",
        autor="desconocido-x",
        ts_iso="2026-05-13T12:00:00+02:00",
        device_label="d", client_uuid="uuid-bad-autor",
    )
    assert res["ok"] is True
    assert res["autor"] == "angel"


def test_default_autor_angel(vault_temporal, clasif_off, clean_idem_cache):
    """Sin pasar autor explícito, el default es 'angel'."""
    res = dia_capturar_impl(
        texto="default angel",
        ts_iso="2026-05-13T13:00:00+02:00",
        device_label="d", client_uuid="uuid-default-autor",
    )
    assert res["ok"] is True
    assert res["autor"] == "angel"


def test_audio_path_lleva_sufijo_autor(vault_temporal, clasif_off, clean_idem_cache):
    """El audio persistido tiene sufijo _{autor} en el nombre del archivo."""
    import base64
    # Datos arbitrarios; con FORCE_FAIL no se transcribe pero el audio se guarda.
    audio_b64 = base64.b64encode(b"opusbytes_xx" * 50).decode("ascii")
    res = dia_capturar_impl(
        texto="ya transcrito",     # texto presente → no llama STT
        audio_b64=audio_b64,
        autor="africa",
        ts_iso="2026-05-13T14:32:17+02:00",
        device_label="d", client_uuid="uuid-audio-africa",
    )
    assert res["ok"] is True
    assert res["audio_persistido"]
    assert res["audio_persistido"].endswith("14-32-17_africa.opus")
