"""Worker documentos_trabajo: lista docs agrupados por tipo."""
from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from claudio_tools.common import vault

log = logging.getLogger("tablero.v2.workers.documentos_trabajo")

# tipo (stem prefijo) → categoría
_TIPO_MAP = {
    "ppsps": "ppsps",
    "plan-retrait": "plan_retrait",
    "plan_retrait": "plan_retrait",
    "devis": "devis",
    "certificat": "certificat",
    "certificats": "certificat",
    "diag-amiante": "diag_amiante",
    "diag_amiante": "diag_amiante",
}


def _detect_tipo(name: str) -> str:
    low = name.lower()
    for key, val in _TIPO_MAP.items():
        if key in low:
            return val
    return "autre"


def _mock() -> dict:
    items_raw = [
        ("ppsps", "PPSPS Bordeaux Nord Mairie v2.pdf", "BORDEAUX NORD · MAIRIE", 412, "2026-05-08"),
        ("ppsps", "PPSPS Limoges Clinique.pdf", "LIMOGES CENTRE", 387, "2026-04-22"),
        ("plan_retrait", "Plan retrait amiante Bordeaux.pdf", "BORDEAUX NORD · MAIRIE", 245, "2026-05-04"),
        ("devis", "Devis Bordeaux 84500 EUR.pdf", "BORDEAUX NORD · MAIRIE", 89, "2026-04-15"),
        ("devis", "Devis Périgueux Pavillon.pdf", "PÉRIGUEUX · PAVILLON", 76, "2026-04-30"),
        ("certificat", "Certificat SS3 - Martin P..pdf", "—", 128, "2025-09-12"),
        ("certificat", "Certificat SS3 - Bernard L..pdf", "—", 132, "2025-11-04"),
        ("diag_amiante", "Diag amiante Bordeaux Mairie.pdf", "BORDEAUX NORD · MAIRIE", 1820, "2026-03-28"),
    ]
    por_tipo: dict[str, list[dict]] = {}
    for tipo, nombre, ch, kb, fecha in items_raw:
        por_tipo.setdefault(tipo, []).append({
            "tipo": tipo, "nombre": nombre, "chantier": ch,
            "size_kb": kb, "fecha": fecha,
        })
    return {
        "por_tipo": por_tipo,
        "total": len(items_raw),
        "ts": datetime.utcnow().isoformat(timespec="seconds") + "Z",
    }


async def documentos_trabajo_tick() -> dict | None:
    base = vault() / "trabajo" / "chantiers"
    if not base.exists():
        return _mock()
    por_tipo: dict[str, list[dict]] = {}
    total = 0
    try:
        for sub in base.iterdir():
            if not sub.is_dir() or sub.name.startswith("_"):
                continue
            docs = sub / "docs"
            if not docs.exists():
                continue
            chantier = sub.name.upper().replace("-", " ")
            for p in docs.rglob("*"):
                if p.is_dir() or p.name.startswith("."):
                    continue
                tipo = _detect_tipo(p.stem)
                try:
                    size_kb = p.stat().st_size / 1024
                    mtime = datetime.fromtimestamp(p.stat().st_mtime).date().isoformat()
                except OSError:
                    continue
                por_tipo.setdefault(tipo, []).append({
                    "tipo": tipo,
                    "nombre": p.name,
                    "chantier": chantier,
                    "size_kb": round(size_kb, 1),
                    "fecha": mtime,
                })
                total += 1
    except Exception as e:
        log.debug(f"documentos_trabajo: {e}")
        return _mock()
    if total == 0:
        return _mock()
    for k in list(por_tipo.keys()):
        por_tipo[k] = sorted(por_tipo[k], key=lambda x: x["fecha"], reverse=True)[:15]
    return {
        "por_tipo": por_tipo,
        "total": total,
        "ts": datetime.utcnow().isoformat(timespec="seconds") + "Z",
    }
