"""Worker briefing_africa: lee última run de agt05_africa."""
from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from claudio_tools.common import vault

log = logging.getLogger("tablero.v2.workers.briefing_africa")


def _file() -> Path:
    return vault() / "agentes" / "agt05_africa" / "_resultado.md"


def _mock() -> dict:
    return {
        "fecha": "2026-05-14",
        "titulo": "Sin briefing reciente",
        "extracto": (
            "agt05_africa todavía no ha publicado resultado esta semana. "
            "Ejecuta el agente desde la tab Agentes."
        ),
        "items": [],
        "ts": datetime.now().isoformat(timespec="seconds"),
    }


def _extract_blocks(text: str) -> list[dict]:
    blocks: list[dict] = []
    cur: dict | None = None
    for line in text.splitlines():
        if line.startswith("## "):
            if cur:
                blocks.append(cur)
            cur = {"titulo": line[3:].strip(), "extracto": ""}
            continue
        if cur is not None:
            if len(cur["extracto"]) < 280 and line.strip():
                cur["extracto"] += line.strip() + " "
    if cur:
        blocks.append(cur)
    return blocks[:5]


async def briefing_africa_tick() -> dict | None:
    p = _file()
    if not p.exists():
        return _mock()
    try:
        text = p.read_text(encoding="utf-8")
    except Exception as e:
        log.debug(f"briefing_africa: {e}")
        return _mock()
    if not text.strip():
        return _mock()
    items = _extract_blocks(text)
    first_line = next(
        (ln for ln in text.splitlines() if ln.startswith("# ") or ln.startswith("## ")),
        "Briefing África",
    ).lstrip("# ").strip()
    mtime = datetime.fromtimestamp(p.stat().st_mtime).date().isoformat()
    return {
        "fecha": mtime,
        "titulo": first_line[:120] or "Briefing África",
        "extracto": (items[0]["extracto"][:280] if items else text[:280].strip()),
        "items": items,
        "ts": datetime.now().isoformat(timespec="seconds"),
    }
