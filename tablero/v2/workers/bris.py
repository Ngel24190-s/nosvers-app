"""Worker bris: agrega datos de animaux/bris/*.md."""
from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

from claudio_tools.common import parse_frontmatter, vault


def _bris_dir() -> Path:
    return vault() / "animaux" / "bris"


async def bris_tick() -> dict | None:
    d = _bris_dir()
    if not d.exists():
        return {"empty": True}
    proxima_vacuna: str | None = None
    ultimo_paseo: str | None = None
    peso_kg: float | None = None
    animo: str | None = None
    try:
        for p in d.glob("*.md"):
            try:
                text = p.read_text(encoding="utf-8")
            except Exception:
                continue
            meta, body = parse_frontmatter(text)
            tipo = (str(meta.get("tipo", "")) or p.stem.split("-")[-1]).lower()
            fecha = str(meta.get("fecha", "")) or str(meta.get("date", ""))
            if "vacuna" in tipo or "vacuna" in p.stem.lower():
                try:
                    f = date.fromisoformat(fecha)
                    if f >= date.today() and (
                        proxima_vacuna is None or f.isoformat() < proxima_vacuna
                    ):
                        proxima_vacuna = f.isoformat()
                except Exception:
                    pass
            if "paseo" in tipo or "paseo" in p.stem.lower():
                if ultimo_paseo is None or fecha > ultimo_paseo:
                    ultimo_paseo = fecha
            try:
                peso = meta.get("peso_kg")
                if peso is not None:
                    peso_kg = float(peso)
            except (TypeError, ValueError):
                pass
            if meta.get("animo"):
                animo = str(meta.get("animo"))
    except Exception:
        return {"empty": True}
    if not any([proxima_vacuna, ultimo_paseo, peso_kg, animo]):
        return {"empty": True, "nombre": "Bris"}
    return {
        "nombre": "Bris",
        "proxima_vacuna": proxima_vacuna,
        "ultimo_paseo": ultimo_paseo,
        "peso_kg": peso_kg,
        "animo": animo,
        "ts": datetime.now().isoformat(timespec="seconds"),
    }
