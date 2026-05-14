"""Worker tareas_dia: tareas granja del día (regar, plantar, cosechar)."""
from __future__ import annotations

import logging
from datetime import date, datetime
from pathlib import Path

from claudio_tools.common import vault

log = logging.getLogger("tablero.v2.workers.tareas_dia")


def _today_file() -> Path:
    return vault() / "nosvers" / "tareas" / f"{date.today().isoformat()}.md"


def _mock() -> dict:
    return {
        "fecha": date.today().isoformat(),
        "tareas": [
            {"texto": "Regar tomates Cœur de Bœuf y courgettes", "categoria": "huerto", "hecha": False, "prioridad": 1},
            {"texto": "Volteada bac compost #2 (semana 18)", "categoria": "compost", "hecha": False, "prioridad": 2},
            {"texto": "Pesar 400g Dendrobaena para AAPPMA Neuvic", "categoria": "aappma", "hecha": False, "prioridad": 1},
            {"texto": "Cosechar salades printemps maduras", "categoria": "huerto", "hecha": False, "prioridad": 2},
            {"texto": "Foto producto: kit Extrait Vivant nuevo embalaje", "categoria": "tienda", "hecha": True, "prioridad": 3},
        ],
        "total": 5,
        "pendientes": 4,
        "hechas": 1,
        "ts": datetime.now().isoformat(timespec="seconds"),
    }


def _parse_tareas(text: str) -> list[dict]:
    tareas: list[dict] = []
    for line in text.splitlines():
        s = line.strip()
        if not s.startswith("- ["):
            continue
        # - [ ] texto · #categoria
        hecha = "x" in s[3:5].lower()
        rest = s[5:].lstrip()
        if rest.startswith("]"):
            rest = rest[1:].lstrip()
        categoria = "general"
        if "#" in rest:
            texto, _, tail = rest.rpartition("#")
            texto = texto.strip().rstrip("·").rstrip()
            categoria = tail.strip().split()[0] if tail.strip() else "general"
        else:
            texto = rest
        tareas.append({
            "texto": texto[:180],
            "categoria": categoria,
            "hecha": hecha,
            "prioridad": 2,
        })
    return tareas


async def tareas_dia_tick() -> dict | None:
    p = _today_file()
    if not p.exists():
        return _mock()
    try:
        text = p.read_text(encoding="utf-8")
    except Exception as e:
        log.debug(f"tareas_dia: {e}")
        return _mock()
    tareas = _parse_tareas(text)
    if not tareas:
        return _mock()
    hechas = sum(1 for t in tareas if t["hecha"])
    return {
        "fecha": date.today().isoformat(),
        "tareas": tareas[:20],
        "total": len(tareas),
        "pendientes": len(tareas) - hechas,
        "hechas": hechas,
        "ts": datetime.now().isoformat(timespec="seconds"),
    }
