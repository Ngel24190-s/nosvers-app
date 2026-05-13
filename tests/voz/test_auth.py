"""T014 — Tests unitarios de voz.auth."""
from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone

import jwt
import pytest

from voz import auth


def test_emitir_y_validar_token(auth_temporal):
    res = auth.emitir_token("movil-angel", ttl_days=30)
    assert res["device"] == "movil-angel"
    assert res["autor"] == "angel"   # default
    assert "jwt" in res
    assert "jti" in res

    payload = auth.validar_token(res["jwt"])
    assert payload is not None
    assert payload["device"] == "movil-angel"
    assert payload["jti"] == res["jti"]
    assert payload["sub"] == "angel"


def test_validar_token_invalido(auth_temporal):
    assert auth.validar_token("no-es-un-jwt") is None
    assert auth.validar_token("") is None
    assert auth.validar_token(None) is None  # type: ignore


def test_revocar_token(auth_temporal):
    res = auth.emitir_token("dispositivo-x")
    assert auth.validar_token(res["jwt"]) is not None
    ok = auth.revocar_token(res["jti"])
    assert ok is True
    assert auth.validar_token(res["jwt"]) is None


def test_revocar_token_inexistente(auth_temporal):
    assert auth.revocar_token("jti-que-no-existe") is False


def test_token_expirado(auth_temporal, monkeypatch):
    # Emite con TTL muy corto (ttl_days mínimo es int, así que firmamos a mano)
    secret = "test-secret-only-for-pytest-do-not-use-in-prod"
    now = datetime.now(timezone.utc)
    exp = now - timedelta(minutes=1)  # ya expirado
    payload = {"jti": "expired-jti", "device": "x", "iat": int(now.timestamp()),
               "exp": int(exp.timestamp()), "sub": "angel"}
    token = jwt.encode(payload, secret, algorithm="HS256")
    # Registra el jti para que el test no lo descarte por "no fue emitido por nosotros"
    with auth._conn() as c:
        c.execute("INSERT INTO tokens(jti, device_label, issued_at, expires_at) VALUES(?,?,?,?)",
                  ("expired-jti", "x", now.isoformat(), exp.isoformat()))
    assert auth.validar_token(token) is None


def test_token_con_firma_correcta_pero_sin_registro(auth_temporal):
    """JWT firmado con el secret correcto pero NO emitido por nosotros → None."""
    secret = "test-secret-only-for-pytest-do-not-use-in-prod"
    now = datetime.now(timezone.utc)
    payload = {
        "jti": "huerfano-jti",
        "device": "x",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(days=1)).timestamp()),
        "sub": "angel",
    }
    token = jwt.encode(payload, secret, algorithm="HS256")
    assert auth.validar_token(token) is None


def test_listar_tokens(auth_temporal):
    auth.emitir_token("d1")
    auth.emitir_token("d2")
    activos = auth.listar_tokens()
    assert len(activos) == 2

    # Revoca uno y verifica filtrado
    primer_jti = activos[0]["jti"]
    auth.revocar_token(primer_jti)
    activos_post = auth.listar_tokens()
    assert len(activos_post) == 1

    todos = auth.listar_tokens(incluir_revocados=True)
    assert len(todos) == 2


def test_emitir_token_con_autor_africa(auth_temporal):
    """BRIEF §14: device puede asociarse a 'africa' vía parámetro autor."""
    res = auth.emitir_token("movil-africa", ttl_days=365, autor="africa")
    assert res["device"] == "movil-africa"
    assert res["autor"] == "africa"
    payload = auth.validar_token(res["jwt"])
    assert payload is not None
    assert payload["sub"] == "africa"


def test_emitir_token_autor_invalido_lanza_error(auth_temporal):
    """Autor desconocido → ValueError (no se emite token)."""
    with pytest.raises(ValueError):
        auth.emitir_token("d", autor="inventado")
