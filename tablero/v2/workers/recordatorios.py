"""Worker recordatorios: lee familia/recordatorios/*.md y publica snapshot."""
from __future__ import annotations

import logging
from datetime import date, timedelta
from pathlib import Path

from claudio_tools.common import parse_frontmatter, vault

log = logging.getLogger("tablero.v2.workers.recordatorios")


def _read_one(path: Path) -> dict | None:
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return None
    meta, body = parse_frontmatter(text)
    if meta.get("hecho") is True:
        return None
    fecha = str(meta.get("fecha", "")).strip()
    if not fecha:
        return None
    texto_line = ""
    for line in body.splitlines():
        s = line.strip()
        if s and not s.startswith("#"):
            texto_line = s
            break
    return {
        "slug": path.stem,
        "texto": texto_line[:200],
        "fecha": fecha,
        "autor": str(meta.get("autor", "")),
        "prioridad": int(meta.get("prioridad", 3) or 3),
        "hecho": False,
    }


async def recordatorios_tick() -> dict | None:
    base = vault() / "familia" / "recordatorios"
    if not base.exists():
        return {"empty": True}
    hoy = date.today()
    en_7 = hoy + timedelta(days=7)
    items: list[dict] = []
    try:
        for p in base.glob("*.md"):
            if p.is_dir():
                continue
            it = _read_one(p)
            if it:
                items.append(it)
    except Exception as e:
        log.debug(f"recordatorios listing: {e}")
        return {"empty": True}

    if not items:
        return {"empty": True}

    def _by_date(it: dict) -> str:
        return it.get("fecha", "9999")

    items.sort(key=_by_date)
    total_hoy = sum(1 for it in items if it["fecha"] == hoy.isoformat())
    total_semana = sum(
        1 for it in items if it["fecha"] <= en_7.isoformat()
    )
    return {
        "items": items[:20],
        "total_hoy": total_hoy,
        "total_semana": total_semana,
        "total": len(items),
    }
