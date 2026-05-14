"""Worker proxima_publicacion: lee siguiente post agt02_instagram en cola."""
from __future__ import annotations

import logging
import re
from datetime import datetime
from pathlib import Path

from claudio_tools.common import vault

log = logging.getLogger("tablero.v2.workers.proxima_publicacion")


def _file() -> Path:
    return vault() / "agentes" / "agt02_instagram" / "_aprobados.md"


def _mock() -> dict:
    return {
        "estado": "vacio",
        "siguiente": None,
        "pendientes": 0,
        "aprobados": 0,
        "ts": datetime.now().isoformat(timespec="seconds"),
    }


_POST_RE = re.compile(r"^---POST\s+(\d+)\s+—\s+([^/]+)\s*/\s*([^-]+)---\s*$", re.IGNORECASE)


def _parse_posts(text: str) -> list[dict]:
    """Encuentra bloques POST N — DIA / HORA con campo STATUS / TIPO / CAPTION."""
    posts: list[dict] = []
    cur: dict | None = None
    caption_collect = False
    caption_buf: list[str] = []
    for raw in text.splitlines():
        line = raw.rstrip()
        m = _POST_RE.match(line)
        if m:
            if cur:
                if caption_buf:
                    cur["caption"] = " ".join(caption_buf).strip()[:280]
                posts.append(cur)
            cur = {
                "n": int(m.group(1)),
                "dia": m.group(2).strip(),
                "hora": m.group(3).strip(),
                "tipo": "",
                "status": "PENDING_APPROVAL",
                "caption": "",
            }
            caption_collect = False
            caption_buf = []
            continue
        if cur is None:
            continue
        if line.startswith("TIPO:"):
            cur["tipo"] = line.split(":", 1)[1].strip()
        elif line.startswith("STATUS:"):
            cur["status"] = line.split(":", 1)[1].strip().upper()
        elif line.startswith("CAPTION:"):
            caption_collect = True
            caption_buf = []
        elif caption_collect:
            if line.startswith("HASHTAGS:") or line.startswith("---"):
                caption_collect = False
                if caption_buf:
                    cur["caption"] = " ".join(caption_buf).strip()[:280]
            elif line.strip():
                caption_buf.append(line.strip())
    if cur:
        if caption_buf and not cur["caption"]:
            cur["caption"] = " ".join(caption_buf).strip()[:280]
        posts.append(cur)
    return posts


async def proxima_publicacion_tick() -> dict | None:
    p = _file()
    if not p.exists():
        return _mock()
    try:
        text = p.read_text(encoding="utf-8")
    except Exception as e:
        log.debug(f"proxima_publicacion: {e}")
        return _mock()
    posts = _parse_posts(text)
    if not posts:
        return _mock()
    pendientes = [p for p in posts if "PENDING" in p["status"] or "APPROVED" in p["status"]]
    aprobados = [p for p in posts if "APPROVED" in p["status"] or "OK" in p["status"]]
    siguiente = pendientes[0] if pendientes else posts[0]
    return {
        "estado": "en_cola" if pendientes else "publicados",
        "siguiente": {
            "n": siguiente.get("n", 0),
            "dia": siguiente.get("dia", ""),
            "hora": siguiente.get("hora", ""),
            "tipo": siguiente.get("tipo", ""),
            "caption": siguiente.get("caption", ""),
            "status": siguiente.get("status", ""),
        },
        "pendientes": len(pendientes),
        "aprobados": len(aprobados),
        "total": len(posts),
        "ts": datetime.now().isoformat(timespec="seconds"),
    }
