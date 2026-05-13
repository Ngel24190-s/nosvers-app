"""Detector de wake word "Claudio" usando openWakeWord.

Captura audio del micrófono con sounddevice en chunks de 1280 muestras
(80 ms a 16 kHz), pasa cada chunk al modelo ONNX, y dispara `on_wake`
cuando la confianza supera `umbral_wake` durante un frame, respetando
el cooldown configurado.

Modo `--test`: muestra en stdout la confianza por activación, útil para
ajustar el umbral en sesión real con Angel.
"""

from __future__ import annotations

import argparse
import logging
import queue
import threading
import time
from collections.abc import Callable
from typing import Optional

import numpy as np
import sounddevice as sd

from .config import Config, load_config

log = logging.getLogger(__name__)

CHUNK_SAMPLES = 1280   # 80 ms @ 16 kHz, formato esperado por openWakeWord


class WakeDetector:
    """Detector de wake word con loop en thread separado."""

    def __init__(
        self,
        cfg: Config,
        on_wake: Callable[[float], None] | None = None,
    ) -> None:
        self.cfg = cfg
        self.on_wake = on_wake or (lambda confianza: None)
        self._stop = threading.Event()
        self._muted = threading.Event()    # mute mic durante TTS playback
        self._q: queue.Queue[np.ndarray] = queue.Queue(maxsize=20)
        self._model: object | None = None
        self._last_activation_ts: float = 0.0
        self._thread: threading.Thread | None = None

    # -------- ciclo de vida --------

    def start(self) -> None:
        """Carga el modelo y arranca el loop. Idempotente."""
        if self._thread is not None and self._thread.is_alive():
            return
        self._load_model()
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._run, name="nosvers-voz-wake", daemon=True
        )
        self._thread.start()
        log.info(
            "wake detector activo (umbral=%.2f cooldown=%.1fs modelo=%s)",
            self.cfg.umbral_wake,
            self.cfg.cooldown_wake_s,
            self.cfg.modelo_wake_path_expanded,
        )

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None

    def mute(self) -> None:
        """Silencia el detector — usar durante playback TTS."""
        self._muted.set()

    def unmute(self) -> None:
        self._muted.clear()

    # -------- detalles --------

    def _load_model(self) -> None:
        from openwakeword import Model

        modelo = str(self.cfg.modelo_wake_path_expanded)
        if not self.cfg.modelo_wake_path_expanded.exists():
            raise FileNotFoundError(
                f"Modelo wake word no encontrado en {modelo}. "
                "Entrenar con training/train_claudio.ipynb."
            )
        self._model = Model(wakeword_models=[modelo], inference_framework="onnx")

    def _audio_callback(self, indata, frames, time_info, status) -> None:
        if status:
            log.warning("sounddevice status: %s", status)
        # int16 mono → np.ndarray (frames,)
        try:
            self._q.put_nowait(indata[:, 0].copy())
        except queue.Full:
            log.warning("queue audio llena — descartando frame")

    def _run(self) -> None:
        device = self.cfg.input_device or None
        with sd.InputStream(
            samplerate=self.cfg.input_samplerate,
            blocksize=CHUNK_SAMPLES,
            channels=1,
            dtype="int16",
            callback=self._audio_callback,
            device=device,
        ):
            while not self._stop.is_set():
                try:
                    chunk = self._q.get(timeout=0.5)
                except queue.Empty:
                    continue
                if self._muted.is_set():
                    continue
                self._process_chunk(chunk)

    def _process_chunk(self, chunk: np.ndarray) -> None:
        assert self._model is not None
        scores = self._model.predict(chunk)  # dict {nombre_modelo: prob}
        # tomar el máximo entre los modelos cargados (en nuestro caso solo Claudio)
        confianza = max(scores.values()) if scores else 0.0
        now = time.monotonic()
        if confianza < self.cfg.umbral_wake:
            return
        if now - self._last_activation_ts < self.cfg.cooldown_wake_s:
            return
        self._last_activation_ts = now
        log.info("wake detectado confianza=%.3f", confianza)
        try:
            self.on_wake(confianza)
        except Exception:
            log.exception("on_wake callback falló")


# ---------------- modo --test standalone ----------------

def _main_test(cfg: Config) -> None:
    print("Modo test wake word — di 'Claudio' al micro. Ctrl+C para salir.")
    print(f"umbral={cfg.umbral_wake}  cooldown={cfg.cooldown_wake_s}s")

    def on_wake(conf: float) -> None:
        print(f"  ✓ wake detectado, confianza={conf:.3f}  ts={time.strftime('%H:%M:%S')}")

    detector = WakeDetector(cfg, on_wake=on_wake)
    detector.start()
    try:
        while True:
            time.sleep(1.0)
    except KeyboardInterrupt:
        print("\nparando…")
    finally:
        detector.stop()


def main() -> None:
    parser = argparse.ArgumentParser(description="nosvers-voz wake detector")
    parser.add_argument("--test", action="store_true", help="modo standalone de prueba")
    parser.add_argument("--umbral", type=float, help="override umbral_wake")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    cfg = load_config()
    if args.umbral is not None:
        cfg = Config(**{**cfg.__dict__, "umbral_wake": args.umbral})
    if args.test:
        _main_test(cfg)
    else:
        print("Sin --test esto sólo expone la clase WakeDetector. Usar __main__.py.")


if __name__ == "__main__":
    main()
