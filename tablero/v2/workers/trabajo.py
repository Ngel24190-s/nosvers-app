"""Worker trabajo (007) — snapshot del dominio Trabajo cada 60s.

Lee `vault/trabajo/` y publica:
- chantiers_activos: int
- ultimo_evento: dict
- alertas: list
- equipe_disponible: int
- ts: ISO

Solo enviado a clientes con scope `trabajo` (filtro en broker.subscribe).
"""
from __future__ import annotations

import logging
from datetime import datetime, date
from pathlib import Path

from claudio_tools.common import parse_frontmatter, vault

log = logging.getLogger("tablero.v2.workers.trabajo")


def _read_chantier(idx: Path) -> dict | None:
    try:
        text = idx.read_text(encoding="utf-8")
    except Exception:
        return None
    meta, _ = parse_frontmatter(text)
    if not meta:
        return None
    meta["__slug"] = idx.parent.name
    return meta


def _ultimo_evento(slug: str, jdir: Path) -> dict | None:
    if not jdir.exists():
        return None
    files = sorted(jdir.glob("*.md"))
    if not files:
        return None
    last = files[-1]
    try:
        text = last.read_text(encoding="utf-8")
    except Exception:
        return None
    # buscar el último ## ts · icon tipo
    tipo = "journal"
    descripcion = ""
    for line in reversed(text.splitlines()):
        s = line.strip()
        if s.startswith("## "):
            parts = s[3:].split("·")
            if len(parts) >= 2:
                tipo = parts[-1].strip().split(" ")[-1] or "journal"
            break
        if s and not descripcion and not s.startswith("—"):
            descripcion = s[:120]
    return {
        "chantier": slug,
        "tipo": tipo,
        "descripcion": descripcion,
        "fecha": last.stem,
    }


async def trabajo_tick() -> dict | None:
    raiz = vault() / "trabajo"
    if not raiz.exists():
        return {"empty": True}
    chantiers_dir = raiz / "chantiers"
    activos: list[dict] = []
    alertas: list[dict] = []
    ultimo_global: dict | None = None
    ultimo_fecha = ""
    if chantiers_dir.exists():
        for sub in sorted(chantiers_dir.iterdir()):
            if not sub.is_dir() or sub.name.startswith("_"):
                continue
            idx = sub / "INDEX.md"
            if not idx.exists():
                continue
            meta = _read_chantier(idx)
            if not meta:
                continue
            estado = (meta.get("estado") or "activo").strip().lower()
            if estado == "activo":
                activos.append({
                    "slug": meta["__slug"],
                    "nombre": meta.get("nombre", meta["__slug"]),
                    "cliente": meta.get("cliente", "—"),
                })
            if estado == "urgente":
                alertas.append({
                    "chantier": meta["__slug"],
                    "tipo": "urgente",
                    "fecha": str(meta.get("fecha_inicio", "")),
                })
            ev = _ultimo_evento(meta["__slug"], sub / "journal")
            if ev and ev["fecha"] > ultimo_fecha:
                ultimo_fecha = ev["fecha"]
                ultimo_global = ev

    # Equipe disponible: cuenta operadores activos en operateurs.yaml
    equipe_path = raiz / "equipe" / "operateurs.yaml"
    equipe_disponible = 0
    if equipe_path.exists():
        try:
            text = equipe_path.read_text(encoding="utf-8")
            equipe_disponible = sum(1 for line in text.splitlines()
                                    if line.strip().startswith("- id:"))
        except Exception:
            equipe_disponible = 0

    return {
        "chantiers_activos": len(activos),
        "activos": activos[:10],
        "alertas": alertas,
        "ultimo_evento": ultimo_global,
        "equipe_disponible": equipe_disponible,
        "ts": datetime.utcnow().isoformat(timespec="seconds") + "Z",
    }
