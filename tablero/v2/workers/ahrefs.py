"""Worker ahrefs: DR / backlinks / referring domains.

Mock realista. TODO: Ahrefs API si se contrata plan.
"""
from __future__ import annotations

import logging
from datetime import datetime

log = logging.getLogger("tablero.v2.workers.ahrefs")


async def ahrefs_tick() -> dict | None:
    return {
        "fuente": "mock",
        "dominio": "nosvers.com",
        "domain_rating": 8,
        "url_rating": 12,
        "backlinks": 47,
        "referring_domains": 18,
        "organic_keywords": 92,
        "organic_traffic": 156,
        "top_backlinks": [
            {"url": "https://terreetnature.fr/blogue/sols-vivants", "dr": 32,
             "anchor": "ferme NosVers en Dordogne"},
            {"url": "https://lombricompost-info.fr/producteurs", "dr": 24,
             "anchor": "extrait vivant de lombric"},
            {"url": "https://forum-permaculture.fr/t/lombricompost", "dr": 18,
             "anchor": "NosVers"},
        ],
        "ts": datetime.now().isoformat(timespec="seconds"),
    }
