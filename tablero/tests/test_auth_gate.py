"""T016 — auth gate smoke tests."""
from __future__ import annotations


def test_health_no_auth_required(client):
    r = client.get("/tablero/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["service"] == "tablero"


def test_whoami_without_token_returns_401(client):
    r = client.get("/tablero/api/whoami")
    assert r.status_code == 401
    body = r.json()
    assert body["ok"] is False
    assert body["error"] == "auth_invalido"


def test_whoami_with_angel_token_ok(client, angel_token):
    r = client.get("/tablero/api/whoami", headers={"Authorization": f"Bearer {angel_token}"})
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["identidad"]["sub"] == "angel"
    assert body["identidad"]["device"] == "pytest-angel"
    assert body["identidad"]["exp"] > 0


def test_whoami_with_africa_token_ok(client, africa_token):
    r = client.get("/tablero/api/whoami", headers={"Authorization": f"Bearer {africa_token}"})
    assert r.status_code == 200
    assert r.json()["identidad"]["sub"] == "africa"


def test_garbage_token_returns_401(client):
    r = client.get("/tablero/api/whoami", headers={"Authorization": "Bearer not-a-real-jwt"})
    assert r.status_code == 401
    assert r.json()["error"] == "auth_invalido"


def test_malformed_authorization_header(client):
    r = client.get("/tablero/api/whoami", headers={"Authorization": "Token foo"})
    assert r.status_code == 401
