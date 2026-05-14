"""Worker compras: lee compras/lista_actual.md y devuelve items pendientes."""
from __future__ import annotations

import re
from pathlib import Path

from claudio_tools.common import vault

# Formato esperado:
#   - [ ] leche · angel · 2026-05-14
#   - [x] pan · angel · 2026-05-13
_LINE_RE = re.compile(
    r"^- \[(?P<done> |x|X)\]\s+(?P<rest>.+?)\s*$"
)


def _lista_file() -> Path:
    return vault() / "compras" / "lista_actual.md"


async def compras_tick() -> dict | None:
    p = _lista_file()
    if not p.exists():
        return {"empty": True}
    items: list[dict] = []
    completados = 0
    try:
        for raw in p.read_text(encoding="utf-8", errors="replace").splitlines():
            m = _LINE_RE.match(raw)
            if not m:
                continue
            done = m.group("done").lower() == "x"
            if done:
                completados += 1
                continue
            partes = [s.strip() for s in m.group("rest").split("·")]
            texto = partes[0] if partes else m.group("rest")
            autor = partes[1] if len(partes) > 1 else ""
            fecha = partes[2] if len(partes) > 2 else ""
            urgente = texto.startswith("⚠️")
            if urgente:
                texto = texto.lstrip("⚠️").strip()
            items.append({
                "texto": texto,
                "autor": autor,
                "fecha": fecha,
                "urgente": urgente,
            })
    except Exception:
        return {"empty": True}
    if not items and completados == 0:
        return {"empty": True}
    return {
        "items": items[:30],
        "total": len(items),
        "completados_pendientes_archivar": completados,
    }
