"""Tests JWT contexts (007).

Cubre:
- emisión Angel con 3 contextos por default
- emisión África con 2 contextos por default
- prohibición de África + trabajo
- check_context casos válidos / inválidos
- retro-compat con tokens sin `available_contexts`

Aísla la DB monkeypatcheando `voz.auth.DB_PATH` y `DATA_DIR` a /tmp
para NO tocar la DB de producción.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest

os.environ.setdefault("VOZ_JWT_SECRET", "test-007-secret")

import jwt as _jwt  # noqa: E402

from voz import auth as _auth_mod  # noqa: E402
from voz.auth import (  # noqa: E402
    CONTEXTS_ANGEL,
    CONTEXTS_DEFAULT,
    check_context,
    emitir_token,
    validar_token,
)

TEST_DATA = Path("/tmp/test_007_voz_data")
TEST_DB = TEST_DATA / "tokens.sqlite"


@pytest.fixture(autouse=True)
def _isolate_db(monkeypatch):
    """Redirige DB_PATH / DATA_DIR a /tmp para NO tocar la DB prod."""
    TEST_DATA.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(_auth_mod, "DATA_DIR", TEST_DATA)
    monkeypatch.setattr(_auth_mod, "DB_PATH", TEST_DB)
    try:
        TEST_DB.unlink()
    except FileNotFoundError:
        pass
    yield
    try:
        TEST_DB.unlink()
    except FileNotFoundError:
        pass


def test_angel_default_contexts():
    t = emitir_token("dev-test-1", autor="angel")
    assert t["available_contexts"] == CONTEXTS_ANGEL
    payload = validar_token(t["jwt"])
    assert payload is not None
    assert payload["available_contexts"] == CONTEXTS_ANGEL


def test_africa_default_contexts():
    t = emitir_token("dev-test-2", autor="africa")
    assert t["available_contexts"] == CONTEXTS_DEFAULT
    assert "trabajo" not in t["available_contexts"]


def test_africa_no_trabajo():
    with pytest.raises(ValueError, match="trabajo"):
        emitir_token("dev-test-3", autor="africa",
                     contexts=["casa", "trabajo"])


def test_check_context_angel_trabajo():
    t = emitir_token("dev-test-4", autor="angel")
    p = validar_token(t["jwt"])
    assert check_context(p, "trabajo") is True
    assert check_context(p, "casa") is True
    assert check_context(p, "nosvers") is True


def test_check_context_africa_trabajo_denied():
    t = emitir_token("dev-test-5", autor="africa")
    p = validar_token(t["jwt"])
    assert check_context(p, "trabajo") is False
    assert check_context(p, "casa") is True
    assert check_context(p, "nosvers") is True


def test_check_context_invalido():
    t = emitir_token("dev-test-6", autor="angel")
    p = validar_token(t["jwt"])
    assert check_context(p, "foo") is False
    assert check_context(p, "") is False
    assert check_context(None, "casa") is False


def test_retrocompat_token_sin_contexts():
    """Token firmado a mano sin available_contexts → default no incluye trabajo."""
    from voz.auth import _secret, ALGORITHM, _conn
    import uuid
    import datetime as dt
    jti = str(uuid.uuid4())
    now = dt.datetime.now(dt.timezone.utc)
    exp = now + dt.timedelta(days=1)
    payload = {
        "jti": jti,
        "device": "old-client",
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
        "sub": "angel",
        # NO available_contexts
    }
    token = _jwt.encode(payload, _secret(), algorithm=ALGORITHM)
    # Registrar para que validar lo acepte
    with _conn() as c:
        c.execute(
            "INSERT INTO tokens(jti, device_label, issued_at, expires_at) VALUES(?,?,?,?)",
            (jti, "old-client", now.isoformat(), exp.isoformat()),
        )
    p = validar_token(token)
    assert p is not None
    # default = ["casa","nosvers"] → trabajo denegado incluso siendo angel
    # (check_context tiene defensa adicional, pero el default tampoco lo incluye)
    assert check_context(p, "casa") is True
    assert check_context(p, "nosvers") is True
    assert check_context(p, "trabajo") is False
