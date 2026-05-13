"""Tests de carga de configuración."""

import textwrap
from pathlib import Path

from nosvers_voz.config import Config, load_config


def test_config_defaults() -> None:
    cfg = Config()
    assert cfg.idioma_default == "es"
    assert cfg.velocidad_tts == 1.0
    assert cfg.umbral_wake == 0.6
    assert cfg.auto_cierre_sin_habla_s == 8.0
    assert cfg.timeout_total_sesion_s == 300.0


def test_with_velocidad_clamp() -> None:
    cfg = Config()
    assert cfg.with_velocidad(2.5).velocidad_tts == 2.0
    assert cfg.with_velocidad(0.1).velocidad_tts == 0.5
    assert cfg.with_velocidad(1.3).velocidad_tts == 1.3


def test_with_idioma_solo_valid() -> None:
    cfg = Config()
    assert cfg.with_idioma("fr").idioma_default == "fr"
    assert cfg.with_idioma("xx").idioma_default == "es"


def test_load_config_no_file(tmp_path: Path) -> None:
    cfg = load_config(tmp_path / "no-existe.toml")
    assert cfg == Config()


def test_load_config_basico(tmp_path: Path) -> None:
    cfg_path = tmp_path / "config.toml"
    cfg_path.write_text(textwrap.dedent("""
        mcp_url = "https://example.test"
        mcp_token = "deadbeef"
        idioma_default = "fr"
        velocidad_tts = 1.2
        umbral_wake = 0.75
        # campo desconocido se debe ignorar
        extra_field = "ignored"
    """).strip())
    cfg = load_config(cfg_path)
    assert cfg.mcp_url == "https://example.test"
    assert cfg.mcp_token == "deadbeef"
    assert cfg.idioma_default == "fr"
    assert cfg.velocidad_tts == 1.2
    assert cfg.umbral_wake == 0.75
