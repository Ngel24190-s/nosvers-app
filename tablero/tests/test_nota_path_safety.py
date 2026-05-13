"""T040 — note detail endpoint smoke tests (path-safety + happy path)."""
from __future__ import annotations

from urllib.parse import quote


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_nota_traversal_returns_400_path_unsafe(client, angel_token):
    # An attempt to escape the vault should be rejected at the parse layer first
    # (path doesn't match `dia/YYYY-MM-DD.md#<ts>`), which is mapped to
    # parametro_invalido. Either parametro_invalido or path_unsafe is acceptable
    # behavior — the requirement is that it's a 400 and does NOT leak data.
    r = client.get(
        f"/tablero/api/nota?path={quote('../../etc/passwd')}",
        headers=_auth(angel_token),
    )
    assert r.status_code == 400
    assert r.json()["error"] in {"path_unsafe", "parametro_invalido"}


def test_nota_missing_path_param(client, angel_token):
    r = client.get("/tablero/api/nota", headers=_auth(angel_token))
    assert r.status_code == 400
    assert r.json()["error"] == "parametro_invalido"


def test_nota_malformed_path(client, angel_token):
    r = client.get(
        f"/tablero/api/nota?path={quote('not-a-real-path')}",
        headers=_auth(angel_token),
    )
    assert r.status_code == 400
    assert r.json()["error"] == "parametro_invalido"


def test_nota_unknown_date(client, angel_token):
    r = client.get(
        f"/tablero/api/nota?path={quote('dia/2099-01-01.md#nonexistent')}",
        headers=_auth(angel_token),
    )
    assert r.status_code == 404
    assert r.json()["error"] == "not_found"


def test_nota_unauth(client):
    r = client.get("/tablero/api/nota?path=dia/2026-05-13.md#whatever")
    assert r.status_code == 401


def test_nota_happy_path_if_data_exists(client, angel_token):
    # Use the timeline endpoint to discover a real path; skip if vault empty.
    r = client.get("/tablero/api/timeline", headers=_auth(angel_token))
    entries = r.json()["entradas"]
    if not entries:
        return
    first = entries[0]
    r2 = client.get(
        f"/tablero/api/nota?path={quote(first['path'])}",
        headers=_auth(angel_token),
    )
    assert r2.status_code == 200, r2.text
    body = r2.json()
    assert body["ok"] is True
    assert body["nota"]["path"] == first["path"]
    assert isinstance(body["nota"]["body_markdown"], str)
    assert "frontmatter" in body["nota"]
