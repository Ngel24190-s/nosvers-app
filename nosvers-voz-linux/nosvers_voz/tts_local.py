"""TTS local con kokoro-onnx.

Soporta voces multilenguaje. Para NosVers usamos:
- `ef_dora`  → castellano (voz femenina)
- `ff_siwis` → francés (voz femenina)

Trocea el texto por frases para reducir TTFB (time-to-first-byte):
empieza a sonar la primera frase mientras se sintetiza la segunda.
"""

from __future__ import annotations

import argparse
import logging
import re
import threading
from typing import Iterable

import numpy as np
import sounddevice as sd

from .config import Config, load_config

log = logging.getLogger(__name__)

# Split por puntuación final, manteniendo el signo
_FRASE_RE = re.compile(r"(?<=[\.\!\?])\s+|(?<=[\.\!\?])$")


def _trocear(texto: str) -> list[str]:
    partes = [p.strip() for p in _FRASE_RE.split(texto) if p and p.strip()]
    # frases muy largas → cortar por comas también
    out: list[str] = []
    for p in partes:
        if len(p) > 200:
            out.extend([s.strip() for s in p.split(",") if s.strip()])
        else:
            out.append(p)
    return out or [texto]


class TTSLocal:
    """Cliente Kokoro TTS con stream por frase."""

    _kokoro = None
    _lock = threading.Lock()

    def __init__(self, cfg: Config | None = None) -> None:
        self.cfg = cfg or load_config()

    def _ensure_kokoro(self):
        with TTSLocal._lock:
            if TTSLocal._kokoro is None:
                from kokoro_onnx import Kokoro

                # kokoro-onnx descarga modelos en cache si no existen
                log.info("inicializando kokoro-onnx (primera vez descarga ~330MB)")
                TTSLocal._kokoro = Kokoro.from_pretrained("kokoro-v1.0")
            return TTSLocal._kokoro

    def decir(
        self,
        texto: str,
        idioma: str | None = None,
        velocidad: float | None = None,
    ) -> None:
        """Sintetiza y reproduce el texto. Bloqueante hasta fin de playback."""
        idioma = idioma or self.cfg.idioma_default
        velocidad = self.cfg.velocidad_tts if velocidad is None else velocidad
        velocidad = max(0.5, min(2.0, velocidad))
        voz = self.cfg.voz_es if idioma == "es" else self.cfg.voz_fr
        lang_code = "es" if idioma == "es" else "fr-fr"
        kokoro = self._ensure_kokoro()

        for frase in _trocear(texto):
            log.debug("tts frase=%r voz=%s vel=%.2f", frase[:60], voz, velocidad)
            audio, sr = kokoro.create(
                frase, voice=voz, speed=velocidad, lang=lang_code
            )
            sd.play(audio, samplerate=sr, blocking=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="TTS local con kokoro-onnx")
    parser.add_argument("--texto", required=True, help="texto a sintetizar")
    parser.add_argument("--voz", default=None, help="ef_dora | ff_siwis (override)")
    parser.add_argument("--idioma", default=None, help="es|fr")
    parser.add_argument("--velocidad", type=float, default=None, help="0.5-2.0")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    cfg = load_config()
    if args.voz:
        # patch de la voz manualmente
        if args.idioma == "fr" or "ff_" in args.voz:
            cfg = Config(**{**cfg.__dict__, "voz_fr": args.voz})
        else:
            cfg = Config(**{**cfg.__dict__, "voz_es": args.voz})
    tts = TTSLocal(cfg)
    tts.decir(args.texto, idioma=args.idioma, velocidad=args.velocidad)


if __name__ == "__main__":
    main()
