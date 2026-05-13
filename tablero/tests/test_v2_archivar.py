"""Tests para POST /tablero/api/v2/nota/archivar y /restaurar (US3)."""
from __future__ import annotations

from pathlib import Path

import pytest
from starlette.testclient import TestClient


@pytest.fixture()
def vault_temporal(monkeypatch, tmp_path: Path):
    base = tmp_path / "knowledge_base"
    dia = base / "dia"
    (dia).mkdir(parents=True, exist_ok=True)
    (dia / "audio").mkdir(exist_ok=True)
    (dia / "resumenes").mkdir(exist_ok=True)
    (base / "prompts").mkdir(exist_ok=True)
    (base / "system" / "speakers").mkdir(parents=True, exist_ok=True)
    (base / "prompts" / "clasificar_nota.md").write_text("# stub\n", encoding="utf-8")

    from voz import vault_io, capturar, clasificar
    monkeypatch.setattr(vault_io, "VAULT_BASE", base)
    monkeypatch.setattr(vault_io, "DIA_DIR", dia)
    monkeypatch.setattr(vault_io, "AUDIO_DIR", dia / "audio")
    monkeypatch.setattr(vault_io, "RESUMENES_DIR", dia / "resumenes")
    monkeypatch.setattr(vault_io, "PROMPTS_DIR", base / "prompts")
    if hasattr(capturar, "DIA_DIR"):
        monkeypatch.setattr(capturar, "DIA_DIR", dia)
    if hasattr(capturar, "VAULT_BASE"):
        monkeypatch.setattr(capturar, "VAULT_BASE", base)
    monkeypatch.setattr(clasificar, "PROMPT_FILE", base / "prompts" / "clasificar_nota.md")
    monkeypatch.setenv("CLASIFICADOR_FORCE_FAIL", "1")

    from tablero.v2 import capturar as v2_cap, editar as v2_ed, archivar as v2_arch, proyectos as v2_proy
    monkeypatch.setattr(v2_cap, "VAULT_BASE", base)
    monkeypatch.setattr(v2_ed, "VAULT_BASE", base)
    monkeypatch.setattr(v2_arch, "VAULT_BASE", base)
    monkeypatch.setattr(v2_proy, "VAULT_BASE", base)

    from tablero.v2 import wiki_index as wi
    idx = wi.WikiIndex(base)
    idx.build()
    wi.set_index(idx)

    return base


def _capturar(client: TestClient, token: str, cuerpo: str = "x") -> dict:
    r = client.post(
        "/tablero/api/v2/capturar",
        json={"cuerpo": cuerpo},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 201, r.text
    return r.json()


def test_archivar_200(client: TestClient, vault_temporal, angel_token: str):
    creada = _capturar(client, angel_token, "para archivar")
    r = client.post(
        "/tablero/api/v2/nota/archivar",
        json={"path": creada["path"], "archive_reason": "test"},
        headers={"Authorization": f"Bearer {angel_token}", "If-Match": creada["concurrency_token"]},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["ok"] is True
    assert body["new_path"].startswith("dia/archivo/")
    # archivo destino existe
    assert (vault_temporal / body["new_path"]).exists()
    # entrada eliminada del día
    fecha = creada["fecha"]
    archivo_dia = vault_temporal / "dia" / f"{fecha}.md"
    contenido = archivo_dia.read_text(encoding="utf-8")
    assert creada["ts"] not in contenido


def test_archivar_409_stale(client: TestClient, vault_temporal, angel_token: str):
    creada = _capturar(client, angel_token)
    r = client.post(
        "/tablero/api/v2/nota/archivar",
        json={"path": creada["path"]},
        headers={"Authorization": f"Bearer {angel_token}", "If-Match": "viejo"},
    )
    assert r.status_code == 409


def test_archivar_404_inexistente(client: TestClient, vault_temporal, angel_token: str):
    r = client.post(
        "/tablero/api/v2/nota/archivar",
        json={"path": "dia/2025-01-01.md#ghost"},
        headers={"Authorization": f"Bearer {angel_token}", "If-Match": "x"},
    )
    assert r.status_code == 404


def test_archivar_401_sin_token(client: TestClient, vault_temporal):
    r = client.post("/tablero/api/v2/nota/archivar", json={"path": "x"})
    assert r.status_code == 401


def test_restaurar_200(client: TestClient, vault_temporal, angel_token: str):
    creada = _capturar(client, angel_token, "ciclo completo")
    arc = client.post(
        "/tablero/api/v2/nota/archivar",
        json={"path": creada["path"]},
        headers={"Authorization": f"Bearer {angel_token}", "If-Match": creada["concurrency_token"]},
    )
    assert arc.status_code == 200
    archivado_path = arc.json()["new_path"]

    r = client.post(
        "/tablero/api/v2/nota/restaurar",
        json={"path": archivado_path},
        headers={"Authorization": f"Bearer {angel_token}"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["ts"] == creada["ts"]
    # archivo dia/archivo/ eliminado
    assert not (vault_temporal / archivado_path).exists()
    # entrada reapareció en día
    archivo_dia = vault_temporal / "dia" / f"{creada['fecha']}.md"
    contenido = archivo_dia.read_text(encoding="utf-8")
    assert creada["ts"] in contenido
    assert "ciclo completo" in contenido


def test_restaurar_404(client: TestClient, vault_temporal, angel_token: str):
    r = client.post(
        "/tablero/api/v2/nota/restaurar",
        json={"path": "dia/archivo/ghost.md"},
        headers={"Authorization": f"Bearer {angel_token}"},
    )
    assert r.status_code == 404


def test_archivar_no_aparece_en_timeline(client: TestClient, vault_temporal, angel_token: str):
    """Tras archivar, el timeline no debe devolver la entrada."""
    creada = _capturar(client, angel_token, "para que desaparezca")
    client.post(
        "/tablero/api/v2/nota/archivar",
        json={"path": creada["path"]},
        headers={"Authorization": f"Bearer {angel_token}", "If-Match": creada["concurrency_token"]},
    )
    r = client.get("/tablero/api/timeline", headers={"Authorization": f"Bearer {angel_token}"})
    assert r.status_code == 200
    entradas = r.json()["entradas"]
    paths = [e["path"] for e in entradas]
    assert creada["path"] not in paths
