"""Tools de menús y recetas.

- menu_sugerir(dia, ingredientes_disponibles)
- receta_guardar(nombre, ingredientes, pasos, fuente)
"""

from __future__ import annotations

import unicodedata
from pathlib import Path

from .common import (
    atomic_write, dump_frontmatter, ensure_dir, log_call, parse_frontmatter,
    slugify, today_iso, ts_iso, vault,
)


def _recetas_dir() -> Path:
    return vault() / "menus" / "recetas"


def _strip(s: str) -> str:
    t = unicodedata.normalize("NFKD", s)
    return "".join(c for c in t if not unicodedata.combining(c)).lower()


def menu_sugerir(dia: str = "", ingredientes_disponibles: str = "") -> str:
    """Sugiere recetas filtrando por ingredientes disponibles.

    Args:
        dia: 'YYYY-MM-DD' o '' (hoy). Solo informativo.
        ingredientes_disponibles: CSV (ej "tomate, cebolla, huevo"). Si está
            vacío, devuelve las primeras 10 recetas alfabéticamente.

    Devuelve un ranking de recetas: las que matchean más ingredientes primero,
    luego las simples.
    """
    args_log = {"dia": dia, "len_ing": len(ingredientes_disponibles or "")}
    try:
        base = _recetas_dir()
        if not base.exists() or not list(base.glob("*.md")):
            log_call("menu_sugerir", "compartido",
                     args_log, True, {"hits": 0})
            return "(sin recetas — usar receta_guardar para añadir)"

        disponibles = {
            _strip(x).strip()
            for x in ingredientes_disponibles.split(",")
            if x.strip()
        }
        items: list[tuple[int, str, str, list[str]]] = []  # (score, slug, nombre, ings_match)
        for fp in base.glob("*.md"):
            try:
                text = fp.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            meta, _body = parse_frontmatter(text)
            nombre = str(meta.get("nombre", fp.stem.replace("-", " ").title()))
            ingredientes = meta.get("ingredientes") or []
            if isinstance(ingredientes, str):
                ingredientes = [x.strip() for x in ingredientes.split(",") if x.strip()]
            ings_norm = [_strip(str(x)) for x in ingredientes]
            if disponibles:
                hits = [i for i in ings_norm if i in disponibles]
                score = len(hits) * 10 - max(0, len(ings_norm) - len(hits))
                if not hits:
                    continue
            else:
                hits = []
                score = -len(ings_norm)  # prefiere simples
            items.append((score, fp.stem, nombre, hits))

        if not items:
            log_call("menu_sugerir", "compartido",
                     args_log, True, {"hits": 0})
            return (
                f"(ninguna receta matchea: {ingredientes_disponibles}). "
                "Añade recetas con receta_guardar."
            )

        items.sort(key=lambda x: (-x[0], x[1]))
        items = items[:10]
        target = dia or today_iso()
        lines = [f"🍽️ **Sugerencias menú · {target}** ({len(items)})"]
        for score, slug, nombre, hits in items:
            tag = f" — match: {', '.join(hits)}" if hits else ""
            lines.append(f"  • {nombre}  `[{slug}]`{tag}")
        log_call("menu_sugerir", "compartido",
                 args_log, True, {"hits": len(items)})
        return "\n".join(lines)
    except Exception as e:
        log_call("menu_sugerir", "compartido",
                 args_log, False, {"error": str(e)[:200]})
        return f"❌ {e}"


def receta_guardar(
    nombre: str,
    ingredientes: str,
    pasos: str,
    fuente: str = "",
) -> str:
    """Guarda una receta en `menus/recetas/<slug>.md` con frontmatter.

    Args:
        nombre: nombre de la receta.
        ingredientes: CSV de ingredientes (ej "tomate, cebolla, huevo, sal").
        pasos: texto con los pasos (markdown libre).
        fuente: origen (ej "abuela", "internet", "libro xxx").
    """
    args_log = {"len_nombre": len(nombre or ""),
                "len_ing": len(ingredientes or ""),
                "len_pasos": len(pasos or "")}
    try:
        if not nombre or not nombre.strip():
            raise ValueError("nombre vacío")
        if not pasos or not pasos.strip():
            raise ValueError("pasos vacíos")
        ings = [x.strip() for x in (ingredientes or "").split(",") if x.strip()]
        if not ings:
            raise ValueError("ingredientes vacíos")
        slug = slugify(nombre)
        path = _recetas_dir() / f"{slug}.md"
        if path.exists():
            i = 2
            while path.exists():
                path = _recetas_dir() / f"{slug}-{i}.md"
                i += 1
        ensure_dir(path.parent)
        meta = {
            "nombre": nombre.strip(),
            "ingredientes": ings,
            "fuente": fuente.strip() or "—",
            "creado": ts_iso(),
        }
        atomic_write(path, dump_frontmatter(meta, pasos.strip() + "\n"))
        log_call("receta_guardar", "compartido",
                 args_log, True, {"slug": slug})
        return f"🍳 Receta guardada: {nombre.strip()}  `[{path.stem}]`"
    except Exception as e:
        log_call("receta_guardar", "compartido",
                 args_log, False, {"error": str(e)[:200]})
        return f"❌ {e}"
