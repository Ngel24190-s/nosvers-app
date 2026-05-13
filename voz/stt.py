"""
voz.stt — Transcripción de audio con faster-whisper (lazy import).

El modelo se carga la primera vez que se invoca `transcribir()` y se
mantiene caliente en el proceso. Multilingüe (es/fr) con autodetección.
"""
from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path

log = logging.getLogger("voz.stt")

_MODEL = None
DEFAULT_MODEL_NAME = "small"
DEFAULT_DEVICE = "cpu"
DEFAULT_COMPUTE = "int8"


def _get_model():
    global _MODEL
    if _MODEL is not None:
        return _MODEL
    try:
        from faster_whisper import WhisperModel  # lazy import
    except ImportError as e:
        raise RuntimeError(
            "faster-whisper no está instalado. "
            "Ejecuta: pip3 install faster-whisper --break-system-packages"
        ) from e
    name = os.getenv("VOZ_STT_MODEL", DEFAULT_MODEL_NAME)
    device = os.getenv("VOZ_STT_DEVICE", DEFAULT_DEVICE)
    compute = os.getenv("VOZ_STT_COMPUTE", DEFAULT_COMPUTE)
    log.info(f"Cargando faster-whisper modelo={name} device={device} compute={compute}")
    _MODEL = WhisperModel(name, device=device, compute_type=compute)
    return _MODEL


def transcribir(audio_path_or_bytes, idioma: str | None = None) -> dict:
    """Transcribe audio. Devuelve dict con texto, idioma_detectado, duracion.

    Args:
        audio_path_or_bytes: Path o bytes (Opus, WAV, MP3, FLAC).
        idioma: 'es', 'fr', etc. None = autodetección.
    """
    model = _get_model()
    if isinstance(audio_path_or_bytes, (bytes, bytearray)):
        # faster-whisper acepta path o numpy; lo más fiable es escribirlo a tmp
        with tempfile.NamedTemporaryFile(suffix=".opus", delete=False) as tf:
            tf.write(audio_path_or_bytes)
            tmp_path = tf.name
        try:
            segments, info = model.transcribe(tmp_path, language=idioma, beam_size=5)
            texto = "".join(s.text for s in segments).strip()
        finally:
            try:
                Path(tmp_path).unlink()
            except OSError:
                pass
    else:
        segments, info = model.transcribe(str(audio_path_or_bytes), language=idioma, beam_size=5)
        texto = "".join(s.text for s in segments).strip()
    return {
        "texto": texto,
        "idioma_detectado": info.language,
        "duracion": info.duration,
    }
