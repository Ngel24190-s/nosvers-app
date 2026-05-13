"""Tests para GET /tablero/api/v2/infra/status (US10)."""
from __future__ import annotations

from pathlib import Path

import pytest
from starlette.testclient import TestClient


@pytest.fixture(autouse=True)
def reset_cache():
    from tablero.v2 import infra as v2_infra
    v2_infra._cache["timestamp"] = 0
    v2_infra._cache["data"] = None
    yield


def test_infra_status_401(client: TestClient):
    r = client.get("/tablero/api/v2/infra/status")
    assert r.status_code == 401


def test_infra_status_devuelve_6_badges(client: TestClient, angel_token: str, monkeypatch, tmp_path: Path):
    # Apuntar AGENTS_DIR y CACHE_DIR a temporales
    from tablero.v2 import infra as v2_infra
    agents = tmp_path / "agents"
    cache = tmp_path / "cache"
    agents.mkdir()
    cache.mkdir()
    monkeypatch.setattr(v2_infra, "AGENTS_DIR", agents)
    monkeypatch.setattr(v2_infra, "CACHE_DIR", cache)

    # Bloquear el HEAD HTTP a nosvers.com
    import httpx
    class FakeResp:
        status_code = 200
    monkeypatch.setattr(httpx, "head", lambda *a, **k: FakeResp())

    r = client.get(
        "/tablero/api/v2/infra/status",
        headers={"Authorization": f"Bearer {angel_token}"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["ok"] is True
    badges = body["badges"]
    ids = {b["id"] for b in badges}
    assert ids == {"vps", "wp", "stripe", "aegis", "cron", "freqtrade"}


def test_infra_cron_lee_touchfiles(client: TestClient, angel_token: str, monkeypatch, tmp_path: Path):
    from tablero.v2 import infra as v2_infra
    agents = tmp_path / "agents"
    cache = tmp_path / "cache"
    agents.mkdir()
    cache.mkdir()
    (agents / "agt07_diario.last_run").write_text("", encoding="utf-8")
    monkeypatch.setattr(v2_infra, "AGENTS_DIR", agents)
    monkeypatch.setattr(v2_infra, "CACHE_DIR", cache)

    import httpx
    class FakeResp:
        status_code = 200
    monkeypatch.setattr(httpx, "head", lambda *a, **k: FakeResp())

    r = client.get("/tablero/api/v2/infra/status", headers={"Authorization": f"Bearer {angel_token}"})
    body = r.json()
    cron_badge = next(b for b in body["badges"] if b["id"] == "cron")
    nombres = {c["name"] for c in cron_badge["crones"]}
    assert "agt07_diario" in nombres
    # los otros aparecen como "nunca corrió"
    assert "agt05_africa" in nombres


def test_infra_wp_falla_devuelve_error(client: TestClient, angel_token: str, monkeypatch, tmp_path: Path):
    from tablero.v2 import infra as v2_infra
    monkeypatch.setattr(v2_infra, "AGENTS_DIR", tmp_path)
    monkeypatch.setattr(v2_infra, "CACHE_DIR", tmp_path)

    import httpx
    def boom(*a, **k):
        raise httpx.ConnectError("simulated")
    monkeypatch.setattr(httpx, "head", boom)

    r = client.get("/tablero/api/v2/infra/status", headers={"Authorization": f"Bearer {angel_token}"})
    badges = r.json()["badges"]
    wp = next(b for b in badges if b["id"] == "wp")
    assert wp["status"] == "error"


def test_infra_status_cache(client: TestClient, angel_token: str, monkeypatch, tmp_path: Path):
    """Dos GETs consecutivos en <30s usan caché (verificable inspeccionando _cache)."""
    from tablero.v2 import infra as v2_infra
    monkeypatch.setattr(v2_infra, "AGENTS_DIR", tmp_path)
    monkeypatch.setattr(v2_infra, "CACHE_DIR", tmp_path)

    import httpx
    class FakeResp:
        status_code = 200
    monkeypatch.setattr(httpx, "head", lambda *a, **k: FakeResp())

    r1 = client.get("/tablero/api/v2/infra/status", headers={"Authorization": f"Bearer {angel_token}"})
    ts1 = v2_infra._cache["timestamp"]
    r2 = client.get("/tablero/api/v2/infra/status", headers={"Authorization": f"Bearer {angel_token}"})
    ts2 = v2_infra._cache["timestamp"]
    assert r1.status_code == r2.status_code == 200
    assert ts1 == ts2  # mismo cache hit
