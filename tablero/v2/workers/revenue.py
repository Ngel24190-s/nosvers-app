"""Worker revenue: stripe API si STRIPE_SECRET_KEY, sino placeholder."""
from __future__ import annotations

import os
import time
import logging
from datetime import datetime

log = logging.getLogger("tablero.v2.workers.revenue")

TARGET_EUR = float(os.getenv("NOSVERS_REVENUE_TARGET", "600"))

try:
    import stripe  # type: ignore
    _STRIPE_OK = True
except ImportError:
    stripe = None  # type: ignore
    _STRIPE_OK = False


async def revenue_tick() -> dict:
    api_key = os.getenv("STRIPE_SECRET_KEY", "")
    if not (_STRIPE_OK and api_key):
        return {
            "day_eur": 0,
            "month_eur": 0,
            "target_eur": TARGET_EUR,
            "blocked": True,
            "last_payment": None,
        }
    try:
        stripe.api_key = api_key  # type: ignore[attr-defined]
        now = datetime.utcnow()
        day_start = int(datetime(now.year, now.month, now.day).timestamp())
        month_start = int(datetime(now.year, now.month, 1).timestamp())
        # Charges del mes
        charges = stripe.Charge.list(  # type: ignore[attr-defined]
            limit=100,
            created={"gte": month_start},
        )
        day_total = 0
        month_total = 0
        last_payment = None
        for ch in charges.auto_paging_iter():
            if not ch.get("paid"):
                continue
            amount = ch.get("amount", 0) / 100.0  # cents → EUR
            month_total += amount
            if ch.get("created", 0) >= day_start:
                day_total += amount
            if last_payment is None or ch.get("created", 0) > last_payment.get("ts", 0):
                desc = ch.get("description") or ch.get("statement_descriptor") or "Stripe"
                last_payment = {
                    "amount_eur": amount,
                    "desc": str(desc)[:60],
                    "ts": int(ch.get("created", 0)),
                }
        return {
            "day_eur": round(day_total, 2),
            "month_eur": round(month_total, 2),
            "target_eur": TARGET_EUR,
            "blocked": False,
            "last_payment": last_payment,
        }
    except Exception as e:
        log.warning(f"revenue stripe error: {e}")
        return {
            "day_eur": 0,
            "month_eur": 0,
            "target_eur": TARGET_EUR,
            "blocked": True,
            "last_payment": None,
            "error": str(e)[:100],
        }
