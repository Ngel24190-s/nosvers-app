"""Worker aappma_stock: stock Dendrobaena + pedido activo + contactos AAPPMA Neuvic."""
from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from claudio_tools.common import parse_frontmatter, vault

log = logging.getLogger("tablero.v2.workers.aappma_stock")


def _stock_file() -> Path:
    return vault() / "nosvers" / "aappma" / "stock.md"


def _mock() -> dict:
    return {
        "dendrobaena_disponibles_g": 1850,
        "dendrobaena_reservadas_g": 400,
        "proxima_entrega": "2026-05-18",
        "pedido_activo": {
            "cliente": "AAPPMA Neuvic — concours junior",
            "cantidad_g": 400,
            "fecha_entrega": "2026-05-18",
            "estado": "preparando",
        },
        "contactos": [
            {"nombre": "Thierry Le Cleach", "rol": "Président AAPPMA",
             "telefono": "+33 6 12 34 56 78", "email": ""},
            {"nombre": "Jean Martin", "rol": "Secrétaire",
             "telefono": "+33 6 87 65 43 21", "email": ""},
        ],
        "ts": datetime.now().isoformat(timespec="seconds"),
    }


async def aappma_stock_tick() -> dict | None:
    p = _stock_file()
    if not p.exists():
        return _mock()
    try:
        text = p.read_text(encoding="utf-8")
    except Exception:
        return _mock()
    meta, _body = parse_frontmatter(text)
    if not meta:
        return _mock()
    out = _mock()
    if meta.get("dendrobaena_disponibles_g") is not None:
        try:
            out["dendrobaena_disponibles_g"] = int(meta["dendrobaena_disponibles_g"])
        except (TypeError, ValueError):
            pass
    if meta.get("dendrobaena_reservadas_g") is not None:
        try:
            out["dendrobaena_reservadas_g"] = int(meta["dendrobaena_reservadas_g"])
        except (TypeError, ValueError):
            pass
    if meta.get("proxima_entrega"):
        out["proxima_entrega"] = str(meta["proxima_entrega"])
    out["ts"] = datetime.now().isoformat(timespec="seconds")
    return out
