"""Entrypoint del daemon nosvers-voz.

Orquesta: carga config → arranca SesionVoz que internamente arranca
WakeDetector y dispara loops conversacionales en demanda.

Logs en `~/.local/state/nosvers-voz/nosvers-voz.log` con rotación por
tamaño (5 archivos × 2 MB). Si systemd corre esto, también ve los logs
en journalctl.
"""

from __future__ import annotations

import logging
import logging.handlers
import os
import signal
import sys
from pathlib import Path

from .config import load_config
from .session import SesionVoz


def _configurar_logging() -> None:
    state_dir = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state")) / "nosvers-voz"
    state_dir.mkdir(parents=True, exist_ok=True)
    log_path = state_dir / "nosvers-voz.log"

    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    root = logging.getLogger()
    root.setLevel(logging.INFO)

    fh = logging.handlers.RotatingFileHandler(
        log_path, maxBytes=2 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    fh.setFormatter(fmt)
    root.addHandler(fh)

    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    root.addHandler(sh)

    logging.getLogger(__name__).info("logs en %s", log_path)


def main() -> int:
    _configurar_logging()
    log = logging.getLogger(__name__)
    cfg = load_config()
    if not cfg.modelo_wake_path_expanded.exists():
        log.error(
            "modelo wake word no encontrado en %s — entrenar primero con "
            "training/train_claudio.ipynb",
            cfg.modelo_wake_path_expanded,
        )
        return 2
    if not os.environ.get("ANTHROPIC_API_KEY"):
        log.warning("ANTHROPIC_API_KEY no está en env — el chat con Claude no funcionará")

    sesion = SesionVoz(cfg)

    def _stop(*_):
        log.info("señal recibida, parando…")
        sesion.detener()

    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)

    sesion.arrancar()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
