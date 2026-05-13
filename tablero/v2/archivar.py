"""tablero.v2.archivar — POST /tablero/api/v2/nota/archivar (US3, soft delete).

Mueve una entrada (fecha, ts) desde dia/<fecha>.md a
dia/archivo/<fecha>-<ts-slug>.md como archivo independiente. Añade
archived_at + archive_reason al frontmatter.

Restaurar es el inverso: mover de dia/archivo/* de vuelta como entrada al
día correspondiente.
"""
from __future__ import annotations

import json
import re
import sys
import time
from datetime import date, datetime

sys.path.insert(0, "/home/nosvers")

from starlette.requests import Request
from starlette.responses import JSONResponse

from voz.vault_io import VAULT_BASE  # noqa: E402

from tablero.log import get_logger  # noqa: E402
from tablero.v2.atomic_write import escribir_atomico, mover_atomico  # noqa: E402
from tablero.v2.dia_io import (  # noqa: E402
    Entrada,
    buscar_entrada,
    escribir_dia,
    leer_dia,
    parsear_dia,
    serializar_dia,
)
from tablero.v2.frontmatter import now_modified_at, serialize as serialize_fm  # noqa: E402
from tablero.v2.wiki_index import get_index  # noqa: E402


log = get_logger("tablero.v2.archivar")


def _parse_path(path: str) -> tuple[date, str] | None:
    if "#" not in path:
        return None
    archivo, ts = path.split("#", 1)
    archivo, ts = archivo.strip(), ts.strip()
    if not archivo.startswith("dia/") or not archivo.endswith(".md"):
        return None
    fecha_str = archivo[len("dia/"):-len(".md")]
    try:
        return date.fromisoformat(fecha_str), ts
    except ValueError:
        return None


def _slug_ts(ts: str) -> str:
    """Convierte un ts ISO en un slug filename-safe."""
    return re.sub(r"[^0-9A-Za-z]", "-", ts).strip("-")


async def archivar_handler(request: Request, autenticador, cors_headers, log_line) -> JSONResponse:
    t0 = time.perf_counter()
    rid = request.headers.get("x-request-id") or "anon"
    payload = await autenticador(request)
    if not payload:
        log_line(rid, "", "v2/archivar", 401, (time.perf_counter() - t0) * 1000)
        return JSONResponse({"ok": False, "error": "auth_invalido"}, status_code=401, headers=cors_headers())

    sub = str(payload.get("sub", ""))

    if_match = request.headers.get("If-Match", "").strip()
    if not if_match:
        return JSONResponse({"ok": False, "error": "missing_if_match"}, status_code=428, headers=cors_headers())

    try:
        body = json.loads(await request.body() or b"{}")
    except json.JSONDecodeError:
        return JSONResponse({"ok": False, "error": "json_invalido"}, status_code=400, headers=cors_headers())

    path = (body.get("path") or "").strip()
    reason = (body.get("archive_reason") or "").strip()[:500] or None

    parsed = _parse_path(path)
    if parsed is None:
        return JSONResponse({"ok": False, "error": "path_invalido"}, status_code=400, headers=cors_headers())
    fecha, ts = parsed

    entradas = leer_dia(VAULT_BASE, fecha)
    target = buscar_entrada(entradas, ts) if entradas else None
    if target is None:
        return JSONResponse({"ok": False, "error": "not_found"}, status_code=404, headers=cors_headers())

    if if_match != target.concurrency_token:
        return JSONResponse({
            "ok": False,
            "error": "stale_modified_at",
            "current_modified_at": target.concurrency_token,
        }, status_code=409, headers=cors_headers())

    # Marcar la entrada como archivada
    target.meta["archived_at"] = now_modified_at()
    if reason:
        target.meta["archive_reason"] = reason
    target.meta["archived_by"] = sub

    # Escribir la entrada como archivo independiente en dia/archivo/
    archivo_dir = VAULT_BASE / "dia" / "archivo"
    archivo_dir.mkdir(parents=True, exist_ok=True)
    nombre_archivado = f"{fecha.isoformat()}-{_slug_ts(ts)}.md"
    destino = archivo_dir / nombre_archivado

    if destino.exists():
        return JSONResponse({"ok": False, "error": "ya_archivada", "detalle": str(destino.relative_to(VAULT_BASE))}, status_code=409, headers=cors_headers())

    contenido_archivado = serialize_fm(target.meta, target.texto + "\n")
    try:
        escribir_atomico(destino, contenido_archivado)
    except Exception as e:  # noqa: BLE001
        log.exception(f"rid={rid} v2/archivar escribir destino: {e}")
        return JSONResponse({"ok": False, "error": "vault_write_failed", "detalle": str(e)}, status_code=500, headers=cors_headers())

    # Eliminar la entrada del archivo del día
    entradas_restantes = [e for e in entradas if e.ts != ts]
    archivo_dia = VAULT_BASE / "dia" / f"{fecha.isoformat()}.md"
    try:
        if entradas_restantes:
            escribir_dia(VAULT_BASE, fecha, entradas_restantes)
        else:
            # Si era la última entrada del día, dejar archivo con solo el header
            archivo_dia.write_text(f"# Diario — {fecha.isoformat()}\n", encoding="utf-8")
    except Exception as e:  # noqa: BLE001
        # Revert: borrar el archivado y devolver 500
        try:
            destino.unlink(missing_ok=True)
        except Exception:
            pass
        log.exception(f"rid={rid} v2/archivar reescribir día: {e}")
        return JSONResponse({"ok": False, "error": "vault_write_failed", "detalle": str(e)}, status_code=500, headers=cors_headers())

    # Actualizar wiki_index: la entrada archivada deja de contar
    try:
        # La entrada archivada está en dia/archivo/ que está excluido por defecto
        get_index().actualizar_nota(destino, contenido_archivado)
        # El archivo del día puede haber perdido wikilinks → re-indexar
        if archivo_dia.exists():
            get_index().actualizar_nota(archivo_dia, archivo_dia.read_text(encoding="utf-8"))
    except Exception:
        log.exception("rid=%s wiki_index update falló (no fatal)", rid)

    response = {
        "ok": True,
        "new_path": str(destino.relative_to(VAULT_BASE)),
        "archived_at": target.meta["archived_at"],
    }
    log_line(rid, sub, "v2/archivar", 200, (time.perf_counter() - t0) * 1000, f"ts={ts}")
    return JSONResponse(response, status_code=200, headers=cors_headers())


async def restaurar_handler(request: Request, autenticador, cors_headers, log_line) -> JSONResponse:
    t0 = time.perf_counter()
    rid = request.headers.get("x-request-id") or "anon"
    payload = await autenticador(request)
    if not payload:
        log_line(rid, "", "v2/restaurar", 401, (time.perf_counter() - t0) * 1000)
        return JSONResponse({"ok": False, "error": "auth_invalido"}, status_code=401, headers=cors_headers())

    sub = str(payload.get("sub", ""))

    try:
        body = json.loads(await request.body() or b"{}")
    except json.JSONDecodeError:
        return JSONResponse({"ok": False, "error": "json_invalido"}, status_code=400, headers=cors_headers())

    rel_path = (body.get("path") or "").strip()
    if not rel_path.startswith("dia/archivo/") or not rel_path.endswith(".md"):
        return JSONResponse({"ok": False, "error": "path_invalido", "detalle": "esperaba dia/archivo/<fecha>-<ts-slug>.md"}, status_code=400, headers=cors_headers())

    src = VAULT_BASE / rel_path
    if not src.exists():
        return JSONResponse({"ok": False, "error": "not_found"}, status_code=404, headers=cors_headers())

    # Parsear el archivado para recuperar la entrada
    contenido = src.read_text(encoding="utf-8")
    entradas_parsed = parsear_dia(contenido)
    if len(entradas_parsed) != 1:
        # Fallback: archivo archivado tiene formato frontmatter+body simple, no
        # archivo-de-día. Lo parseamos manualmente.
        from tablero.v2.frontmatter import parse as parse_fm
        meta, texto = parse_fm(contenido)
        if not meta or "ts" not in meta:
            return JSONResponse({"ok": False, "error": "archivado_corrupto"}, status_code=500, headers=cors_headers())
        entry = Entrada(ts=str(meta["ts"]), meta=meta, texto=texto.strip())
    else:
        entry = entradas_parsed[0]

    # Limpiar campos de archivado
    entry.meta.pop("archived_at", None)
    entry.meta.pop("archive_reason", None)
    entry.meta.pop("archived_by", None)
    # Marca de restauración con modified_at (D-003)
    entry.meta["modified_at"] = now_modified_at()
    entry.meta["restored_by"] = sub

    # Determinar la fecha de destino del ts
    try:
        fecha = datetime.fromisoformat(entry.ts).date()
    except ValueError:
        return JSONResponse({"ok": False, "error": "ts_invalido"}, status_code=500, headers=cors_headers())

    # Re-insertar en el día correspondiente
    dia_entradas = leer_dia(VAULT_BASE, fecha)
    # Verificar que no haya colisión por ts
    if any(e.ts == entry.ts for e in dia_entradas):
        return JSONResponse({"ok": False, "error": "ts_collision", "detalle": "ya existe entrada con ese ts en el día"}, status_code=409, headers=cors_headers())

    dia_entradas.append(entry)
    try:
        escribir_dia(VAULT_BASE, fecha, dia_entradas)
        src.unlink()
    except Exception as e:  # noqa: BLE001
        log.exception(f"rid={rid} v2/restaurar: {e}")
        return JSONResponse({"ok": False, "error": "vault_write_failed", "detalle": str(e)}, status_code=500, headers=cors_headers())

    # Actualizar wiki_index
    try:
        archivo_dia = VAULT_BASE / "dia" / f"{fecha.isoformat()}.md"
        get_index().actualizar_nota(archivo_dia, archivo_dia.read_text(encoding="utf-8"))
        get_index().eliminar_nota(src)
    except Exception:
        log.exception("rid=%s wiki_index update falló (no fatal)", rid)

    response = {
        "ok": True,
        "new_path": f"dia/{fecha.isoformat()}.md#{entry.ts}",
        "fecha": fecha.isoformat(),
        "ts": entry.ts,
    }
    log_line(rid, sub, "v2/restaurar", 200, (time.perf_counter() - t0) * 1000, f"ts={entry.ts}")
    return JSONResponse(response, status_code=200, headers=cors_headers())
