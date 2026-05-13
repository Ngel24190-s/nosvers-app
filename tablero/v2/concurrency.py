"""tablero.v2.concurrency — concurrencia optimista por If-Match (D-003).

Cliente envía header `If-Match: <modified_at_ISO>` en PATCH/POST/DELETE write.
Servidor compara con el `modified_at` actual del archivo en disco. Si difiere
→ HTTP 409 con `current_modified_at` para que el cliente pueda recargar.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from starlette.requests import Request
from starlette.responses import JSONResponse

from tablero.v2.frontmatter import parse


class StaleModifiedAt(Exception):
    def __init__(self, current: str | None):
        self.current = current
        super().__init__(f"stale modified_at; current={current}")


def leer_modified_at(archivo: Path) -> str | None:
    """Lee y devuelve el campo modified_at del frontmatter de un archivo .md.

    Devuelve None si el archivo no existe, no tiene frontmatter, o el campo
    no está presente.
    """
    if not archivo.exists():
        return None
    try:
        text = archivo.read_text(encoding="utf-8")
    except OSError:
        return None
    meta, _ = parse(text)
    val = meta.get("modified_at")
    return str(val) if val is not None else None


def verificar_if_match(request: Request, archivo: Path) -> None:
    """Lanza StaleModifiedAt si el header If-Match no coincide con el archivo.

    Si el archivo no tiene modified_at todavía (notas Fase A pre-B+C), aceptar
    cualquier If-Match — el primer guardado introduce el campo y futuros writes
    verifican.
    """
    cliente = request.headers.get("If-Match", "").strip()
    if not cliente:
        # Falta el header — el caller debe responder 428 Precondition Required
        raise StaleModifiedAt(None)
    actual = leer_modified_at(archivo)
    if actual is None:
        return  # archivo sin modified_at todavía → aceptar
    if cliente != actual:
        raise StaleModifiedAt(actual)


def respuesta_409(actual: str | None, cors_headers: dict | None = None) -> JSONResponse:
    payload: dict[str, Any] = {"ok": False, "error": "stale_modified_at"}
    if actual is not None:
        payload["current_modified_at"] = actual
    return JSONResponse(payload, status_code=409, headers=cors_headers or {})


def respuesta_428(cors_headers: dict | None = None) -> JSONResponse:
    return JSONResponse(
        {"ok": False, "error": "missing_if_match"},
        status_code=428,
        headers=cors_headers or {},
    )
