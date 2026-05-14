"""Tools de mantenimiento de la casa.

- casa_mantenimiento_anotar(tarea, fecha, proximo, autor)
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from .common import (
    atomic_append, ensure_dir, log_call, normalize_author, parse_date,
    today_iso, ts_human, vault,
)


def _mantenimiento_path() -> Path:
    return vault() / "casa" / "mantenimiento.md"


def casa_mantenimiento_anotar(
    tarea: str,
    fecha: str = "",
    proximo: str = "",
    autor: str = "angel",
) -> str:
    """Apunta una tarea de mantenimiento de la casa.

    Args:
        tarea: qué se hizo / se hará (ej "deshollinado chimenea").
        fecha: 'YYYY-MM-DD' o 'hoy'. Default: hoy.
        proximo: fecha estimada de la próxima vez (opcional).
        autor: angel | africa.
    """
    args_log = {"len_tarea": len(tarea or ""), "fecha": fecha,
                "proximo": proximo}
    try:
        a = normalize_author(autor, allow_bris=False)
        if not tarea or not tarea.strip():
            raise ValueError("tarea vacía")
        f = parse_date(fecha) if fecha else date.today()
        if fecha and fecha.lower() == "hoy":
            f = date.today()
        if not f:
            raise ValueError(f"fecha inválida: {fecha!r}")
        prox = parse_date(proximo) if proximo else None
        path = _mantenimiento_path()
        if not path.exists():
            ensure_dir(path.parent)
            atomic_append(path, "# Mantenimiento casa\n\n")
        extra = f" · próx {prox.isoformat()}" if prox else ""
        atomic_append(
            path,
            f"- {f.isoformat()} · {tarea.strip()} · {a}{extra}\n",
        )
        log_call("casa_mantenimiento_anotar", a, args_log, True)
        msg = f"🏠 Anotado: {tarea.strip()[:60]} ({f.isoformat()})"
        if prox:
            msg += f" · próx {prox.isoformat()}"
        return msg
    except Exception as e:
        log_call("casa_mantenimiento_anotar", autor or "?",
                 args_log, False, {"error": str(e)[:200]})
        return f"❌ {e}"
