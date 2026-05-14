"""Worker comentarios_wp: comentarios pendientes moderar.

Lee WP REST `/wp-json/wp/v2/comments?status=hold` si WP_BASE_URL y WP_TOKEN
están en env. De lo contrario mock realista.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime

log = logging.getLogger("tablero.v2.workers.comentarios_wp")


def _mock() -> dict:
    return {
        "fuente": "mock",
        "pendientes": 3,
        "items": [
            {"id": 101, "autor": "Marie L.", "post": "Lombricompost · le guide complet",
             "extracto": "Bonjour, j'ai une question sur la quantité d'eau...",
             "fecha": "2026-05-13"},
            {"id": 102, "autor": "Pierre M.", "post": "Pourquoi vos vers ne meurent pas en hiver",
             "extracto": "Excellent article, merci. Une précision sur l'humidité...",
             "fecha": "2026-05-12"},
            {"id": 103, "autor": "anonymous_3xz",
             "post": "Extrait Vivant de Lombric · mode d'emploi",
             "extracto": "Spam con enlace sospechoso, debería filtrarse...",
             "fecha": "2026-05-14"},
        ],
        "ts": datetime.now().isoformat(timespec="seconds"),
    }


async def comentarios_wp_tick() -> dict | None:
    base = os.getenv("WP_BASE_URL") or ""
    token = os.getenv("WP_TOKEN") or ""
    if not base or not token:
        return _mock()
    # Fetch real WP REST. Best-effort: si falla, mock.
    try:
        import urllib.request  # local import para no pagar si no se usa
        import json

        url = base.rstrip("/") + "/wp-json/wp/v2/comments?status=hold&per_page=20"
        req = urllib.request.Request(url, headers={
            "Authorization": f"Bearer {token}",
            "User-Agent": "tablero-v2/comentarios_wp",
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        items = []
        for c in data[:10] if isinstance(data, list) else []:
            items.append({
                "id": c.get("id"),
                "autor": c.get("author_name") or "anon",
                "post": str(c.get("post") or "—"),
                "extracto": (c.get("content", {}).get("rendered") or "")[:200],
                "fecha": (c.get("date") or "")[:10],
            })
        return {
            "fuente": "wp_rest",
            "pendientes": len(items),
            "items": items,
            "ts": datetime.now().isoformat(timespec="seconds"),
        }
    except Exception as e:
        log.debug(f"comentarios_wp wp_rest fallback to mock: {e}")
        return _mock()
