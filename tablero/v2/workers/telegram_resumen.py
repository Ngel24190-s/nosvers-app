"""Worker telegram_resumen: últimos N mensajes del bot.

Lee /home/nosvers/bot/messages.jsonl o vault claudio/telegram/ si existen.
De lo contrario mock realista.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

log = logging.getLogger("tablero.v2.workers.telegram_resumen")


_LOG_PATHS = [
    Path("/home/nosvers/bot/messages.jsonl"),
    Path("/home/nosvers/logs/telegram.jsonl"),
]


def _mock() -> dict:
    return {
        "fuente": "mock",
        "total": 4,
        "items": [
            {"ts": "2026-05-14T19:45", "autor": "Angel", "texto": "Arranca proyecto 010"},
            {"ts": "2026-05-14T14:12", "autor": "claudio", "texto": "✅ Deploy 009 widgets ricos OK"},
            {"ts": "2026-05-14T08:30", "autor": "Angel", "texto": "Mira los pedidos Stripe de hoy"},
            {"ts": "2026-05-13T21:05", "autor": "claudio",
             "texto": "Pedido nuevo: 1 kit Extrait Vivant — Marie Dubois (45 €)"},
        ],
        "ts": datetime.now().isoformat(timespec="seconds"),
    }


async def telegram_resumen_tick() -> dict | None:
    for p in _LOG_PATHS:
        if not p.exists():
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        lines = [ln for ln in text.splitlines() if ln.strip()]
        items = []
        for raw in lines[-10:]:
            try:
                obj = json.loads(raw)
            except Exception:
                continue
            items.append({
                "ts": str(obj.get("ts") or obj.get("timestamp") or "")[:16],
                "autor": str(obj.get("autor") or obj.get("from") or "—"),
                "texto": str(obj.get("texto") or obj.get("text") or "")[:200],
            })
        if items:
            return {
                "fuente": str(p),
                "total": len(items),
                "items": items[::-1],  # más reciente primero
                "ts": datetime.now().isoformat(timespec="seconds"),
            }
    return _mock()
