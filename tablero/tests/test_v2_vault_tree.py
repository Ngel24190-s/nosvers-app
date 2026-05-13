"""Tests para GET /tablero/api/v2/vault/tree (US8)."""
from __future__ import annotations

from pathlib import Path

import pytest
from starlette.testclient import TestClient


@pytest.fixture()
def vault_temporal(monkeypatch, tmp_path: Path):
    base = tmp_path / "knowledge_base"
    (base / "dia").mkdir(parents=True)
    (base / "dia" / "2026-05-13.md").write_text("# Diario\n", encoding="utf-8")
    (base / "proyectos").mkdir()
    (base / "proyectos" / "tienda.md").write_text("---\nestado: todo\n---\n", encoding="utf-8")
    (base / "contexto").mkdir()
    (base / ".hidden_dir").mkdir()
    (base / ".hidden_file.md").write_text("hidden", encoding="utf-8")

    from voz import vault_io
    monkeypatch.setattr(vault_io, "VAULT_BASE", base)
    from tablero.v2 import vault_tree as v2_tree
    monkeypatch.setattr(v2_tree, "VAULT_BASE", base)

    return base


def test_tree_root(client: TestClient, vault_temporal, angel_token: str):
    r = client.get("/tablero/api/v2/vault/tree", headers={"Authorization": f"Bearer {angel_token}"})
    assert r.status_code == 200
    body = r.json()
    nombres = {c["name"] for c in body["children"]}
    assert "dia" in nombres
    assert "proyectos" in nombres
    assert "contexto" in nombres
    # hidden excluidos
    assert ".hidden_dir" not in nombres
    assert ".hidden_file.md" not in nombres


def test_tree_subcarpeta(client: TestClient, vault_temporal, angel_token: str):
    r = client.get("/tablero/api/v2/vault/tree?path=dia", headers={"Authorization": f"Bearer {angel_token}"})
    assert r.status_code == 200
    body = r.json()
    assert any(c["name"] == "2026-05-13.md" and c["type"] == "file" for c in body["children"])


def test_tree_traversal_rechazado(client: TestClient, vault_temporal, angel_token: str):
    r = client.get("/tablero/api/v2/vault/tree?path=../../../etc", headers={"Authorization": f"Bearer {angel_token}"})
    assert r.status_code == 400
    assert r.json()["error"] == "path_unsafe"


def test_tree_404(client: TestClient, vault_temporal, angel_token: str):
    r = client.get("/tablero/api/v2/vault/tree?path=ghost", headers={"Authorization": f"Bearer {angel_token}"})
    assert r.status_code == 404


def test_tree_401(client: TestClient, vault_temporal):
    r = client.get("/tablero/api/v2/vault/tree")
    assert r.status_code == 401


def test_tree_files_tienen_size(client: TestClient, vault_temporal, angel_token: str):
    r = client.get("/tablero/api/v2/vault/tree?path=dia", headers={"Authorization": f"Bearer {angel_token}"})
    files = [c for c in r.json()["children"] if c["type"] == "file"]
    assert all("size" in f for f in files)
