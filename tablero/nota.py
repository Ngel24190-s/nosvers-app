"""
tablero.nota — read a single note's full content for the detail view.

Path-safety: every requested path is resolved against the vault's `dia/` directory;
anything escaping it raises PathUnsafe and the REST handler maps it to 400.
"""
from __future__ import annotations

import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path

sys.path.insert(0, "/home/nosvers")

from voz.vault_io import DIA_DIR, leer_dia  # noqa: E402


class PathUnsafe(Exception):
    """Requested `path` would resolve outside `knowledge_base/dia/`."""


class NotaNotFound(Exception):
    """No note matched the (date, ts) pair in the request path."""


_PATH_RE = re.compile(r"^dia/(\d{4}-\d{2}-\d{2})\.md#(.+)$")
_ATTACH_RE = re.compile(r"!\[[^\]]*\]\((attachments/[^)]+)\)")

_DIA_RESOLVED = DIA_DIR.resolve()


def _ensure_safe(p: Path) -> Path:
    """Resolve `p` and confirm it sits under DIA_DIR. Raises PathUnsafe otherwise."""
    try:
        resolved = p.resolve()
    except (OSError, RuntimeError) as e:
        raise PathUnsafe(f"path resolution failed: {e}") from e
    try:
        resolved.relative_to(_DIA_RESOLVED)
    except ValueError as e:
        raise PathUnsafe(f"path escapes {_DIA_RESOLVED}: {resolved}") from e
    return resolved


def _attachments_de(body_md: str) -> list[dict]:
    """Scan the markdown body for `attachments/...` image references."""
    out: list[dict] = []
    seen: set[str] = set()
    for m in _ATTACH_RE.finditer(body_md):
        src = m.group(1)
        if src in seen:
            continue
        seen.add(src)
        rel = src.split("attachments/", 1)[-1] if src.startswith("attachments/") else src
        candidate = (DIA_DIR / rel).resolve()
        try:
            exists = candidate.exists() and candidate.is_file()
        except OSError:
            exists = False
        kind = "image"
        low = src.lower()
        if low.endswith((".opus", ".mp3", ".wav", ".m4a", ".ogg")):
            kind = "audio"
        elif not low.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg")):
            kind = "other"
        out.append({"src": src, "exists": exists, "kind": kind})
    return out


def leer_nota(path: str) -> dict:
    """Resolve `path` (e.g. `dia/2026-05-13.md#<ts>`) and return the full payload.

    Returns the dict matching contracts/nota.openapi.yaml `NoteFull`. Raises:
      - ValueError when `path` doesn't match the expected shape (handler → 400).
      - PathUnsafe when the resolved path escapes the vault (handler → 400).
      - NotaNotFound when the day file is missing or no note matches `ts`.
    """
    if not path:
        raise ValueError("path requerido")
    m = _PATH_RE.match(path)
    if not m:
        raise ValueError("path no coincide con el patrón dia/YYYY-MM-DD.md#<ts>")
    fecha_str, ts_fragment = m.group(1), m.group(2)
    try:
        fecha = date.fromisoformat(fecha_str)
    except ValueError as e:
        raise ValueError(f"fecha inválida en path: {e}") from e

    day_file = DIA_DIR / f"{fecha.isoformat()}.md"
    safe_path = _ensure_safe(day_file)
    if not safe_path.exists():
        raise NotaNotFound(f"day file missing: {fecha.isoformat()}")

    notas = leer_dia(fecha)
    chosen = next((n for n in notas if n.ts == ts_fragment), None)
    if chosen is None:
        raise NotaNotFound(f"no note with ts={ts_fragment!r} in {fecha.isoformat()}")

    try:
        mtime_iso = datetime.fromtimestamp(safe_path.stat().st_mtime, tz=timezone.utc).isoformat()
    except OSError:
        mtime_iso = ""

    frontmatter = {
        "ts": chosen.ts,
        "autor": chosen.autor,
        "etiqueta": chosen.etiqueta,
        "origen": chosen.origen,
        "audio": chosen.audio,
        "clasificador_confianza": chosen.clasificador_confianza,
        "clasificador_modelo": chosen.clasificador_modelo,
    }

    body_markdown = chosen.texto or ""
    return {
        "path": path,
        "frontmatter": frontmatter,
        "body_markdown": body_markdown,
        "mtime": mtime_iso,
        "attachments": _attachments_de(body_markdown),
    }


__all__ = ["leer_nota", "PathUnsafe", "NotaNotFound"]
