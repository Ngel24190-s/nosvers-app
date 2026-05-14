"""Worker huerto_estado: lee nosvers/huerto/ o publica mock realista."""
from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from claudio_tools.common import parse_frontmatter, vault

log = logging.getLogger("tablero.v2.workers.huerto_estado")


def _huerto_dir() -> Path:
    return vault() / "nosvers" / "huerto"


def _mock() -> dict:
    return {
        "cultivos": [
            {"nombre": "Tomates Cœur de Bœuf", "area_m2": 8, "siembra": "2026-03-15",
             "cosecha_prev": "2026-07-20", "ultimo_riego": "2026-05-13", "estado": "creciendo"},
            {"nombre": "Courgettes", "area_m2": 6, "siembra": "2026-04-02",
             "cosecha_prev": "2026-06-25", "ultimo_riego": "2026-05-13", "estado": "creciendo"},
            {"nombre": "Salades de printemps", "area_m2": 3, "siembra": "2026-03-28",
             "cosecha_prev": "2026-05-25", "ultimo_riego": "2026-05-14", "estado": "maduro"},
            {"nombre": "Haricots verts", "area_m2": 4, "siembra": "2026-04-20",
             "cosecha_prev": "2026-07-10", "ultimo_riego": "2026-05-12", "estado": "plantado"},
            {"nombre": "Ail rose de Lautrec", "area_m2": 2, "siembra": "2025-11-15",
             "cosecha_prev": "2026-06-30", "ultimo_riego": "2026-05-11", "estado": "creciendo"},
        ],
        "total_cultivos": 5,
        "ultimo_riego_general": "2026-05-14",
        "compost": {
            "nivel": "alto",
            "temperatura_c": 52,
            "ultima_volteada": "2026-05-10",
        },
        "ts": datetime.now().isoformat(timespec="seconds"),
    }


async def huerto_estado_tick() -> dict | None:
    d = _huerto_dir()
    if not d.exists():
        return _mock()
    cultivos: list[dict] = []
    ultimo_riego_general: str | None = None
    compost: dict | None = None
    try:
        for p in d.glob("*.md"):
            if p.is_dir() or p.stem.startswith("_"):
                continue
            try:
                text = p.read_text(encoding="utf-8")
            except Exception:
                continue
            meta, _body = parse_frontmatter(text)
            if not meta:
                continue
            if p.stem == "compost" or meta.get("tipo") == "compost":
                compost = {
                    "nivel": str(meta.get("nivel", "medio")),
                    "temperatura_c": meta.get("temperatura_c"),
                    "ultima_volteada": str(meta.get("ultima_volteada", "")),
                }
                continue
            nombre = str(meta.get("nombre") or meta.get("cultivo") or p.stem)
            riego = str(meta.get("ultimo_riego", ""))
            if riego and (ultimo_riego_general is None or riego > ultimo_riego_general):
                ultimo_riego_general = riego
            cultivos.append({
                "nombre": nombre,
                "area_m2": meta.get("area_m2"),
                "siembra": str(meta.get("siembra", "")),
                "cosecha_prev": str(meta.get("cosecha_prev", "")),
                "ultimo_riego": riego,
                "estado": str(meta.get("estado", "creciendo")),
            })
    except Exception as e:
        log.debug(f"huerto listing: {e}")
        return _mock()
    if not cultivos and not compost:
        return _mock()
    return {
        "cultivos": cultivos[:20],
        "total_cultivos": len(cultivos),
        "ultimo_riego_general": ultimo_riego_general,
        "compost": compost,
        "ts": datetime.now().isoformat(timespec="seconds"),
    }
