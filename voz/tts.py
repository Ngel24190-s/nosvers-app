"""
voz.tts — Síntesis de voz con Piper (es_ES-davefx-medium).

Genera MP3 a partir de texto y lo guarda en
/home/nosvers/tablero/web/dist/audio/dictado/<uuid>.mp3
servido por Caddy en /audio/dictado/<uuid>.mp3
"""
from __future__ import annotations

import hashlib
import logging
import os
import subprocess
import time
from pathlib import Path

log = logging.getLogger("voz.tts")

PIPER_BIN_PY = "/home/nosvers/venv/bin/python3"
PIPER_MODEL = os.getenv(
    "VOZ_TTS_MODEL",
    "/home/nosvers/piper-voices/es/es_ES/davefx/medium/es_ES-davefx-medium.onnx",
)
OUT_DIR = Path("/home/nosvers/tablero/web/dist/audio/dictado")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Cache simple: misma frase → mismo MP3 (evita recomputar)
_CACHE: dict[str, str] = {}
_CACHE_MAX = 64


def sintetizar(texto: str) -> str | None:
    """Genera audio MP3 del texto. Devuelve URL relativa o None si falla."""
    texto = (texto or "").strip()
    if not texto:
        return None

    key = hashlib.sha256(texto.encode("utf-8")).hexdigest()[:16]
    if key in _CACHE:
        return _CACHE[key]

    wav = OUT_DIR / f"{key}.wav"
    mp3 = OUT_DIR / f"{key}.mp3"
    url = f"/audio/dictado/{key}.mp3"

    if mp3.exists():
        _CACHE[key] = url
        return url

    t0 = time.monotonic()
    try:
        # Piper → WAV
        subprocess.run(
            [PIPER_BIN_PY, "-m", "piper",
             "--model", PIPER_MODEL,
             "--output-file", str(wav)],
            input=texto.encode("utf-8"),
            check=True, capture_output=True, timeout=15,
        )
        # WAV → MP3 (ffmpeg, más ligero para el móvil)
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error",
             "-i", str(wav),
             "-codec:a", "libmp3lame", "-qscale:a", "4",
             str(mp3)],
            check=True, capture_output=True, timeout=8,
        )
        wav.unlink(missing_ok=True)
    except subprocess.CalledProcessError as e:
        log.error(f"Piper falló: {e.stderr.decode('utf-8', errors='ignore')[:200]}")
        return None
    except subprocess.TimeoutExpired:
        log.error("Piper TTS timeout")
        return None
    except Exception as e:
        log.exception(f"TTS error: {e}")
        return None

    dt = (time.monotonic() - t0) * 1000
    log.info(f"TTS {len(texto)}c en {dt:.0f}ms → {url}")

    # LRU simple
    if len(_CACHE) >= _CACHE_MAX:
        _CACHE.pop(next(iter(_CACHE)))
    _CACHE[key] = url
    return url
