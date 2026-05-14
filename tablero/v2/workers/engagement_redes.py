"""Worker engagement_redes: IG/YT/FB últimos 7 días.

Lee logs de agt02_instagram / agt07_youtube / agt08_facebook si presentes;
de lo contrario mock realista.
"""
from __future__ import annotations

import logging
import random
from datetime import date, datetime
from pathlib import Path

log = logging.getLogger("tablero.v2.workers.engagement_redes")


LOGS_DIR = Path("/home/nosvers/logs")


def _count_recent_lines(name: str, days: int = 7) -> int:
    p = LOGS_DIR / f"{name}.log"
    if not p.exists():
        return 0
    try:
        text = p.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return 0
    # Crude: count lines containing today-7..today
    from datetime import timedelta
    today = date.today()
    accepted = {(today - timedelta(days=i)).isoformat() for i in range(days)}
    n = 0
    for line in text.splitlines():
        for d in accepted:
            if d in line:
                n += 1
                break
    return n


async def engagement_redes_tick() -> dict | None:
    rng = random.Random(date.today().toordinal())
    ig_logs = _count_recent_lines("agt02_instagram")
    yt_logs = _count_recent_lines("agt07_youtube")
    fb_logs = _count_recent_lines("agt08_facebook")
    return {
        "fuente": "mock" if (ig_logs + yt_logs + fb_logs) == 0 else "logs+mock",
        "rango_dias": 7,
        "instagram": {
            "followers": 318,
            "posts_semana": 5,
            "likes_total": 412 + rng.randint(-30, 30),
            "comments_total": 36 + rng.randint(-5, 8),
            "engagement_rate_pct": 4.2,
            "agente_logs_semana": ig_logs,
        },
        "youtube": {
            "subs": 47,
            "videos_semana": 0,
            "views_semana": 124 + rng.randint(-20, 20),
            "watch_time_min": 215,
            "agente_logs_semana": yt_logs,
        },
        "facebook": {
            "page_likes": 89,
            "posts_semana": 2,
            "reach": 1450 + rng.randint(-100, 200),
            "engagements": 78 + rng.randint(-10, 15),
            "agente_logs_semana": fb_logs,
        },
        "ts": datetime.now().isoformat(timespec="seconds"),
    }
