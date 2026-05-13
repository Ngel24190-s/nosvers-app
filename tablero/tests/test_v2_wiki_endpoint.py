"""Tests para GET /tablero/api/v2/wiki-index (US7)."""
from __future__ import annotations

from pathlib import Path

import pytest
from starlette.testclient import TestClient


@pytest.fixture()
def vault_temporal(monkeypatch, tmp_path: Path):
    base = tmp_path / "knowledge_base"
    (base / "dia").mkdir(parents=True)
    (base / "dia" / "2026-05-13.md").write_text(
        "# Diario — 2026-05-13\n\n---\nts: '2026-05-13T10:00:00+00:00'\nautor: angel\netiqueta: idea\n---\n\nIdea sobre [[lombrithé]] y [[composteur]].\n",
        encoding="utf-8",
    )

    from voz import vault_io
    monkeypatch.setattr(vault_io, "VAULT_BASE", base)
    from tablero.v2 import wiki_index as wi
    idx = wi.WikiIndex(base)
    idx.build()
    wi.set_index(idx)

    return base


def test_wiki_index_full(client: TestClient, vault_temporal, angel_token: str):
    r = client.get("/tablero/api/v2/wiki-index", headers={"Authorization": f"Bearer {angel_token}"})
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert "lombrithe" in body["index"]
    assert "composteur" in body["index"]
    assert body["generated_at"] is not None


def test_wiki_index_filtrado_por_target(client: TestClient, vault_temporal, angel_token: str):
    r = client.get(
        "/tablero/api/v2/wiki-index?target=lombrithé",
        headers={"Authorization": f"Bearer {angel_token}"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["target"] == "lombrithé"
    assert len(body["backlinks"]) == 1


def test_wiki_index_target_inexistente_devuelve_lista_vacia(client: TestClient, vault_temporal, angel_token: str):
    r = client.get(
        "/tablero/api/v2/wiki-index?target=ghost",
        headers={"Authorization": f"Bearer {angel_token}"},
    )
    assert r.status_code == 200
    assert r.json()["backlinks"] == []


def test_wiki_index_401(client: TestClient, vault_temporal):
    r = client.get("/tablero/api/v2/wiki-index")
    assert r.status_code == 401
