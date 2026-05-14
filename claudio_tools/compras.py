"""Lista de la compra y despensa.

- lista_compras_añadir(item, autor, cantidad, urgente)
- lista_compras_ver()
- lista_compras_completar(item)
- despensa_estado()
"""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from .common import (
    atomic_append, atomic_write, ensure_dir, log_call, month_iso,
    normalize_author, today_iso, vault,
)


def _lista_path() -> Path:
    return vault() / "compras" / "lista_actual.md"


def _historico_path() -> Path:
    return vault() / "compras" / "historico" / f"{month_iso()}.md"


def _normalize_item(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip().lower()


def lista_compras_añadir(
    item: str,
    autor: str,
    cantidad: str = "",
    urgente: bool = False,
) -> str:
    """Añade un item a la lista vigente.

    Args:
        item: producto a comprar.
        autor: quién lo añade (angel | africa).
        cantidad: opcional (ej "1kg", "2 botes").
        urgente: si True, prefija ⚠️.
    """
    args_log = {"len_item": len(item or ""), "cantidad": cantidad,
                "urgente": urgente}
    try:
        a = normalize_author(autor, allow_bris=False)
        if not item or not item.strip():
            raise ValueError("item vacío")
        path = _lista_path()
        if not path.exists():
            ensure_dir(path.parent)
            atomic_append(path, "# Lista de la compra\n\n")

        text = path.read_text(encoding="utf-8", errors="replace")
        normalizado = _normalize_item(item)
        # Evitar duplicados activos (líneas con `[ ]`)
        for raw in text.splitlines():
            mt = re.match(r"^- \[ \] (.+?) ·", raw)
            if mt and _normalize_item(mt.group(1).split("·")[0]) == normalizado:
                log_call("lista_compras_anadir", a, args_log, True,
                         {"duplicado": True})
                return f"ℹ️ Ya está en lista: {item.strip()}"

        prefix = "⚠️ " if urgente else ""
        cant_str = f" ({cantidad})" if cantidad else ""
        line = f"- [ ] {prefix}{item.strip()}{cant_str} · {a} · {today_iso()}\n"
        atomic_append(path, line)
        log_call("lista_compras_anadir", a, args_log, True,
                 {"duplicado": False})
        return f"🛒 Añadido: {item.strip()}{cant_str}"
    except Exception as e:
        log_call("lista_compras_anadir", autor or "?", args_log, False,
                 {"error": str(e)[:200]})
        return f"❌ {e}"


def lista_compras_ver() -> str:
    """Devuelve la lista vigente, agrupada por autor."""
    args_log = {}
    try:
        path = _lista_path()
        if not path.exists():
            log_call("lista_compras_ver", "compartido",
                     args_log, True, {"hits": 0})
            return "(lista vacía)"
        text = path.read_text(encoding="utf-8", errors="replace")
        items: list[tuple[str, str, str]] = []  # (autor, fecha, contenido)
        for raw in text.splitlines():
            mt = re.match(r"^- \[ \] (.+)$", raw)
            if not mt:
                continue
            line = mt.group(1)
            # Estructura "<item> · <autor> · <fecha>"
            partes = [p.strip() for p in line.rsplit("·", 2)]
            if len(partes) == 3:
                contenido, au, fecha = partes
            else:
                contenido, au, fecha = line, "?", ""
            items.append((au, fecha, contenido))
        if not items:
            log_call("lista_compras_ver", "compartido",
                     args_log, True, {"hits": 0})
            return "(lista vacía)"
        lines = [f"🛒 **Lista de la compra** ({len(items)})"]
        for au, fecha, contenido in items:
            lines.append(f"  ☐ {contenido}  ({au})")
        log_call("lista_compras_ver", "compartido",
                 args_log, True, {"hits": len(items)})
        return "\n".join(lines)
    except Exception as e:
        log_call("lista_compras_ver", "compartido",
                 args_log, False, {"error": str(e)[:200]})
        return f"❌ {e}"


def lista_compras_completar(item: str) -> str:
    """Marca un item como comprado: lo quita de la lista activa y lo añade al
    histórico del mes actual.

    Match: el item se identifica por coincidencia parcial case-insensitive en
    `lista_actual.md`. Si hay ambigüedad → error.
    """
    args_log = {"item": item}
    try:
        path = _lista_path()
        if not path.exists():
            raise FileNotFoundError("lista_actual.md no existe")
        text = path.read_text(encoding="utf-8", errors="replace")
        target = _normalize_item(item)
        if not target:
            raise ValueError("item vacío")

        out_lines = []
        completados = []
        for raw in text.splitlines():
            mt = re.match(r"^- \[ \] (.+)$", raw)
            if mt and target in _normalize_item(mt.group(1)):
                completados.append(mt.group(1))
                continue
            out_lines.append(raw)

        if not completados:
            log_call("lista_compras_completar", "compartido",
                     args_log, True, {"hits": 0})
            return f"(no encuentro «{item}» en la lista activa)"
        if len(completados) > 3:
            # Demasiado ambiguo
            log_call("lista_compras_completar", "compartido",
                     args_log, False, {"ambiguo": len(completados)})
            return (
                f"❌ Ambigüedad: «{item}» matchea {len(completados)} items. "
                "Sé más específico."
            )

        atomic_write(path, "\n".join(out_lines).rstrip() + "\n")
        # Append al histórico
        hist = _historico_path()
        if not hist.exists():
            ensure_dir(hist.parent)
            atomic_append(hist, f"# Compras hechas · {month_iso()}\n\n")
        for c in completados:
            atomic_append(hist, f"- {today_iso()} · {c}\n")
        log_call("lista_compras_completar", "compartido",
                 args_log, True, {"hits": len(completados)})
        return f"✅ Completado ({len(completados)}): {', '.join(c[:30] for c in completados)}"
    except Exception as e:
        log_call("lista_compras_completar", "compartido",
                 args_log, False, {"error": str(e)[:200]})
        return f"❌ {e}"


def despensa_estado() -> str:
    """Devuelve el contenido de `compras/despensa.yaml`, agrupado por categoría."""
    args_log = {}
    try:
        path = vault() / "compras" / "despensa.yaml"
        if not path.exists():
            log_call("despensa_estado", "compartido",
                     args_log, True, {"hits": 0})
            return "(sin despensa.yaml)"
        try:
            import yaml
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except Exception as e:
            return f"❌ YAML inválido: {e}"
        items = data.get("items") or []
        if not items:
            log_call("despensa_estado", "compartido",
                     args_log, True, {"hits": 0})
            return "(despensa vacía — rellenar compras/despensa.yaml)"
        grupos: dict[str, list[str]] = {}
        for it in items:
            cat = str(it.get("categoria", "otros"))
            prod = str(it.get("producto", "?"))
            cant = str(it.get("cantidad", ""))
            cad = str(it.get("caducidad", ""))
            chunk = f"{prod} ({cant})" + (f" — cad {cad}" if cad else "")
            grupos.setdefault(cat, []).append(chunk)
        lines = [f"🥫 **Despensa** ({len(items)} items)"]
        for cat, prods in sorted(grupos.items()):
            lines.append(f"\n  *{cat}*")
            for p in prods:
                lines.append(f"    • {p}")
        log_call("despensa_estado", "compartido",
                 args_log, True, {"hits": len(items)})
        return "\n".join(lines)
    except Exception as e:
        log_call("despensa_estado", "compartido",
                 args_log, False, {"error": str(e)[:200]})
        return f"❌ {e}"
