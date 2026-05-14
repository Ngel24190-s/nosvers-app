"""Worker menu_dia: parsea menus/semana_actual.md y devuelve el día actual."""
from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from claudio_tools.common import vault

_DIAS = ["lunes", "martes", "miércoles", "miercoles",
        "jueves", "viernes", "sábado", "sabado", "domingo"]
_DIA_IDX = {
    "lunes": 0, "martes": 1, "miércoles": 2, "miercoles": 2,
    "jueves": 3, "viernes": 4, "sábado": 5, "sabado": 5, "domingo": 6,
}
_HEADER_RE = re.compile(r"^#{1,3}\s+(.+?)\s*$")


def _semana_file() -> Path:
    return vault() / "menus" / "semana_actual.md"


def _split_secciones(text: str) -> dict[str, str]:
    """Divide por headers (## día) y devuelve {dia_normalizado: contenido}."""
    out: dict[str, str] = {}
    actual = None
    buf: list[str] = []
    for line in text.splitlines():
        m = _HEADER_RE.match(line)
        if m:
            if actual:
                out[actual] = "\n".join(buf).strip()
            buf = []
            head = m.group(1).strip().lower()
            for d in _DIAS:
                if d in head:
                    actual = d
                    break
            else:
                actual = None
            continue
        if actual:
            buf.append(line)
    if actual:
        out[actual] = "\n".join(buf).strip()
    return out


async def menu_dia_tick() -> dict | None:
    path = _semana_file()
    if not path.exists():
        return {"empty": True}
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return {"empty": True}
    secciones = _split_secciones(text)
    if not secciones:
        return {"empty": True}
    hoy_idx = date.today().weekday()
    dia_nombre = None
    for d, idx in _DIA_IDX.items():
        if idx == hoy_idx and d in secciones:
            dia_nombre = d
            break
    if dia_nombre is None:
        return {"empty": True}
    body = secciones[dia_nombre]
    comida = ""
    cena = ""
    for line in body.splitlines():
        s = line.strip().lstrip("-*").strip()
        low = s.lower()
        if low.startswith("comida"):
            comida = s.split(":", 1)[-1].strip()
        elif low.startswith("cena"):
            cena = s.split(":", 1)[-1].strip()
    return {
        "dia": dia_nombre,
        "fecha": date.today().isoformat(),
        "comida": comida,
        "cena": cena,
        "raw": body[:400],
    }
