"""Worker vermicultura: Dendrobaena stock + AAPPMA pedidos + Thierry contact.

Versión más rica que `aappma_stock`: integra Eisenia (lombriz para vermicompost)
+ Dendrobaena (lombriz para pesca AAPPMA Neuvic). Lee vault si existe;
si no, mock realista.
"""
from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from claudio_tools.common import parse_frontmatter, vault

log = logging.getLogger("tablero.v2.workers.vermicultura")


def _root() -> Path:
    return vault() / "nosvers" / "vermicultura"


def _aappma_file() -> Path:
    return vault() / "nosvers" / "aappma" / "stock.md"


def _mock() -> dict:
    return {
        "eisenia": {
            "bacs": 3,
            "biomasa_kg": 24.5,
            "produccion_lombricompost_kg_mes": 18,
            "ultima_recolte": "2026-05-08",
        },
        "dendrobaena": {
            "stock_g": 1850,
            "reservadas_g": 400,
            "proxima_entrega": "2026-05-18",
        },
        "aappma": {
            "pedido_activo": {
                "cliente": "AAPPMA Neuvic — concours junior",
                "cantidad_g": 400,
                "fecha_entrega": "2026-05-18",
                "estado": "preparando",
            },
            "concours_proximo": "2026-05-25",
        },
        "thierry": {
            "nombre": "Thierry Le Cleach",
            "rol": "Président AAPPMA Neuvic",
            "telefono": "+33 6 12 34 56 78",
            "email": "",
            "ultimo_contacto": "2026-05-05",
        },
        "ts": datetime.now().isoformat(timespec="seconds"),
    }


def _try_read(p: Path) -> dict | None:
    if not p.exists():
        return None
    try:
        text = p.read_text(encoding="utf-8")
    except Exception:
        return None
    meta, _ = parse_frontmatter(text)
    return meta or None


async def vermicultura_tick() -> dict | None:
    out = _mock()
    # Si existe vault/nosvers/vermicultura/eisenia.md, sobrescribir métricas
    eisenia_meta = _try_read(_root() / "eisenia.md")
    if eisenia_meta:
        for k in ("bacs", "biomasa_kg", "produccion_lombricompost_kg_mes", "ultima_recolte"):
            if k in eisenia_meta:
                out["eisenia"][k] = eisenia_meta[k]
    # Si existe stock.md de aappma, sobrescribir Dendrobaena
    aappma_meta = _try_read(_aappma_file())
    if aappma_meta:
        if aappma_meta.get("dendrobaena_disponibles_g") is not None:
            try:
                out["dendrobaena"]["stock_g"] = int(aappma_meta["dendrobaena_disponibles_g"])
            except (TypeError, ValueError):
                pass
        if aappma_meta.get("dendrobaena_reservadas_g") is not None:
            try:
                out["dendrobaena"]["reservadas_g"] = int(aappma_meta["dendrobaena_reservadas_g"])
            except (TypeError, ValueError):
                pass
        if aappma_meta.get("proxima_entrega"):
            out["dendrobaena"]["proxima_entrega"] = str(aappma_meta["proxima_entrega"])
    out["ts"] = datetime.now().isoformat(timespec="seconds")
    return out
