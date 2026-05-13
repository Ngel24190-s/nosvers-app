"""Verificación de firmas de webhooks externos."""
from __future__ import annotations

import hashlib
import hmac
import logging
import time

log = logging.getLogger("tablero.v2.automatizaciones.webhooks")

STRIPE_TOLERANCE_S = 300


def verify_stripe_signature(payload: bytes, sig_header: str, secret: str) -> bool:
    """Verifica un header Stripe-Signature `t=...,v1=...`.

    Equivalente a stripe.Webhook.construct_event pero sin dep duro al SDK.
    """
    if not sig_header or not secret:
        return False
    parts = {}
    for kv in sig_header.split(","):
        if "=" in kv:
            k, _, v = kv.partition("=")
            parts.setdefault(k.strip(), []).append(v.strip())
    ts_list = parts.get("t") or []
    v1_list = parts.get("v1") or []
    if not ts_list or not v1_list:
        return False
    try:
        ts = int(ts_list[0])
    except ValueError:
        return False
    if abs(time.time() - ts) > STRIPE_TOLERANCE_S:
        log.warning(f"stripe signature timestamp fuera de tolerancia: {ts}")
        return False
    signed_payload = f"{ts}.".encode() + payload
    expected = hmac.new(secret.encode(), signed_payload, hashlib.sha256).hexdigest()
    for v1 in v1_list:
        if hmac.compare_digest(expected, v1):
            return True
    return False
