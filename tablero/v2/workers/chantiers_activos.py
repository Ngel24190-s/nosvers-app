"""Worker chantiers_activos: snapshot rico para tab Aujourd'hui + Chantiers."""
from __future__ import annotations

import logging
from datetime import date, datetime
from pathlib import Path

from claudio_tools.common import parse_frontmatter, vault

log = logging.getLogger("tablero.v2.workers.chantiers_activos")


def _chantiers_dir() -> Path:
    return vault() / "trabajo" / "chantiers"


def _mock() -> dict:
    return {
        "total": 3,
        "urgentes": 1,
        "en_cours": 1,
        "debut": 1,
        "items": [
            {
                "slug": "bordeaux-nord-mairie",
                "nombre": "BORDEAUX NORD · MAIRIE",
                "cliente": "Mairie de Bordeaux",
                "direccion": "12 rue Lavoisier · 33000",
                "devis_eur": 84500,
                "estado": "urgente",
                "fecha_inicio": "2026-05-02",
                "fecha_fin_prev": "2026-05-25",
                "dias_restantes": 11,
                "equipe_ids": ["MARTIN", "LEROY", "DUPONT"],
            },
            {
                "slug": "limoges-centre-clinique",
                "nombre": "LIMOGES CENTRE · CLINIQUE ST PIERRE",
                "cliente": "Clinique Saint Pierre",
                "direccion": "8 av. Garibaldi · 87000",
                "devis_eur": 42300,
                "estado": "en_cours",
                "fecha_inicio": "2026-04-28",
                "fecha_fin_prev": "2026-06-12",
                "dias_restantes": 29,
                "equipe_ids": ["BERNARD", "MOREAU"],
            },
            {
                "slug": "perigueux-pavillon-prive",
                "nombre": "PÉRIGUEUX · PAVILLON RIVE GAUCHE",
                "cliente": "M. & Mme Lefèvre",
                "direccion": "rue des Tilleuls · 24000",
                "devis_eur": 18900,
                "estado": "debut",
                "fecha_inicio": "2026-05-20",
                "fecha_fin_prev": "2026-06-05",
                "dias_restantes": 22,
                "equipe_ids": ["MARTIN", "ANGEL"],
            },
        ],
        "ts": datetime.utcnow().isoformat(timespec="seconds") + "Z",
    }


def _dias_restantes(fecha_fin: str) -> int | None:
    if not fecha_fin:
        return None
    try:
        f = date.fromisoformat(fecha_fin)
        return (f - date.today()).days
    except (ValueError, TypeError):
        return None


async def chantiers_activos_tick() -> dict | None:
    d = _chantiers_dir()
    if not d.exists():
        return _mock()
    items: list[dict] = []
    try:
        for sub in sorted(d.iterdir()):
            if not sub.is_dir() or sub.name.startswith("_"):
                continue
            idx = sub / "INDEX.md"
            if not idx.exists():
                continue
            try:
                meta, _ = parse_frontmatter(idx.read_text(encoding="utf-8"))
            except Exception:
                continue
            if not meta:
                continue
            estado_raw = str(meta.get("estado", "en_cours")).strip().lower()
            # Normalizar estados a los 5 que conoce el widget
            if estado_raw in ("activo", "active"):
                estado = "en_cours"
            elif estado_raw == "urgente":
                estado = "urgente"
            elif estado_raw in ("debut", "début", "iniciado", "inicio"):
                estado = "debut"
            elif estado_raw == "pausado":
                estado = "pausado"
            elif estado_raw in ("archivado", "fini", "terminé"):
                estado = "archivado"
            else:
                estado = "en_cours"
            if estado == "archivado":
                continue
            equipe = meta.get("equipe") or meta.get("equipe_ids") or []
            if isinstance(equipe, str):
                equipe = [e.strip() for e in equipe.split(",") if e.strip()]
            try:
                devis = float(meta.get("devis_eur") or meta.get("devis") or 0)
            except (TypeError, ValueError):
                devis = 0.0
            items.append({
                "slug": sub.name,
                "nombre": str(meta.get("nombre", sub.name)).upper(),
                "cliente": str(meta.get("cliente", "—")),
                "direccion": str(meta.get("direccion", "")),
                "devis_eur": int(devis),
                "estado": estado,
                "fecha_inicio": str(meta.get("fecha_inicio", "")),
                "fecha_fin_prev": str(meta.get("fecha_fin_prev", "")),
                "dias_restantes": _dias_restantes(str(meta.get("fecha_fin_prev", ""))),
                "equipe_ids": list(equipe)[:8],
            })
    except Exception as e:
        log.debug(f"chantiers_activos: {e}")
        return _mock()
    if not items:
        return _mock()
    urg = sum(1 for it in items if it["estado"] == "urgente")
    ec = sum(1 for it in items if it["estado"] == "en_cours")
    deb = sum(1 for it in items if it["estado"] == "debut")
    return {
        "total": len(items),
        "urgentes": urg,
        "en_cours": ec,
        "debut": deb,
        "items": items[:20],
        "ts": datetime.utcnow().isoformat(timespec="seconds") + "Z",
    }
