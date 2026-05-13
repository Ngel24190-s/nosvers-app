#!/usr/bin/env python3
"""Cron nightly: borra subcarpetas de audio del día con > 7 días.

Idempotente. Si falla un borrado individual, sigue con los demás.
"""
from __future__ import annotations

import logging
import re
import shutil
import sys
from datetime import date, timedelta
from pathlib import Path

LOG_DIR = Path("/home/nosvers/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [purge_audio] %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "purge_audio.log"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger("purge_audio")

AUDIO_DIR = Path("/home/nosvers/public_html/knowledge_base/dia/audio")
TTL_DIAS = 7


def main() -> int:
    if not AUDIO_DIR.exists():
        log.info("no existe dia/audio/ — nada que purgar")
        return 0
    hoy = date.today()
    limite = hoy - timedelta(days=TTL_DIAS)
    purgados = 0
    bytes_recuperados = 0
    for sub in AUDIO_DIR.iterdir():
        if not sub.is_dir():
            continue
        m = re.match(r"^(\d{4}-\d{2}-\d{2})$", sub.name)
        if not m:
            continue
        try:
            f = date.fromisoformat(m.group(1))
        except ValueError:
            continue
        if f >= limite:
            continue  # dentro del TTL
        try:
            tamano = sum(p.stat().st_size for p in sub.rglob("*") if p.is_file())
            shutil.rmtree(sub)
            purgados += 1
            bytes_recuperados += tamano
            log.info(f"borrado {sub.name} ({tamano // 1024} KB)")
        except OSError as e:
            log.error(f"no pude borrar {sub.name}: {e}")
    log.info(f"purga completa: {purgados} subdirs eliminados, {bytes_recuperados // 1024} KB liberados")
    return 0


if __name__ == "__main__":
    sys.exit(main())
