"""Tests para POST /tablero/api/v2/agentes/ejecutar y GET /catalogo (US11)."""
from __future__ import annotations

from pathlib import Path

import pytest
from starlette.testclient import TestClient


def test_catalogo_401(client: TestClient):
    r = client.get("/tablero/api/v2/agentes/catalogo")
    assert r.status_code == 401


def test_catalogo_lista_agentes(client: TestClient, angel_token: str):
    r = client.get("/tablero/api/v2/agentes/catalogo", headers={"Authorization": f"Bearer {angel_token}"})
    assert r.status_code == 200
    agentes = r.json()["agentes"]
    slugs = {a["slug"] for a in agentes}
    assert {"agt05_africa", "agt07_diario", "agt_eisenia", "orchestrator"} <= slugs


def test_ejecutar_slug_no_en_catalogo_404(client: TestClient, angel_token: str):
    r = client.post(
        "/tablero/api/v2/agentes/ejecutar",
        json={"slug": "fantasma"},
        headers={"Authorization": f"Bearer {angel_token}"},
    )
    assert r.status_code == 404
    assert r.json()["error"] == "not_in_catalog"


def test_ejecutar_script_missing(client: TestClient, angel_token: str, monkeypatch, tmp_path: Path):
    from tablero.v2 import agentes as v2_ag
    monkeypatch.setattr(v2_ag, "AGENTS_ROOT", tmp_path)  # carpeta vacía
    r = client.post(
        "/tablero/api/v2/agentes/ejecutar",
        json={"slug": "agt07_diario"},
        headers={"Authorization": f"Bearer {angel_token}"},
    )
    assert r.status_code == 500
    assert r.json()["error"] == "script_missing"


def test_ejecutar_ok_subprocess_falso(client: TestClient, angel_token: str, monkeypatch, tmp_path: Path):
    """Crea un script falso que escribe en stdout y termina rápido."""
    from tablero.v2 import agentes as v2_ag
    monkeypatch.setattr(v2_ag, "AGENTS_ROOT", tmp_path)
    fake = tmp_path / "agt07_diario.py"
    fake.write_text("import sys\nprint('hola del agente falso')\nsys.exit(0)\n", encoding="utf-8")

    r = client.post(
        "/tablero/api/v2/agentes/ejecutar",
        json={"slug": "agt07_diario", "timeout_s": 10},
        headers={"Authorization": f"Bearer {angel_token}"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["ok"] is True
    assert body["slug"] == "agt07_diario"
    assert "hola del agente falso" in body["output"]
    assert body["triggered_by"] == "angel"


def test_ejecutar_timeout_504(client: TestClient, angel_token: str, monkeypatch, tmp_path: Path):
    from tablero.v2 import agentes as v2_ag
    monkeypatch.setattr(v2_ag, "AGENTS_ROOT", tmp_path)
    fake = tmp_path / "agt07_diario.py"
    fake.write_text("import time\ntime.sleep(5)\n", encoding="utf-8")

    r = client.post(
        "/tablero/api/v2/agentes/ejecutar",
        json={"slug": "agt07_diario", "timeout_s": 1},
        headers={"Authorization": f"Bearer {angel_token}"},
    )
    assert r.status_code == 504
    assert r.json()["error"] == "agente_stall"
    assert "MCP_STALL_AGENTE" in r.json()["output"]


def test_ejecutar_401(client: TestClient):
    r = client.post("/tablero/api/v2/agentes/ejecutar", json={"slug": "agt07_diario"})
    assert r.status_code == 401
