"""Worker web_traffic: visitas nosvers.com últimos 30 días.

Mock realista basado en patrón típico de blog SEO emergente.
TODO: integrar Plausible / GA4 si se configura.
"""
from __future__ import annotations

import logging
import random
from datetime import date, datetime, timedelta

log = logging.getLogger("tablero.v2.workers.web_traffic")


def _generate_series() -> list[dict]:
    """30 días, baseline 80 visitas/día, fines semana +30%, ruido ±25%."""
    rng = random.Random(date.today().toordinal())
    series: list[dict] = []
    today = date.today()
    for i in range(30, 0, -1):
        d = today - timedelta(days=i)
        baseline = 80
        if d.weekday() >= 5:
            baseline = int(baseline * 1.3)
        # tendencia mes: +0.6 visitas/día
        baseline += (30 - i) * 0.6
        visitas = max(5, int(baseline + rng.uniform(-baseline * 0.25, baseline * 0.25)))
        pagevisits = int(visitas * rng.uniform(1.4, 2.1))
        series.append({"fecha": d.isoformat(), "visitas": visitas, "paginas_vistas": pagevisits})
    return series


async def web_traffic_tick() -> dict | None:
    series = _generate_series()
    total_visitas = sum(s["visitas"] for s in series)
    total_paginas = sum(s["paginas_vistas"] for s in series)
    visitas_hoy = series[-1]["visitas"] if series else 0
    visitas_ayer = series[-2]["visitas"] if len(series) > 1 else 0
    return {
        "fuente": "mock",
        "dominio": "nosvers.com",
        "rango_dias": 30,
        "total_visitas": total_visitas,
        "total_paginas": total_paginas,
        "visitas_hoy": visitas_hoy,
        "visitas_ayer": visitas_ayer,
        "delta_dia": visitas_hoy - visitas_ayer,
        "series": series,
        "ts": datetime.now().isoformat(timespec="seconds"),
    }
