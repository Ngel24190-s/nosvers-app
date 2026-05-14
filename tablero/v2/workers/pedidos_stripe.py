"""Worker pedidos_stripe: lee nosvers/ventas/ o publica mock realista.

Si en el futuro se integra Stripe API, sustituir el bloque mock por la consulta.
"""
from __future__ import annotations

import logging
from datetime import date, datetime
from pathlib import Path

from claudio_tools.common import parse_frontmatter, vault

log = logging.getLogger("tablero.v2.workers.pedidos_stripe")


def _ventas_dir() -> Path:
    return vault() / "nosvers" / "ventas"


def _mock() -> dict:
    return {
        "mes_total_eur": 487.50,
        "pedidos_mes": 14,
        "ultimo": {
            "cliente": "Marie Dubois",
            "producto": "Extrait Vivant de Lombric · 500ml",
            "eur": 45.00,
            "fecha": "2026-05-14",
        },
        "club_subs": {
            "activos": 9,
            "nuevos_mes": 2,
            "mrr_eur": 135.00,
        },
        "ts": datetime.now().isoformat(timespec="seconds"),
    }


async def pedidos_stripe_tick() -> dict | None:
    d = _ventas_dir()
    if not d.exists():
        return _mock()
    mes_actual = date.today().strftime("%Y-%m")
    total = 0.0
    n = 0
    ultimo: dict | None = None
    ultima_fecha = ""
    try:
        for p in sorted(d.glob(f"{mes_actual}*.md"), reverse=True):
            try:
                text = p.read_text(encoding="utf-8")
            except Exception:
                continue
            meta, _body = parse_frontmatter(text)
            if not meta:
                continue
            try:
                eur = float(meta.get("eur") or meta.get("monto") or 0)
            except (TypeError, ValueError):
                continue
            fecha = str(meta.get("fecha", p.stem[:10]))
            total += eur
            n += 1
            if not ultimo or fecha > ultima_fecha:
                ultima_fecha = fecha
                ultimo = {
                    "cliente": str(meta.get("cliente", "")),
                    "producto": str(meta.get("producto", "")),
                    "eur": eur,
                    "fecha": fecha,
                }
    except Exception as e:
        log.debug(f"pedidos_stripe: {e}")
        return _mock()
    if n == 0:
        return _mock()
    return {
        "mes_total_eur": round(total, 2),
        "pedidos_mes": n,
        "ultimo": ultimo,
        "club_subs": _mock()["club_subs"],
        "ts": datetime.now().isoformat(timespec="seconds"),
    }
