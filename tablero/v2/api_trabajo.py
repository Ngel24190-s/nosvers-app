"""tablero.v2.api_trabajo — endpoints REST v3 del contexto Trabajo (007).

Bajo `/tablero/api/v3/trabajo/`:
- GET /chantiers?estado=activos|archivados|urgentes|todos
- GET /chantier/{slug}
- GET /equipe
- GET /documents?tipo=todos|ppsps|plans-retrait|devis|certificats|diag-amiante

Todos validan `voz.auth.check_context(payload, "trabajo")`. 401 si no hay
JWT, 403 si el JWT no autoriza el contexto trabajo.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

from starlette.requests import Request
from starlette.responses import JSONResponse, Response

sys.path.insert(0, "/home/nosvers")

from voz.auth import validar_token, check_context  # noqa: E402
from claudio_tools.common import parse_frontmatter, vault  # noqa: E402

log = logging.getLogger("tablero.v2.api_trabajo")

# CORS aceptamos los mismos orígenes que el resto del tablero — para la PWA
# claudio se sirve same-origin así que CORS solo importa en dev.
_CORS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, OPTIONS",
    "Access-Control-Allow-Headers": "Authorization, Content-Type, X-Claudio-Context",
    "Access-Control-Max-Age": "86400",
    "Vary": "Origin",
}


def _json(data: dict | list, status: int = 200) -> JSONResponse:
    return JSONResponse(data, status_code=status, headers=_CORS)


async def options_handler(request: Request) -> Response:
    return Response(status_code=204, headers=_CORS)


def _auth_and_check(request: Request) -> tuple[dict | None, JSONResponse | None]:
    """Returns (payload, error_response). Si error, ignora payload."""
    auth = request.headers.get("authorization", "")
    if not auth.lower().startswith("bearer "):
        return None, _json({"ok": False, "error": "auth_invalido"}, 401)
    token = auth[7:].strip()
    payload = validar_token(token)
    if not payload:
        return None, _json({"ok": False, "error": "auth_invalido"}, 401)
    if not check_context(payload, "trabajo"):
        return None, _json({"ok": False, "error": "context_no_autorizado"}, 403)
    return payload, None


def _trabajo_root() -> Path:
    return vault() / "trabajo"


def _read_chantier_meta(idx: Path) -> dict[str, Any]:
    try:
        text = idx.read_text(encoding="utf-8")
    except Exception:
        return {}
    meta, _ = parse_frontmatter(text)
    if not meta:
        return {}
    meta["__slug"] = idx.parent.name
    return meta


# ── /chantiers ─────────────────────────────────────────────────────

async def chantiers_handler(request: Request) -> JSONResponse:
    payload, err = _auth_and_check(request)
    if err is not None:
        return err
    estado = (request.query_params.get("estado") or "activos").strip().lower()
    if estado not in {"activos", "archivados", "urgentes", "todos"}:
        return _json({"ok": False, "error": "estado_invalido"}, 400)

    chantiers_dir = _trabajo_root() / "chantiers"
    if not chantiers_dir.exists():
        return _json({"ok": True, "chantiers": [], "total": 0})
    items: list[dict] = []
    for sub in sorted(chantiers_dir.iterdir()):
        if not sub.is_dir() or sub.name.startswith("_"):
            continue
        idx = sub / "INDEX.md"
        if not idx.exists():
            continue
        meta = _read_chantier_meta(idx)
        if not meta:
            continue
        items.append({
            "slug": meta["__slug"],
            "nombre": meta.get("nombre", meta["__slug"]),
            "cliente": meta.get("cliente", "—"),
            "direccion": meta.get("direccion", ""),
            "devis_eur": meta.get("devis_eur", 0),
            "fecha_inicio": meta.get("fecha_inicio", ""),
            "fecha_fin_prev": meta.get("fecha_fin_prev", ""),
            "estado": meta.get("estado", "activo"),
            "equipe_ids": meta.get("equipe_ids", []) or [],
        })

    if estado != "todos":
        target = {"activos": "activo", "archivados": "archivado",
                  "urgentes": "urgente"}[estado]
        items = [it for it in items if it["estado"] == target]

    return _json({"ok": True, "chantiers": items, "total": len(items)})


# ── /chantier/{slug} ───────────────────────────────────────────────

async def chantier_detail_handler(request: Request) -> JSONResponse:
    payload, err = _auth_and_check(request)
    if err is not None:
        return err
    slug = (request.path_params.get("slug") or "").strip()
    if not slug or slug.startswith("_") or "/" in slug or ".." in slug:
        return _json({"ok": False, "error": "slug_invalido"}, 400)
    cdir = _trabajo_root() / "chantiers" / slug
    if not cdir.exists() or not cdir.is_dir():
        return _json({"ok": False, "error": "no_existe"}, 404)
    idx = cdir / "INDEX.md"
    meta = _read_chantier_meta(idx) if idx.exists() else {}
    journals = []
    jdir = cdir / "journal"
    if jdir.exists():
        for j in sorted(jdir.glob("*.md"), reverse=True)[:10]:
            try:
                journals.append({
                    "fecha": j.stem,
                    "extracto": j.read_text(encoding="utf-8")[:500],
                })
            except Exception:
                pass
    return _json({
        "ok": True,
        "chantier": {
            "slug": slug,
            **{k: v for k, v in meta.items() if not k.startswith("__")},
            "journal_recientes": journals,
        },
    })


# ── /equipe ─────────────────────────────────────────────────────────

async def equipe_handler(request: Request) -> JSONResponse:
    payload, err = _auth_and_check(request)
    if err is not None:
        return err
    path = _trabajo_root() / "equipe" / "operateurs.yaml"
    if not path.exists():
        return _json({"ok": True, "operateurs": [], "total": 0})

    text = path.read_text(encoding="utf-8")
    operateurs: list[dict] = []
    current: dict | None = None
    for line in text.splitlines():
        if line.startswith("operateurs:"):
            continue
        if line.startswith("  - id:"):
            if current:
                operateurs.append(current)
            current = {"id": line.split(":", 1)[1].strip()}
            continue
        if current is not None and line.startswith("    "):
            stripped = line.lstrip()
            if ":" in stripped and not stripped.startswith("-"):
                k, _, v = stripped.partition(":")
                v = v.strip()
                if v:
                    current[k.strip()] = v
    if current:
        operateurs.append(current)
    return _json({"ok": True, "operateurs": operateurs,
                  "total": len(operateurs)})


# ── /documents ──────────────────────────────────────────────────────

_DOC_TIPOS = {"ppsps", "plans-retrait", "devis", "certificats",
              "diag-amiante"}


async def documents_handler(request: Request) -> JSONResponse:
    payload, err = _auth_and_check(request)
    if err is not None:
        return err
    tipo = (request.query_params.get("tipo") or "todos").strip().lower()
    tipos = sorted(_DOC_TIPOS) if tipo == "todos" else [tipo]
    if tipo != "todos" and tipo not in _DOC_TIPOS:
        return _json({"ok": False, "error": "tipo_invalido"}, 400)

    docs: list[dict] = []
    for t in tipos:
        d = _trabajo_root() / "documents" / t
        if not d.exists():
            continue
        for f in sorted(d.glob("*.md"), reverse=True)[:50]:
            try:
                stat = f.stat()
                docs.append({
                    "tipo": t,
                    "nombre": f.name,
                    "size": stat.st_size,
                    "mtime": stat.st_mtime,
                })
            except Exception:
                pass
    return _json({"ok": True, "documents": docs, "total": len(docs)})
