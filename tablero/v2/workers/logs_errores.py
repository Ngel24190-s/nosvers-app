"""Worker logs_errores: errores últimas 24h agrupados por agente."""
from __future__ import annotations

import logging
import time
from datetime import datetime
from pathlib import Path

log = logging.getLogger("tablero.v2.workers.logs_errores")


LOGS_DIR = Path("/home/nosvers/logs")
_ERROR_KEYWORDS = ("ERROR", "FAIL", "EXCEPTION", "Traceback")


def _mock() -> dict:
    return {
        "fuente": "mock",
        "total_errores": 0,
        "ventana_horas": 24,
        "por_agente": {},
        "ts": datetime.now().isoformat(timespec="seconds"),
    }


async def logs_errores_tick() -> dict | None:
    if not LOGS_DIR.exists():
        return _mock()
    cutoff = time.time() - 24 * 3600
    por_agente: dict[str, dict] = {}
    total = 0
    try:
        for p in LOGS_DIR.glob("*.log"):
            try:
                st = p.stat()
            except OSError:
                continue
            if st.st_mtime < cutoff and st.st_size < 10:
                continue
            name = p.stem
            try:
                # Sólo leer las últimas ~32 KB de cada log para evitar OOM
                with p.open("rb") as f:
                    f.seek(0, 2)
                    size = f.tell()
                    f.seek(max(size - 32_000, 0))
                    tail = f.read().decode("utf-8", errors="replace")
            except Exception:
                continue
            n = sum(
                1 for line in tail.splitlines()
                if any(k in line for k in _ERROR_KEYWORDS)
            )
            if n > 0:
                # last error line
                last = ""
                for line in reversed(tail.splitlines()):
                    if any(k in line for k in _ERROR_KEYWORDS):
                        last = line.strip()[:240]
                        break
                por_agente[name] = {
                    "n": n,
                    "ultimo": last,
                    "mtime": int(st.st_mtime),
                }
                total += n
    except Exception as e:
        log.debug(f"logs_errores: {e}")
        return _mock()
    return {
        "fuente": "logs",
        "total_errores": total,
        "ventana_horas": 24,
        "por_agente": dict(sorted(por_agente.items(), key=lambda kv: -kv[1]["n"])[:15]),
        "ts": datetime.now().isoformat(timespec="seconds"),
    }
