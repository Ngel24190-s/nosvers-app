"""STT local con faster-whisper.

Carga lazy del modelo: la primera transcripción tarda ~3-5s, las siguientes
~300-800ms en CPU para audios de 5-10s. Modelo `small` es el sweet spot
calidad/velocidad para CPU.
"""

from __future__ import annotations

import argparse
import logging
import threading
from pathlib import Path
from typing import Union

import numpy as np

from .config import Config, load_config

log = logging.getLogger(__name__)


class STTLocal:
    """Transcriptor con faster-whisper. Modelo cargado lazy y cacheado."""

    _model = None
    _lock = threading.Lock()

    def __init__(self, cfg: Config | None = None) -> None:
        self.cfg = cfg or load_config()

    def _ensure_model(self):
        with STTLocal._lock:
            if STTLocal._model is None:
                from faster_whisper import WhisperModel

                device = self.cfg.device_stt
                if device == "auto":
                    try:
                        import torch
                        device = "cuda" if torch.cuda.is_available() else "cpu"
                    except ImportError:
                        device = "cpu"
                compute_type = "int8" if device == "cpu" else "float16"
                log.info(
                    "cargando faster-whisper modelo=%s device=%s compute=%s",
                    self.cfg.modelo_stt, device, compute_type,
                )
                STTLocal._model = WhisperModel(
                    self.cfg.modelo_stt,
                    device=device,
                    compute_type=compute_type,
                )
            return STTLocal._model

    def transcribir(
        self,
        audio: Union[np.ndarray, str, Path],
        idioma: str | None = None,
    ) -> str:
        """Transcribe un array float32 (16kHz mono) o un path a archivo.

        Devuelve el texto concatenado. Si idioma=None, autodetecta.
        """
        model = self._ensure_model()
        if isinstance(audio, (str, Path)):
            source = str(audio)
        else:
            arr = audio
            if arr.dtype != np.float32:
                if arr.dtype == np.int16:
                    arr = arr.astype(np.float32) / 32768.0
                else:
                    arr = arr.astype(np.float32)
            source = arr
        segments, info = model.transcribe(
            source,
            language=idioma,
            beam_size=1,
            vad_filter=True,
            vad_parameters={"min_silence_duration_ms": 500},
        )
        texto = " ".join(s.text.strip() for s in segments).strip()
        log.info(
            "transcrito len=%d idioma_detectado=%s prob=%.2f",
            len(texto), info.language, info.language_probability,
        )
        return texto


def main() -> None:
    parser = argparse.ArgumentParser(description="STT local con faster-whisper")
    parser.add_argument("--file", required=True, help="audio file (wav/flac/opus/...)")
    parser.add_argument("--idioma", default=None, help="es|fr|None (autodetect)")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    stt = STTLocal()
    texto = stt.transcribir(args.file, idioma=args.idioma)
    print(texto)


if __name__ == "__main__":
    main()
