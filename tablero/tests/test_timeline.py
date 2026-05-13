"""T019 + T028 — timeline endpoint smoke tests."""
from __future__ import annotations


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_timeline_default_returns_ok(client, angel_token):
    r = client.get("/tablero/api/timeline", headers=_auth(angel_token))
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert isinstance(body["entradas"], list)
    assert "rango" in body
    assert "desde" in body["rango"] and "hasta" in body["rango"]
    # Default range is last 30 days
    desde, hasta = body["rango"]["desde"], body["rango"]["hasta"]
    assert desde <= hasta


def test_timeline_entries_have_required_fields(client, angel_token):
    r = client.get("/tablero/api/timeline", headers=_auth(angel_token))
    body = r.json()
    for e in body["entradas"]:
        assert e["autor"] in {"angel", "africa"}
        assert e["etiqueta"] in {"trabajo", "nosvers", "familia", "mental", "idea", "otro"}
        assert e["fecha"]
        assert e["ts"]
        assert "path" in e


def test_timeline_sorted_descending(client, angel_token):
    r = client.get("/tablero/api/timeline", headers=_auth(angel_token))
    entries = r.json()["entradas"]
    if len(entries) < 2:
        return  # not enough data to verify ordering — pass
    sorted_view = sorted(entries, key=lambda e: (e["fecha"], e["ts"]), reverse=True)
    assert entries == sorted_view


def test_timeline_filter_autor_angel(client, angel_token):
    r = client.get("/tablero/api/timeline?autor=angel", headers=_auth(angel_token))
    assert r.status_code == 200
    for e in r.json()["entradas"]:
        assert e["autor"] == "angel"


def test_timeline_filter_autor_africa(client, angel_token):
    r = client.get("/tablero/api/timeline?autor=africa", headers=_auth(angel_token))
    assert r.status_code == 200
    for e in r.json()["entradas"]:
        assert e["autor"] == "africa"


def test_timeline_invalid_range_400(client, angel_token):
    r = client.get(
        "/tablero/api/timeline?desde=2026-12-31&hasta=2026-01-01",
        headers=_auth(angel_token),
    )
    assert r.status_code == 400
    assert r.json()["error"] == "parametro_invalido"


def test_timeline_invalid_autor_400(client, angel_token):
    r = client.get("/tablero/api/timeline?autor=hacker", headers=_auth(angel_token))
    assert r.status_code == 400


def test_timeline_invalid_etiqueta_400(client, angel_token):
    r = client.get("/tablero/api/timeline?etiqueta=bogus", headers=_auth(angel_token))
    assert r.status_code == 400


def test_timeline_unauth(client):
    r = client.get("/tablero/api/timeline")
    assert r.status_code == 401
