"""Worker composteur: status agt_composteur (si activado) o mock."""
from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from claudio_tools.common import vault

log = logging.getLogger("tablero.v2.workers.composteur")


def _file() -> Path:
    return vault() / "agentes" / "agt_composteur" / "_resultado.md"


def _mock() -> dict:
    return {
        "activo": False,
        "nota": "agt_composteur no instalado todavía",
        "temperatura_c": 52,
        "humedad_pct": 65,
        "fase": "termofila",
        "ultima_volteada": "2026-05-10",
        "proxima_volteada": "2026-05-17",
        "alertas": [],
        "ts": datetime.now().isoformat(timespec="seconds"),
    }


async def composteur_tick() -> dict | None:
    p = _file()
    if not p.exists():
        return _mock()
    try:
        text = p.read_text(encoding="utf-8")
    except Exception as e:
        log.debug(f"composteur: {e}")
        return _mock()
    out = _mock()
    out["activo"] = True
    out["nota"] = ""
    snippet = text.strip().splitlines()
    if snippet:
        first = next((ln for ln in snippet if ln.strip() and not ln.startswith("#")), "")
        if first:
            out["nota"] = first.strip()[:200]
    out["ts"] = datetime.now().isoformat(timespec="seconds")
    return out
