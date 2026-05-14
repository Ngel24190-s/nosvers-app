"""Worker search_console: impresiones / clicks / queries top.

Mock realista. TODO: Google Search Console API (oauth requerido).
"""
from __future__ import annotations

import logging
import random
from datetime import date, datetime, timedelta

log = logging.getLogger("tablero.v2.workers.search_console")


_QUERIES = [
    ("lombricompost dordogne", 28, 4, 8.4),
    ("vers de pêche neuvic", 22, 6, 4.1),
    ("extrait vivant lombric", 18, 5, 6.2),
    ("ferme sol vivant nouvelle aquitaine", 15, 2, 12.3),
    ("eisenia foetida vente", 12, 3, 7.8),
    ("dendrobaena aappma", 9, 4, 3.5),
    ("compost actif liquide", 7, 1, 14.1),
    ("microbiome sol jardin", 5, 0, 21.0),
]


async def search_console_tick() -> dict | None:
    rng = random.Random(date.today().toordinal())
    today = date.today()
    series_28d: list[dict] = []
    for i in range(28, 0, -1):
        d = today - timedelta(days=i)
        impr = int(120 + (28 - i) * 4 + rng.uniform(-30, 30))
        clicks = max(0, int(impr * rng.uniform(0.05, 0.12)))
        series_28d.append({"fecha": d.isoformat(), "impresiones": impr, "clicks": clicks})
    total_impr = sum(s["impresiones"] for s in series_28d)
    total_clicks = sum(s["clicks"] for s in series_28d)
    ctr = (total_clicks / total_impr * 100) if total_impr else 0.0
    queries = [
        {"query": q, "impresiones": impr, "clicks": clk, "posicion_media": round(pos, 1)}
        for (q, impr, clk, pos) in _QUERIES
    ]
    return {
        "fuente": "mock",
        "rango_dias": 28,
        "total_impresiones": total_impr,
        "total_clicks": total_clicks,
        "ctr_pct": round(ctr, 2),
        "posicion_media": 8.6,
        "queries_top": queries,
        "series": series_28d,
        "ts": datetime.now().isoformat(timespec="seconds"),
    }
