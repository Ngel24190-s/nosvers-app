"""tablero.v2.automatizaciones.storage — Persistencia YAML.

YAML soberano en knowledge_base/automatizaciones/*.yaml. Atomic write para
zero-corruption. Read-only listado tolera ficheros corruptos (los enumera).
"""
from __future__ import annotations

import logging
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from tablero.v2.atomic_write import escribir_atomico
from tablero.v2.automatizaciones import ARCHIVE_DIR, VAULT_DIR
from tablero.v2.automatizaciones.models import (
    ID_PATTERN,
    Automation,
    AutomationCreate,
)

log = logging.getLogger("tablero.v2.automatizaciones.storage")

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def slugify(nombre: str) -> str:
    s = _SLUG_RE.sub("_", nombre.lower()).strip("_")
    return s[:80] or "sin_nombre"


def generar_id(nombre: str, prefix: str = "auto") -> str:
    today = datetime.now(timezone.utc).strftime("%Y_%m_%d")
    return f"{prefix}_{today}_{slugify(nombre)}"


def _path_para(id_: str) -> Path:
    if not re.match(ID_PATTERN, id_):
        raise ValueError(f"id inválido: {id_}")
    return Path(VAULT_DIR) / f"{id_}.yaml"


def load_all() -> tuple[list[Automation], dict[str, str]]:
    """Carga todos los YAML del directorio.

    Returns: (automations, errores) donde errores es {filename: motivo}.
    """
    base = Path(VAULT_DIR)
    base.mkdir(parents=True, exist_ok=True)
    items: list[Automation] = []
    errores: dict[str, str] = {}
    seen_ids: set[str] = set()
    for p in sorted(base.glob("*.yaml")):
        try:
            data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
            a = Automation.model_validate(data)
            if a.id in seen_ids:
                errores[p.name] = f"id duplicado: {a.id}"
                continue
            seen_ids.add(a.id)
            items.append(a)
        except Exception as e:
            errores[p.name] = str(e)[:200]
            log.warning(f"YAML inválido {p.name}: {e}")
    return items, errores


def load_one(id_: str) -> Automation | None:
    p = _path_para(id_)
    if not p.exists():
        return None
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    return Automation.model_validate(data)


def save(automation: Automation) -> None:
    """Persiste atomicamente."""
    p = _path_para(automation.id)
    data = automation.model_dump(mode="json")
    yaml_text = yaml.safe_dump(data, sort_keys=False, allow_unicode=True, indent=2)
    escribir_atomico(p, yaml_text)


def create_from(body: AutomationCreate, autor: str) -> Automation:
    """Crea una Automation con id generado + timestamps + autor."""
    now = datetime.now(timezone.utc)
    id_ = generar_id(body.nombre, prefix="auto")
    # Si ya existe, añade sufijo numérico
    base_id = id_
    suffix = 1
    while _path_para(id_).exists():
        suffix += 1
        id_ = f"{base_id}_{suffix}"
    return Automation(
        id=id_,
        nombre=body.nombre,
        autor=autor,  # type: ignore[arg-type]
        creado=now,
        modificado=now,
        activo=body.activo,
        trigger=body.trigger,
        acciones=body.acciones,
        metadatos=body.metadatos,
    )


def update(id_: str, body: AutomationCreate) -> Automation | None:
    existing = load_one(id_)
    if existing is None:
        return None
    updated = Automation(
        id=existing.id,
        nombre=body.nombre,
        autor=existing.autor,
        creado=existing.creado,
        modificado=datetime.now(timezone.utc),
        activo=body.activo,
        trigger=body.trigger,
        acciones=body.acciones,
        metadatos=body.metadatos,
    )
    save(updated)
    return updated


def delete(id_: str) -> Path | None:
    """Mueve YAML a archivadas/."""
    p = _path_para(id_)
    if not p.exists():
        return None
    Path(ARCHIVE_DIR).mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dest = Path(ARCHIVE_DIR) / f"{p.stem}_deleted_{ts}.yaml"
    shutil.move(str(p), str(dest))
    return dest


def set_activo(id_: str, activo: bool) -> Automation | None:
    a = load_one(id_)
    if a is None:
        return None
    a = a.model_copy(update={
        "activo": activo,
        "modificado": datetime.now(timezone.utc),
    })
    save(a)
    return a


def summary(a: Automation, last_run: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "id": a.id,
        "nombre": a.nombre,
        "autor": a.autor,
        "activo": a.activo,
        "trigger_tipo": a.trigger.tipo,
        "modificado": a.modificado.isoformat(),
        "last_run": last_run,
    }
