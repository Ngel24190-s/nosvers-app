"""Tests para PATCH /tablero/api/v2/nota (T023 / US2)."""
from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest
from starlette.testclient import TestClient


@pytest.fixture()
def vault_temporal(monkeypatch, tmp_path: Path):
    """Mismo fixture que en test_v2_capturar, replicado para tener tests independientes."""
    base = tmp_path / "knowledge_base"
    dia = base / "dia"
    audio = dia / "audio"
    resumenes = dia / "resumenes"
    prompts = base / "prompts"
    speakers = base / "system" / "speakers"
    for d in (dia, audio, resumenes, prompts, speakers):
        d.mkdir(parents=True, exist_ok=True)
    (prompts / "clasificar_nota.md").write_text("# stub\n", encoding="utf-8")

    from voz import vault_io, capturar, clasificar
    monkeypatch.setattr(vault_io, "VAULT_BASE", base)
    monkeypatch.setattr(vault_io, "DIA_DIR", dia)
    monkeypatch.setattr(vault_io, "AUDIO_DIR", audio)
    monkeypatch.setattr(vault_io, "RESUMENES_DIR", resumenes)
    monkeypatch.setattr(vault_io, "PROMPTS_DIR", prompts)
    if hasattr(capturar, "DIA_DIR"):
        monkeypatch.setattr(capturar, "DIA_DIR", dia)
    if hasattr(capturar, "VAULT_BASE"):
        monkeypatch.setattr(capturar, "VAULT_BASE", base)
    monkeypatch.setattr(clasificar, "PROMPT_FILE", prompts / "clasificar_nota.md")
    monkeypatch.setenv("CLASIFICADOR_FORCE_FAIL", "1")

    from tablero.v2 import capturar as v2_cap, editar as v2_ed
    monkeypatch.setattr(v2_cap, "VAULT_BASE", base)
    monkeypatch.setattr(v2_ed, "VAULT_BASE", base)

    from tablero.v2 import wiki_index as wi
    idx = wi.WikiIndex(base)
    idx.build()
    wi.set_index(idx)

    return base


def _capturar(client: TestClient, token: str, cuerpo: str = "original") -> dict:
    r = client.post(
        "/tablero/api/v2/capturar",
        json={"cuerpo": cuerpo},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 201, r.text
    return r.json()


def test_editar_401_sin_token(client: TestClient, vault_temporal):
    r = client.patch("/tablero/api/v2/nota", json={"path": "dia/x.md#x", "cuerpo": "y"})
    assert r.status_code == 401


def test_editar_428_sin_if_match(client: TestClient, vault_temporal, angel_token: str):
    creada = _capturar(client, angel_token)
    r = client.patch(
        "/tablero/api/v2/nota",
        json={"path": creada["path"], "cuerpo": "nuevo"},
        headers={"Authorization": f"Bearer {angel_token}"},
    )
    assert r.status_code == 428
    assert r.json()["error"] == "missing_if_match"


def test_editar_200_ok(client: TestClient, vault_temporal, angel_token: str):
    creada = _capturar(client, angel_token, cuerpo="original")
    r = client.patch(
        "/tablero/api/v2/nota",
        json={"path": creada["path"], "cuerpo": "editado"},
        headers={
            "Authorization": f"Bearer {angel_token}",
            "If-Match": creada["concurrency_token"],
        },
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["ok"] is True
    assert body["concurrency_token"] != creada["concurrency_token"]  # modified_at refreshed
    # Verificar archivo en disco
    fecha = body["fecha"]
    archivo = vault_temporal / "dia" / f"{fecha}.md"
    contenido = archivo.read_text(encoding="utf-8")
    assert "editado" in contenido
    assert "original" not in contenido
    assert "modified_at:" in contenido


def test_editar_409_stale_if_match(client: TestClient, vault_temporal, angel_token: str):
    creada = _capturar(client, angel_token)
    r = client.patch(
        "/tablero/api/v2/nota",
        json={"path": creada["path"], "cuerpo": "y"},
        headers={
            "Authorization": f"Bearer {angel_token}",
            "If-Match": "ts-incorrecto",
        },
    )
    assert r.status_code == 409
    body = r.json()
    assert body["error"] == "stale_modified_at"
    assert body["current_modified_at"] == creada["concurrency_token"]


def test_editar_404_path_inexistente(client: TestClient, vault_temporal, angel_token: str):
    r = client.patch(
        "/tablero/api/v2/nota",
        json={"path": "dia/2025-01-01.md#ghost", "cuerpo": "x"},
        headers={"Authorization": f"Bearer {angel_token}", "If-Match": "ghost"},
    )
    assert r.status_code == 404


def test_editar_400_path_invalido(client: TestClient, vault_temporal, angel_token: str):
    r = client.patch(
        "/tablero/api/v2/nota",
        json={"path": "ruta-invalida", "cuerpo": "x"},
        headers={"Authorization": f"Bearer {angel_token}", "If-Match": "x"},
    )
    assert r.status_code == 400
    assert r.json()["error"] == "path_invalido"


def test_editar_paridad_cross_author(client: TestClient, vault_temporal, angel_token: str, africa_token: str):
    """Angel crea, África edita — debe funcionar con paridad de acceso (US2 #5)."""
    creada = _capturar(client, angel_token, cuerpo="texto-angel")
    r = client.patch(
        "/tablero/api/v2/nota",
        json={"path": creada["path"], "cuerpo": "editado-por-africa"},
        headers={
            "Authorization": f"Bearer {africa_token}",
            "If-Match": creada["concurrency_token"],
        },
    )
    assert r.status_code == 200
    fecha = r.json()["fecha"]
    contenido = (vault_temporal / "dia" / f"{fecha}.md").read_text(encoding="utf-8")
    assert "editado-por-africa" in contenido
    assert "last_editor_sub: africa" in contenido  # trazabilidad


def test_editar_segunda_edicion_token_evoluciona(client: TestClient, vault_temporal, angel_token: str):
    """Tras la primera edición, el concurrency_token cambia y la siguiente edit
    requiere el nuevo token."""
    creada = _capturar(client, angel_token, cuerpo="v1")
    r1 = client.patch(
        "/tablero/api/v2/nota",
        json={"path": creada["path"], "cuerpo": "v2"},
        headers={"Authorization": f"Bearer {angel_token}", "If-Match": creada["concurrency_token"]},
    )
    assert r1.status_code == 200
    nuevo_token = r1.json()["concurrency_token"]

    # Intentar con token viejo → 409
    r2 = client.patch(
        "/tablero/api/v2/nota",
        json={"path": creada["path"], "cuerpo": "v3"},
        headers={"Authorization": f"Bearer {angel_token}", "If-Match": creada["concurrency_token"]},
    )
    assert r2.status_code == 409

    # Con token nuevo → 200
    r3 = client.patch(
        "/tablero/api/v2/nota",
        json={"path": creada["path"], "cuerpo": "v3"},
        headers={"Authorization": f"Bearer {angel_token}", "If-Match": nuevo_token},
    )
    assert r3.status_code == 200
