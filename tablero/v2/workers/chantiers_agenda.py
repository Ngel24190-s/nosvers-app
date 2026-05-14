"""Worker chantiers_agenda: eventos del día desde journals o mock."""
from __future__ import annotations

import logging
import re
from datetime import date, datetime
from pathlib import Path

from claudio_tools.common import vault

log = logging.getLogger("tablero.v2.workers.chantiers_agenda")

_EVENT_RE = re.compile(
    r"^##\s+(?P<hora>\d{1,2}:\d{2})\s*·\s*(?P<tipo>\w+)(?:\s*·\s*(?P<resto>.+))?\s*$"
)


def _mock() -> dict:
    hoy = date.today().isoformat()
    return {
        "fecha": hoy,
        "eventos": [
            {
                "hora": "08:30",
                "chantier": "BORDEAUX NORD · MAIRIE",
                "tipo": "visita",
                "descripcion": "Inspection plan retrait amiante",
                "operateurs": ["MARTIN", "LEROY"],
            },
            {
                "hora": "11:00",
                "chantier": "LIMOGES CENTRE",
                "tipo": "livraison",
                "descripcion": "Livraison combinaisons type 5 + filtres",
                "operateurs": ["BERNARD"],
            },
            {
                "hora": "14:30",
                "chantier": "BORDEAUX NORD · MAIRIE",
                "tipo": "rdv_client",
                "descripcion": "Point hebdo avec Mme Roux (Mairie)",
                "operateurs": ["ANGEL"],
            },
            {
                "hora": "16:00",
                "chantier": "PÉRIGUEUX · PAVILLON",
                "tipo": "reunion",
                "descripcion": "Briefing équipe démarrage chantier",
                "operateurs": ["MARTIN", "ANGEL"],
            },
        ],
        "total": 4,
        "ts": datetime.utcnow().isoformat(timespec="seconds") + "Z",
    }


async def chantiers_agenda_tick() -> dict | None:
    """Lee `trabajo/chantiers/*/journal/<hoy>.md` para eventos del día."""
    d = vault() / "trabajo" / "chantiers"
    if not d.exists():
        return _mock()
    hoy = date.today().isoformat()
    eventos: list[dict] = []
    try:
        for sub in sorted(d.iterdir()):
            if not sub.is_dir() or sub.name.startswith("_"):
                continue
            jpath = sub / "journal" / f"{hoy}.md"
            if not jpath.exists():
                continue
            try:
                text = jpath.read_text(encoding="utf-8")
            except Exception:
                continue
            chantier_nombre = sub.name.upper().replace("-", " ")
            for line in text.splitlines():
                m = _EVENT_RE.match(line)
                if not m:
                    continue
                eventos.append({
                    "hora": m.group("hora"),
                    "chantier": chantier_nombre,
                    "tipo": (m.group("tipo") or "autre").lower(),
                    "descripcion": (m.group("resto") or "").strip(),
                    "operateurs": [],
                })
    except Exception as e:
        log.debug(f"chantiers_agenda: {e}")
        return _mock()
    if not eventos:
        return _mock()
    eventos.sort(key=lambda e: e["hora"])
    return {
        "fecha": hoy,
        "eventos": eventos[:30],
        "total": len(eventos),
        "ts": datetime.utcnow().isoformat(timespec="seconds") + "Z",
    }
