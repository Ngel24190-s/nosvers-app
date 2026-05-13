"""Carga de configuración desde ~/.config/nosvers-voz/config.toml."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field, replace
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

DEFAULT_CONFIG_PATH = Path.home() / ".config" / "nosvers-voz" / "config.toml"


@dataclass(frozen=True)
class Config:
    mcp_url: str = ""
    mcp_token: str = ""

    idioma_default: str = "es"
    velocidad_tts: float = 1.0
    voz_es: str = "ef_dora"
    voz_fr: str = "ff_siwis"

    umbral_wake: float = 0.6
    cooldown_wake_s: float = 3.0
    modelo_wake_path: str = "~/nosvers-voz-linux/models/claudio.onnx"

    auto_cierre_sin_habla_s: float = 8.0
    timeout_total_sesion_s: float = 300.0

    modelo_stt: str = "small"
    device_stt: str = "auto"

    modelo_chat: str = "claude-sonnet-4-6"
    max_tokens_chat: int = 600

    input_device: str = ""
    input_samplerate: int = 16000

    @property
    def modelo_wake_path_expanded(self) -> Path:
        return Path(os.path.expanduser(self.modelo_wake_path))

    def with_velocidad(self, nueva: float) -> "Config":
        nueva = max(0.5, min(2.0, nueva))
        return replace(self, velocidad_tts=nueva)

    def with_idioma(self, nuevo: str) -> "Config":
        if nuevo not in ("es", "fr"):
            return self
        return replace(self, idioma_default=nuevo)


def load_config(path: Path | None = None) -> Config:
    """Carga la config desde TOML. Si el archivo no existe, devuelve defaults."""
    path = path or DEFAULT_CONFIG_PATH
    if not path.exists():
        return Config()
    with path.open("rb") as fh:
        data = tomllib.load(fh)
    known = {f.name for f in Config.__dataclass_fields__.values()}  # type: ignore[attr-defined]
    filtered = {k: v for k, v in data.items() if k in known}
    return Config(**filtered)


if __name__ == "__main__":
    cfg = load_config()
    for k, v in cfg.__dict__.items():
        if "token" in k:
            v = (v[:6] + "…") if v else ""
        print(f"  {k} = {v!r}")
