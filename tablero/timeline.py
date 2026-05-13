"""
tablero.timeline — server-side helper that builds the merged TimelineEntry list.

Reuses voz.vault_io directly (Constitution IV). No write paths imported.
Returns plain dicts ready for JSON serialization per contracts/timeline.openapi.yaml.
"""
from __future__ import annotations

import sys
from datetime import date, timedelta
from typing import Iterable

sys.path.insert(0, "/home/nosvers")

from voz.vault_io import (  # noqa: E402  — path insertion is intentional
    AUTORES_VALIDOS,
    ETIQUETAS_VALIDAS,
    leer_dia,
    listar_dias,
)

_TITLE_MAX = 120
_PREVIEW_MAX = 200


def _titulo_de(texto: str) -> str | None:
    for line in (texto or "").splitlines():
        s = line.strip()
        if not s:
            continue
        s = s.lstrip("#").strip()
        if not s:
            continue
        return s[:_TITLE_MAX] + ("…" if len(s) > _TITLE_MAX else "")
    return None


def _preview_de(texto: str) -> str:
    flat = " ".join((texto or "").split())
    return flat[:_PREVIEW_MAX] + ("…" if len(flat) > _PREVIEW_MAX else "")


def _entrada_de_nota(fecha: date, nota) -> dict:
    return {
        "path": f"dia/{fecha.isoformat()}.md#{nota.ts}",
        "fecha": fecha.isoformat(),
        "ts": nota.ts,
        "autor": nota.autor,
        "etiqueta": nota.etiqueta,
        "origen": nota.origen,
        "titulo": _titulo_de(nota.texto),
        "preview": _preview_de(nota.texto),
        "tiene_audio": nota.audio is not None,
        "metadata_incompleta": False,
    }


def listar_timeline(
    desde: date | None = None,
    hasta: date | None = None,
    autor: str = "ambos",
    etiqueta: str = "",
    limit: int = 200,
    offset: int = 0,
) -> dict:
    """Build the merged timeline payload.

    Returns a dict matching the `entradas/total/rango` shape of the timeline contract.
    Date defaults: hasta=today, desde=hasta-30d (inclusive).
    """
    if hasta is None:
        hasta = date.today()
    if desde is None:
        desde = hasta - timedelta(days=30)
    if desde > hasta:
        raise ValueError("desde > hasta")

    autor_norm = (autor or "ambos").strip().lower()
    if autor_norm in {"", "ambos"}:
        filtro_autor: Iterable[str] = AUTORES_VALIDOS
    else:
        if autor_norm not in AUTORES_VALIDOS:
            raise ValueError(f"autor inválido: {autor_norm!r}")
        filtro_autor = {autor_norm}

    etiqueta_norm = (etiqueta or "").strip().lower()
    if etiqueta_norm and etiqueta_norm not in ETIQUETAS_VALIDAS:
        raise ValueError(f"etiqueta inválida: {etiqueta_norm!r}")

    entradas: list[dict] = []
    for f in listar_dias(desde, hasta):
        for n in leer_dia(f):
            if n.autor not in filtro_autor:
                continue
            if etiqueta_norm and n.etiqueta != etiqueta_norm:
                continue
            entradas.append(_entrada_de_nota(f, n))

    entradas.sort(key=lambda e: (e["fecha"], e["ts"]), reverse=True)
    total = len(entradas)
    limit = max(1, min(500, int(limit)))
    offset = max(0, int(offset))
    page = entradas[offset : offset + limit]

    return {
        "ok": True,
        "entradas": page,
        "total": len(page),
        "rango": {"desde": desde.isoformat(), "hasta": hasta.isoformat()},
    }


__all__ = ["listar_timeline"]
