"""Tests para GET+PATCH /tablero/api/v2/proyectos (US6 kanban)."""
from __future__ import annotations

from pathlib import Path

import pytest
from starlette.testclient import TestClient


@pytest.fixture()
def vault_temporal(monkeypatch, tmp_path: Path):
    base = tmp_path / "knowledge_base"
    base.mkdir(parents=True, exist_ok=True)

    from voz import vault_io
    monkeypatch.setattr(vault_io, "VAULT_BASE", base)

    from tablero.v2 import proyectos as v2_proy
    monkeypatch.setattr(v2_proy, "VAULT_BASE", base)

    from tablero.v2 import wiki_index as wi
    idx = wi.WikiIndex(base)
    idx.build()
    wi.set_index(idx)

    return base


def test_get_proyectos_crea_bienvenida_si_vacio(client: TestClient, vault_temporal, angel_token: str):
    r = client.get("/tablero/api/v2/proyectos", headers={"Authorization": f"Bearer {angel_token}"})
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    proyectos = body["proyectos"]
    assert len(proyectos) >= 1
    assert any(p["slug"] == "bienvenida" for p in proyectos)
    # carpeta y archivo físicos creados
    assert (vault_temporal / "proyectos" / "bienvenida.md").exists()


def test_get_proyectos_lista_existentes(client: TestClient, vault_temporal, angel_token: str):
    (vault_temporal / "proyectos").mkdir(exist_ok=True)
    (vault_temporal / "proyectos" / "tienda.md").write_text(
        "---\ntitulo: Tienda Lemon\nestado: doing\nmodified_at: '2026-05-13T10:00:00+00:00'\n---\ncuerpo\n",
        encoding="utf-8",
    )
    r = client.get("/tablero/api/v2/proyectos", headers={"Authorization": f"Bearer {angel_token}"})
    assert r.status_code == 200
    proyectos = r.json()["proyectos"]
    tienda = next((p for p in proyectos if p["slug"] == "tienda"), None)
    assert tienda is not None
    assert tienda["estado"] == "doing"
    assert tienda["titulo"] == "Tienda Lemon"


def test_get_proyectos_estado_invalido_cae_en_sin_estado(client: TestClient, vault_temporal, angel_token: str):
    (vault_temporal / "proyectos").mkdir(exist_ok=True)
    (vault_temporal / "proyectos" / "x.md").write_text(
        "---\ntitulo: X\nestado: xyz\nmodified_at: '2026-05-13T10:00:00+00:00'\n---\n",
        encoding="utf-8",
    )
    r = client.get("/tablero/api/v2/proyectos", headers={"Authorization": f"Bearer {angel_token}"})
    p = next(p for p in r.json()["proyectos"] if p["slug"] == "x")
    assert p["estado"] == "sin_estado"


def test_patch_estado_actualiza_frontmatter(client: TestClient, vault_temporal, angel_token: str):
    (vault_temporal / "proyectos").mkdir(exist_ok=True)
    archivo = vault_temporal / "proyectos" / "y.md"
    archivo.write_text(
        "---\ntitulo: Y\nestado: todo\nmodified_at: '2026-05-13T10:00:00+00:00'\netiquetas: [demo]\n---\ncuerpo libre\n",
        encoding="utf-8",
    )
    r = client.patch(
        "/tablero/api/v2/proyectos",
        json={"slug": "y", "estado": "doing"},
        headers={"Authorization": f"Bearer {angel_token}", "If-Match": "2026-05-13T10:00:00+00:00"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["estado"] == "doing"
    contenido = archivo.read_text(encoding="utf-8")
    assert "estado: doing" in contenido
    assert "etiquetas:" in contenido  # preservado


def test_patch_409_stale(client: TestClient, vault_temporal, angel_token: str):
    (vault_temporal / "proyectos").mkdir(exist_ok=True)
    (vault_temporal / "proyectos" / "z.md").write_text(
        "---\ntitulo: Z\nestado: todo\nmodified_at: '2026-05-13T10:00:00+00:00'\n---\n",
        encoding="utf-8",
    )
    r = client.patch(
        "/tablero/api/v2/proyectos",
        json={"slug": "z", "estado": "doing"},
        headers={"Authorization": f"Bearer {angel_token}", "If-Match": "viejo"},
    )
    assert r.status_code == 409


def test_patch_404(client: TestClient, vault_temporal, angel_token: str):
    r = client.patch(
        "/tablero/api/v2/proyectos",
        json={"slug": "fantasma", "estado": "doing"},
        headers={"Authorization": f"Bearer {angel_token}", "If-Match": "x"},
    )
    assert r.status_code == 404


def test_patch_estado_invalido_400(client: TestClient, vault_temporal, angel_token: str):
    (vault_temporal / "proyectos").mkdir(exist_ok=True)
    (vault_temporal / "proyectos" / "a.md").write_text(
        "---\ntitulo: A\nestado: todo\nmodified_at: '2026-05-13T10:00:00+00:00'\n---\n",
        encoding="utf-8",
    )
    r = client.patch(
        "/tablero/api/v2/proyectos",
        json={"slug": "a", "estado": "no-existe"},
        headers={"Authorization": f"Bearer {angel_token}", "If-Match": "2026-05-13T10:00:00+00:00"},
    )
    assert r.status_code == 400


def test_get_401_sin_token(client: TestClient, vault_temporal):
    r = client.get("/tablero/api/v2/proyectos")
    assert r.status_code == 401
