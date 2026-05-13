"""Tests para GET /tablero/api/v2/health (Cockpit Fase D)."""
from __future__ import annotations

from starlette.testclient import TestClient


def test_health_200_devuelve_psutil_snapshot(client: TestClient):
    r = client.get("/tablero/api/v2/health")
    # Producción/test: psutil instalado → 200; si no, 503 — ambos válidos.
    assert r.status_code in (200, 503)
    if r.status_code == 200:
        body = r.json()
        for key in (
            "cpu_pct", "ram_pct", "disk_pct", "uptime_s",
            "load_1", "ram_total_mb", "disk_total_gb",
        ):
            assert key in body, f"falta key {key}"
        assert isinstance(body["uptime_s"], int)
        assert body["uptime_s"] >= 0


def test_health_no_requiere_auth(client: TestClient):
    """El endpoint /v2/health es de bajo coste y NO exige Bearer."""
    r = client.get("/tablero/api/v2/health")
    # Sin header Authorization no devuelve 401.
    assert r.status_code != 401


def test_health_503_si_psutil_falla(client: TestClient, monkeypatch):
    """Si health_snapshot devuelve None, el endpoint devuelve 503."""
    from tablero.v2 import health as v2_health
    monkeypatch.setattr(v2_health, "health_snapshot", lambda: None)
    r = client.get("/tablero/api/v2/health")
    assert r.status_code == 503
    body = r.json()
    assert body.get("error") == "psutil_unavailable"
