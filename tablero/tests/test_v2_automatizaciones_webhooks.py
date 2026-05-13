"""Test verificación firma Stripe."""
from __future__ import annotations

import hashlib
import hmac
import time

from tablero.v2.automatizaciones.webhooks import verify_stripe_signature


def _sign(payload: bytes, secret: str, ts: int) -> str:
    signed = f"{ts}.".encode() + payload
    v1 = hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
    return f"t={ts},v1={v1}"


def test_firma_valida():
    secret = "whsec_test"
    payload = b'{"type":"payment_intent.succeeded"}'
    ts = int(time.time())
    sig = _sign(payload, secret, ts)
    assert verify_stripe_signature(payload, sig, secret) is True


def test_firma_invalida():
    secret = "whsec_test"
    payload = b'{"type":"x"}'
    ts = int(time.time())
    sig = _sign(payload, "OTRA_SECRET", ts)
    assert verify_stripe_signature(payload, sig, secret) is False


def test_firma_caducada():
    secret = "whsec_test"
    payload = b'{}'
    ts = int(time.time()) - 1000  # fuera de tolerancia 300s
    sig = _sign(payload, secret, ts)
    assert verify_stripe_signature(payload, sig, secret) is False


def test_header_vacio():
    assert verify_stripe_signature(b"x", "", "s") is False
    assert verify_stripe_signature(b"x", "t=1,v1=zzz", "") is False
