"""Worker gastos: parsea finanzas/gastos/YYYY-MM.md + mes anterior."""
from __future__ import annotations

import re
from datetime import date, timedelta
from pathlib import Path

from claudio_tools.common import vault

_LINE_RE = re.compile(
    r"^- (\d{4}-\d{2}-\d{2}) \d{2}:\d{2} · ([\d.]+)€ · (.+?) · (\w+) · (\w+)\s*$"
)


def _gastos_file(yyyy_mm: str) -> Path:
    return vault() / "finanzas" / "gastos" / f"{yyyy_mm}.md"


def _parse_mes(yyyy_mm: str) -> tuple[dict[str, float], float, int]:
    path = _gastos_file(yyyy_mm)
    if not path.exists():
        return {}, 0.0, 0
    by_cat: dict[str, float] = {}
    total = 0.0
    n = 0
    try:
        for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
            m = _LINE_RE.match(raw.strip())
            if not m:
                continue
            try:
                monto = float(m.group(2))
            except ValueError:
                continue
            cat = m.group(4)
            by_cat[cat] = by_cat.get(cat, 0.0) + monto
            total += monto
            n += 1
    except Exception:
        return {}, 0.0, 0
    return by_cat, total, n


async def gastos_tick() -> dict | None:
    hoy = date.today()
    mes = hoy.strftime("%Y-%m")
    prev = (hoy.replace(day=1) - timedelta(days=1)).strftime("%Y-%m")
    by_cat, total, n = _parse_mes(mes)
    _prev_by_cat, total_prev, _n_prev = _parse_mes(prev)
    if total == 0 and total_prev == 0:
        return {"empty": True}
    return {
        "mes": mes,
        "total_mes_eur": round(total, 2),
        "total_mes_anterior_eur": round(total_prev, 2),
        "delta_vs_anterior_eur": round(total - total_prev, 2),
        "por_categoria": {k: round(v, 2) for k, v in by_cat.items()},
        "n_apuntes": n,
    }
