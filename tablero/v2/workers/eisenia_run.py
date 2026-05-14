"""Worker eisenia_run: lee output reciente agt_eisenia.

`_resultado.md` puede contener JSON con alertas tipo recolte_imminente,
temperatura, humedad, etc.
"""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from pathlib import Path

from claudio_tools.common import vault

log = logging.getLogger("tablero.v2.workers.eisenia_run")


def _file() -> Path:
    return vault() / "agentes" / "agt_eisenia" / "_resultado.md"


def _mock() -> dict:
    return {
        "ultima_ejecucion": None,
        "alertas": [],
        "estado": "sin_datos",
        "resumen": "agt_eisenia todavía no ha generado resultado.",
        "ts": datetime.now().isoformat(timespec="seconds"),
    }


_JSON_RE = re.compile(r"(\[[\s\S]*?\]|\{[\s\S]*?\})")


def _extract_alertas(text: str) -> list[dict]:
    m = _JSON_RE.search(text)
    if not m:
        return []
    try:
        data = json.loads(m.group(1))
    except json.JSONDecodeError:
        return []
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        return []
    out: list[dict] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        out.append({
            "type": str(item.get("type", "info")),
            "bac": str(item.get("bac", "")),
            "jours": item.get("jours"),
            "kg_estimes": item.get("kg_estimés") or item.get("kg_estimes"),
            "urgence": str(item.get("urgence", "normale")),
        })
    return out[:6]


async def eisenia_run_tick() -> dict | None:
    p = _file()
    if not p.exists():
        return _mock()
    try:
        text = p.read_text(encoding="utf-8")
    except Exception as e:
        log.debug(f"eisenia_run: {e}")
        return _mock()
    if not text.strip():
        return _mock()
    alertas = _extract_alertas(text)
    mtime = datetime.fromtimestamp(p.stat().st_mtime).isoformat(timespec="seconds")
    urgentes = sum(1 for a in alertas if a["urgence"] in ("urgente", "alta", "high"))
    return {
        "ultima_ejecucion": mtime,
        "alertas": alertas,
        "estado": "alertas" if alertas else "ok",
        "urgentes": urgentes,
        "resumen": (
            f"{len(alertas)} alerta(s)" if alertas else "Sin alertas recientes"
        ),
        "ts": datetime.now().isoformat(timespec="seconds"),
    }
