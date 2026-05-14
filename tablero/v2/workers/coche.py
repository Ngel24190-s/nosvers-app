"""Worker coche: lee coche/INDEX.md y devuelve estado."""
from __future__ import annotations

from datetime import date
from pathlib import Path

from claudio_tools.common import parse_frontmatter, vault


def _index_file() -> Path:
    return vault() / "coche" / "INDEX.md"


async def coche_tick() -> dict | None:
    path = _index_file()
    if not path.exists():
        return {"empty": True}
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return {"empty": True}
    meta, _body = parse_frontmatter(text)
    if not meta:
        return {"empty": True}
    # Si todos los campos clave están vacíos, treat as empty
    campos_clave = [meta.get(k) for k in (
        "matricula", "modelo", "kilometros", "itv_proxima", "seguro_renovacion"
    )]
    if not any(campos_clave):
        return {"empty": True}
    out: dict = {
        "matricula": str(meta.get("matricula", "")),
        "modelo": str(meta.get("modelo", "")),
        "kilometros": meta.get("kilometros"),
        "itv_proxima": str(meta.get("itv_proxima", "")),
        "seguro_renovacion": str(meta.get("seguro_renovacion", "")),
        "ultimo_mantenimiento": str(meta.get("ultimo_mantenimiento", "")),
    }
    # Días hasta ITV
    try:
        if out["itv_proxima"]:
            f = date.fromisoformat(out["itv_proxima"])
            out["itv_dias_falta"] = (f - date.today()).days
    except ValueError:
        out["itv_dias_falta"] = None
    try:
        if out["seguro_renovacion"]:
            f = date.fromisoformat(out["seguro_renovacion"])
            out["seguro_dias_falta"] = (f - date.today()).days
    except ValueError:
        out["seguro_dias_falta"] = None
    return out
