"""Tests storage Automation Engine (004) — usa directorio temporal."""
from __future__ import annotations

import importlib
from datetime import datetime, timezone
from pathlib import Path

import pytest

from tablero.v2.automatizaciones import models


@pytest.fixture()
def tmp_vault(tmp_path, monkeypatch):
    """Apunta storage al tmp_path."""
    from tablero.v2 import automatizaciones as pkg
    from tablero.v2.automatizaciones import storage
    monkeypatch.setattr(pkg, "VAULT_DIR", str(tmp_path))
    monkeypatch.setattr(pkg, "ARCHIVE_DIR", str(tmp_path / "archivadas"))
    monkeypatch.setattr(pkg, "LOGS_DIR", str(tmp_path / "logs"))
    importlib.reload(storage)
    return storage, tmp_path


def _make_create():
    return models.AutomationCreate(
        nombre="X test",
        trigger=models.CronTrigger(tipo="cron", rrule="*/5 * * * *"),
        acciones=[models.DiaCapturarAction(tipo="dia_capturar", texto="hola")],
    )


def test_create_save_load(tmp_vault):
    storage, tmp = tmp_vault
    a = storage.create_from(_make_create(), autor="angel")
    storage.save(a)
    items, errs = storage.load_all()
    assert len(items) == 1
    assert items[0].id == a.id
    assert errs == {}


def test_load_one(tmp_vault):
    storage, tmp = tmp_vault
    a = storage.create_from(_make_create(), autor="angel")
    storage.save(a)
    loaded = storage.load_one(a.id)
    assert loaded is not None
    assert loaded.nombre == "X test"


def test_delete_archives(tmp_vault):
    storage, tmp = tmp_vault
    a = storage.create_from(_make_create(), autor="angel")
    storage.save(a)
    dest = storage.delete(a.id)
    assert dest is not None
    assert dest.parent.name == "archivadas"
    assert storage.load_one(a.id) is None


def test_set_activo(tmp_vault):
    storage, tmp = tmp_vault
    a = storage.create_from(_make_create(), autor="angel")
    a = a.model_copy(update={"activo": True})
    storage.save(a)
    storage.set_activo(a.id, False)
    loaded = storage.load_one(a.id)
    assert loaded.activo is False


def test_corrupto_no_rompe_load_all(tmp_vault):
    storage, tmp = tmp_vault
    a = storage.create_from(_make_create(), autor="angel")
    storage.save(a)
    (tmp / "corrupto.yaml").write_text("nombre: x\ntrigger: {tipo: desconocido}", encoding="utf-8")
    items, errs = storage.load_all()
    assert len(items) == 1
    assert "corrupto.yaml" in errs


def test_ids_unicos(tmp_vault):
    storage, tmp = tmp_vault
    # crear dos con mismo nombre — el segundo debe tener sufijo numérico
    a1 = storage.create_from(_make_create(), autor="angel")
    storage.save(a1)
    a2 = storage.create_from(_make_create(), autor="angel")
    storage.save(a2)
    assert a1.id != a2.id
