"""Worker equipe: lista operateurs DI Environnement con estado."""
from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from claudio_tools.common import parse_frontmatter, vault

log = logging.getLogger("tablero.v2.workers.equipe")


def _iniciales(nombre: str) -> str:
    parts = [p for p in nombre.replace("·", " ").split() if p]
    if not parts:
        return "?"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()


def _mock() -> dict:
    ops = [
        {"id": "MARTIN", "nombre": "Pierre Martin", "rol": "Chef d'équipe SS3",
         "estado": "actif", "chantier_actual": "BORDEAUX NORD"},
        {"id": "LEROY", "nombre": "David Leroy", "rol": "Opérateur SS3",
         "estado": "actif", "chantier_actual": "BORDEAUX NORD"},
        {"id": "DUPONT", "nombre": "Marc Dupont", "rol": "Opérateur SS3",
         "estado": "actif", "chantier_actual": "BORDEAUX NORD"},
        {"id": "BERNARD", "nombre": "Lucas Bernard", "rol": "Chef d'équipe SS3",
         "estado": "actif", "chantier_actual": "LIMOGES CENTRE"},
        {"id": "MOREAU", "nombre": "Thomas Moreau", "rol": "Opérateur SS3",
         "estado": "formation", "chantier_actual": "LIMOGES CENTRE"},
        {"id": "ANGEL", "nombre": "Angel V.", "rol": "Conducteur de travaux",
         "estado": "actif", "chantier_actual": "—"},
    ]
    for op in ops:
        op["iniciales"] = _iniciales(op["nombre"])
    return {
        "operateurs": ops,
        "total": len(ops),
        "actifs": sum(1 for o in ops if o["estado"] == "actif"),
        "en_formation": sum(1 for o in ops if o["estado"] == "formation"),
        "ts": datetime.utcnow().isoformat(timespec="seconds") + "Z",
    }


async def equipe_tick() -> dict | None:
    d = vault() / "trabajo" / "equipe"
    if not d.exists():
        return _mock()
    ops: list[dict] = []
    try:
        for p in sorted(d.glob("*.md")):
            if p.stem.startswith("_"):
                continue
            try:
                meta, _ = parse_frontmatter(p.read_text(encoding="utf-8"))
            except Exception:
                continue
            if not meta:
                continue
            nombre = str(meta.get("nombre") or p.stem.replace("-", " ").title())
            estado_raw = str(meta.get("estado", "actif")).strip().lower()
            if estado_raw not in ("actif", "formation", "absent", "conge"):
                estado_raw = "actif"
            op_id = str(meta.get("id") or p.stem).upper()
            ops.append({
                "id": op_id,
                "nombre": nombre,
                "rol": str(meta.get("rol", "")),
                "estado": estado_raw,
                "chantier_actual": str(meta.get("chantier_actual", "")),
                "iniciales": _iniciales(nombre),
            })
    except Exception as e:
        log.debug(f"equipe: {e}")
        return _mock()
    if not ops:
        return _mock()
    return {
        "operateurs": ops,
        "total": len(ops),
        "actifs": sum(1 for o in ops if o["estado"] == "actif"),
        "en_formation": sum(1 for o in ops if o["estado"] == "formation"),
        "ts": datetime.utcnow().isoformat(timespec="seconds") + "Z",
    }
