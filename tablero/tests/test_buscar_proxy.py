"""T034 — search endpoint smoke tests (proxy over voz.buscar.dia_buscar_impl)."""
from __future__ import annotations


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_buscar_empty_q_returns_400(client, angel_token):
    r = client.get("/tablero/api/buscar?q=", headers=_auth(angel_token))
    assert r.status_code == 400
    assert r.json()["error"] == "input_vacio"


def test_buscar_unauth(client):
    r = client.get("/tablero/api/buscar?q=anything")
    assert r.status_code == 401


def test_buscar_no_matches_returns_empty_list(client, angel_token):
    # A query that's extremely unlikely to match anything in the vault.
    r = client.get(
        "/tablero/api/buscar?q=zzzqqqxxxnomatchverylongstring42",
        headers=_auth(angel_token),
    )
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["total"] == 0
    assert body["resultados"] == []


def test_buscar_returns_results_shape(client, angel_token):
    # Use a generic stopword that likely matches at least one note. We don't
    # assert non-empty, just shape correctness when results exist.
    r = client.get("/tablero/api/buscar?q=test", headers=_auth(angel_token))
    assert r.status_code == 200
    body = r.json()
    for hit in body["resultados"]:
        assert hit["autor"] in {"angel", "africa"}
        assert "fecha" in hit and "ts" in hit and "fragmento" in hit
