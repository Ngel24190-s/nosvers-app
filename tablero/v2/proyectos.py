"""tablero.v2.proyectos — GET+PATCH /tablero/api/v2/proyectos (US6).

Lee knowledge_base/proyectos/*.md como tarjetas kanban con frontmatter
{estado, modified_at, titulo, responsable?, deadline?, etiquetas?}.

Si la carpeta no existe, la crea al primer GET con un archivo bienvenida.md
explicativo (FR-014).

Concurrencia optimista via If-Match (D-003).
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, "/home/nosvers")

from starlette.requests import Request
from starlette.responses import JSONResponse

from voz.vault_io import VAULT_BASE  # noqa: E402

from tablero.log import get_logger  # noqa: E402
from tablero.v2.atomic_write import escribir_atomico  # noqa: E402
from tablero.v2.frontmatter import (  # noqa: E402
    actualizar_modified_at,
    now_modified_at,
    parse as parse_fm,
    serialize as serialize_fm,
)
from tablero.v2.slug_resolver import slug_de_archivo  # noqa: E402
from tablero.v2.wiki_index import get_index  # noqa: E402

log = get_logger("tablero.v2.proyectos")

ESTADOS_VALIDOS = {"todo", "doing", "done", "blocked"}
ESTADO_FALLBACK = "sin_estado"

_BIENVENIDA = """---
titulo: "Bienvenida a Proyectos NosVers"
estado: todo
modified_at: '{now}'
responsable: angel
etiquetas: [meta, onboarding]
---

# Cómo usar este kanban

Cada archivo `.md` en `knowledge_base/proyectos/` es una tarjeta del kanban.
El campo `estado` del frontmatter determina la columna donde aparece:

- `todo`     → por hacer
- `doing`    → en curso
- `done`     → hecho
- `blocked`  → bloqueado

Si pones un valor distinto (o lo dejas vacío), la tarjeta cae en la columna
"sin estado" como advertencia.

Arrastra una tarjeta entre columnas para cambiar el estado — el frontmatter
se reescribe automáticamente. Soporte para `responsable`, `deadline` y
`etiquetas` es opcional.

Borra este archivo cuando quieras: no es obligatorio.
"""


def _proyectos_dir() -> Path:
    return VAULT_BASE / "proyectos"


def _asegurar_estructura() -> None:
    """Si la carpeta no existe o está vacía, créala con bienvenida.md (FR-014)."""
    d = _proyectos_dir()
    if not d.exists():
        d.mkdir(parents=True, exist_ok=True)
    if not list(d.glob("*.md")):
        contenido = _BIENVENIDA.format(now=now_modified_at())
        escribir_atomico(d / "bienvenida.md", contenido)


def _leer_proyecto(archivo: Path) -> dict[str, Any]:
    text = archivo.read_text(encoding="utf-8")
    meta, body = parse_fm(text)
    estado = str(meta.get("estado", "")).strip().lower()
    if estado not in ESTADOS_VALIDOS:
        estado = ESTADO_FALLBACK
    return {
        "slug": slug_de_archivo(archivo),
        "titulo": str(meta.get("titulo", archivo.stem)),
        "estado": estado,
        "modified_at": str(meta.get("modified_at", "")) or None,
        "responsable": str(meta.get("responsable", "")) or None,
        "deadline": str(meta.get("deadline", "")) or None,
        "etiquetas": meta.get("etiquetas") if isinstance(meta.get("etiquetas"), list) else [],
        "cuerpo": body.strip(),
    }


async def listar_handler(request: Request, autenticador, cors_headers, log_line) -> JSONResponse:
    t0 = time.perf_counter()
    rid = request.headers.get("x-request-id") or "anon"
    payload = await autenticador(request)
    if not payload:
        log_line(rid, "", "v2/proyectos", 401, (time.perf_counter() - t0) * 1000)
        return JSONResponse({"ok": False, "error": "auth_invalido"}, status_code=401, headers=cors_headers())

    sub = str(payload.get("sub", ""))

    try:
        _asegurar_estructura()
    except Exception as e:  # noqa: BLE001
        log.exception(f"rid={rid} _asegurar_estructura: {e}")
        return JSONResponse({"ok": False, "error": "vault_init_failed"}, status_code=500, headers=cors_headers())

    proyectos: list[dict[str, Any]] = []
    for archivo in sorted(_proyectos_dir().glob("*.md")):
        try:
            proyectos.append(_leer_proyecto(archivo))
        except Exception:
            log.exception("Error leyendo proyecto %s", archivo)

    log_line(rid, sub, "v2/proyectos", 200, (time.perf_counter() - t0) * 1000, f"n={len(proyectos)}")
    return JSONResponse({"ok": True, "proyectos": proyectos}, headers=cors_headers())


async def actualizar_handler(request: Request, autenticador, cors_headers, log_line) -> JSONResponse:
    t0 = time.perf_counter()
    rid = request.headers.get("x-request-id") or "anon"
    payload = await autenticador(request)
    if not payload:
        log_line(rid, "", "v2/proyectos/patch", 401, (time.perf_counter() - t0) * 1000)
        return JSONResponse({"ok": False, "error": "auth_invalido"}, status_code=401, headers=cors_headers())

    sub = str(payload.get("sub", ""))

    if_match = request.headers.get("If-Match", "").strip()
    if not if_match:
        return JSONResponse({"ok": False, "error": "missing_if_match"}, status_code=428, headers=cors_headers())

    try:
        body = json.loads(await request.body() or b"{}")
    except json.JSONDecodeError:
        return JSONResponse({"ok": False, "error": "json_invalido"}, status_code=400, headers=cors_headers())

    slug = (body.get("slug") or "").strip()
    if not slug or not re.match(r"^[A-Za-z0-9_\-]+$", slug):
        return JSONResponse({"ok": False, "error": "slug_invalido"}, status_code=400, headers=cors_headers())

    archivo = _proyectos_dir() / f"{slug}.md"
    if not archivo.exists():
        return JSONResponse({"ok": False, "error": "not_found"}, status_code=404, headers=cors_headers())

    # Concurrencia optimista
    text = archivo.read_text(encoding="utf-8")
    meta, body_md = parse_fm(text)
    actual_token = str(meta.get("modified_at") or "")
    if actual_token and actual_token != if_match:
        return JSONResponse({
            "ok": False,
            "error": "stale_modified_at",
            "current_modified_at": actual_token,
        }, status_code=409, headers=cors_headers())

    # Aplicar cambios
    cambio = False
    if "estado" in body:
        nuevo = str(body["estado"]).strip().lower()
        if nuevo not in ESTADOS_VALIDOS:
            return JSONResponse({"ok": False, "error": "estado_invalido"}, status_code=400, headers=cors_headers())
        meta["estado"] = nuevo
        cambio = True
    if "titulo" in body:
        meta["titulo"] = str(body["titulo"]).strip()
        cambio = True
    if "responsable" in body:
        r = str(body["responsable"]).strip().lower()
        if r not in {"angel", "africa", ""}:
            return JSONResponse({"ok": False, "error": "responsable_invalido"}, status_code=400, headers=cors_headers())
        if r:
            meta["responsable"] = r
        else:
            meta.pop("responsable", None)
        cambio = True
    if "deadline" in body:
        d = str(body["deadline"]).strip()
        if d and not re.match(r"^\d{4}-\d{2}-\d{2}$", d):
            return JSONResponse({"ok": False, "error": "deadline_invalido"}, status_code=400, headers=cors_headers())
        if d:
            meta["deadline"] = d
        else:
            meta.pop("deadline", None)
        cambio = True
    if "etiquetas" in body:
        if not isinstance(body["etiquetas"], list):
            return JSONResponse({"ok": False, "error": "etiquetas_invalido"}, status_code=400, headers=cors_headers())
        meta["etiquetas"] = [str(t) for t in body["etiquetas"] if isinstance(t, str)]
        cambio = True
    if "cuerpo" in body:
        body_md = str(body["cuerpo"])
        cambio = True

    if not cambio:
        return JSONResponse({"ok": False, "error": "sin_cambios"}, status_code=400, headers=cors_headers())

    meta = actualizar_modified_at(meta)
    meta["last_editor_sub"] = sub

    try:
        nuevo_texto = serialize_fm(meta, body_md if body_md.endswith("\n") else body_md + "\n")
        escribir_atomico(archivo, nuevo_texto)
    except Exception as e:  # noqa: BLE001
        log.exception(f"rid={rid} v2/proyectos/patch escribir: {e}")
        return JSONResponse({"ok": False, "error": "vault_write_failed"}, status_code=500, headers=cors_headers())

    # Wiki-index
    try:
        get_index().actualizar_nota(archivo, archivo.read_text(encoding="utf-8"))
    except Exception:
        pass

    resultado = _leer_proyecto(archivo)
    log_line(rid, sub, "v2/proyectos/patch", 200, (time.perf_counter() - t0) * 1000, f"slug={slug}")
    return JSONResponse({"ok": True, **resultado}, headers=cors_headers())
