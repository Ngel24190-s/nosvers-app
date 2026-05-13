"""Tests para POST /tablero/api/v2/capturar (T018 / US1)."""
from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest
from starlette.testclient import TestClient


# Reusamos el conftest existente para fixtures app/client/angel_token/africa_token
# y añadimos un fixture de vault temporal por test


@pytest.fixture()
def vault_temporal(monkeypatch, tmp_path: Path):
    """Aísla la I/O del vault para los tests de captura."""
    base = tmp_path / "knowledge_base"
    dia = base / "dia"
    audio = dia / "audio"
    resumenes = dia / "resumenes"
    prompts = base / "prompts"
    speakers = base / "system" / "speakers"
    for d in (dia, audio, resumenes, prompts, speakers):
        d.mkdir(parents=True, exist_ok=True)
    # Prompt stub
    (prompts / "clasificar_nota.md").write_text("# Prompt clasificar (stub)\n", encoding="utf-8")

    from voz import vault_io, capturar, clasificar
    monkeypatch.setattr(vault_io, "VAULT_BASE", base)
    monkeypatch.setattr(vault_io, "DIA_DIR", dia)
    monkeypatch.setattr(vault_io, "AUDIO_DIR", audio)
    monkeypatch.setattr(vault_io, "RESUMENES_DIR", resumenes)
    monkeypatch.setattr(vault_io, "PROMPTS_DIR", prompts)
    monkeypatch.setattr(vault_io, "SYSTEM_DIR", base / "system")
    monkeypatch.setattr(vault_io, "SPEAKERS_DIR", speakers)
    if hasattr(capturar, "DIA_DIR"):
        monkeypatch.setattr(capturar, "DIA_DIR", dia)
    if hasattr(capturar, "VAULT_BASE"):
        monkeypatch.setattr(capturar, "VAULT_BASE", base)
    monkeypatch.setattr(clasificar, "PROMPT_FILE", prompts / "clasificar_nota.md")

    # Forzar clasificador fallback (no llama API real)
    monkeypatch.setenv("CLASIFICADOR_FORCE_FAIL", "1")

    # Override VAULT_BASE en módulos v2 (importan al cargar)
    from tablero.v2 import capturar as v2_cap, editar as v2_ed
    monkeypatch.setattr(v2_cap, "VAULT_BASE", base)
    monkeypatch.setattr(v2_ed, "VAULT_BASE", base)

    # Reset wiki_index a vault temporal
    from tablero.v2 import wiki_index as wi
    idx = wi.WikiIndex(base)
    idx.build()
    wi.set_index(idx)

    return base


def test_capturar_401_sin_token(client: TestClient, vault_temporal):
    r = client.post("/tablero/api/v2/capturar", json={"cuerpo": "hola"})
    assert r.status_code == 401


def test_capturar_201_ok_angel(client: TestClient, vault_temporal, angel_token: str):
    r = client.post(
        "/tablero/api/v2/capturar",
        json={"cuerpo": "Idea sobre lombrithé", "etiquetas": ["idea"]},
        headers={"Authorization": f"Bearer {angel_token}"},
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["ok"] is True
    assert body["autor"] == "angel"
    assert body["etiqueta"] == "idea"
    assert body["path"].startswith("dia/") and body["path"].endswith(f".md#{body['ts']}")
    # archivo físico existe
    fecha = body["fecha"]
    archivo = vault_temporal / "dia" / f"{fecha}.md"
    assert archivo.exists()
    contenido = archivo.read_text(encoding="utf-8")
    assert "Idea sobre lombrithé" in contenido
    assert "autor: angel" in contenido


def test_capturar_autor_inferido_africa(client: TestClient, vault_temporal, africa_token: str):
    r = client.post(
        "/tablero/api/v2/capturar",
        json={"cuerpo": "Nota desde móvil de África"},
        headers={"Authorization": f"Bearer {africa_token}"},
    )
    assert r.status_code == 201
    body = r.json()
    assert body["autor"] == "africa"


def test_capturar_cuerpo_vacio_400(client: TestClient, vault_temporal, angel_token: str):
    r = client.post(
        "/tablero/api/v2/capturar",
        json={"cuerpo": "   "},
        headers={"Authorization": f"Bearer {angel_token}"},
    )
    assert r.status_code == 400
    assert r.json()["error"] == "input_vacio"


def test_capturar_etiqueta_invalida_400(client: TestClient, vault_temporal, angel_token: str):
    r = client.post(
        "/tablero/api/v2/capturar",
        json={"cuerpo": "x", "etiquetas": ["categoría-inexistente"]},
        headers={"Authorization": f"Bearer {angel_token}"},
    )
    assert r.status_code == 400
    assert r.json()["error"] == "etiqueta_invalida"


def test_capturar_titulo_se_prepende_como_h2(client: TestClient, vault_temporal, angel_token: str):
    r = client.post(
        "/tablero/api/v2/capturar",
        json={"cuerpo": "cuerpo libre", "titulo": "Idea importante"},
        headers={"Authorization": f"Bearer {angel_token}"},
    )
    assert r.status_code == 201
    fecha = r.json()["fecha"]
    contenido = (vault_temporal / "dia" / f"{fecha}.md").read_text(encoding="utf-8")
    assert "## Idea importante" in contenido


def test_capturar_actualiza_wiki_index(client: TestClient, vault_temporal, angel_token: str):
    r = client.post(
        "/tablero/api/v2/capturar",
        json={"cuerpo": "Esta nota referencia [[lombrithé]] y otra cosa"},
        headers={"Authorization": f"Bearer {angel_token}"},
    )
    assert r.status_code == 201

    from tablero.v2.wiki_index import get_index
    idx = get_index()
    backlinks = idx.backlinks_de("lombrithé")
    assert len(backlinks) == 1


def test_capturar_body_demasiado_grande_400(client: TestClient, vault_temporal, angel_token: str):
    big = "x" * (1024 * 1024 + 1)
    r = client.post(
        "/tablero/api/v2/capturar",
        json={"cuerpo": big},
        headers={"Authorization": f"Bearer {angel_token}"},
    )
    assert r.status_code == 400
    assert r.json()["error"] == "body_too_large"
