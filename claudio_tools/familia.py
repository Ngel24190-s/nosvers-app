"""Recordatorios familiares y cumpleaños.

- recordatorio_crear(texto, fecha, autor, prioridad)
- recordatorios_listar(periodo, autor)
- recordatorio_completar(id_o_slug)
- familia_cumpleanos_listar(meses)
"""

from __future__ import annotations

import re
from datetime import date, datetime, timedelta
from pathlib import Path

from .common import (
    atomic_write, dump_frontmatter, ensure_dir, log_call, normalize_author,
    parse_date, parse_frontmatter, slugify, today_iso, ts_iso, vault,
)


def _recordatorios_dir() -> Path:
    return vault() / "familia" / "recordatorios"


def _completados_dir() -> Path:
    return _recordatorios_dir() / "completados"


def recordatorio_crear(
    texto: str,
    fecha: str,
    autor: str,
    prioridad: int = 3,
) -> str:
    """Crea un recordatorio fechado en `familia/recordatorios/<slug>.md`.

    Args:
        texto: descripción legible (1-3 frases).
        fecha: 'YYYY-MM-DD' o 'hoy' / 'mañana'.
        autor: angel | africa | compartido.
        prioridad: 1 (muy bajo) a 10 (urgente). Default 3.
    """
    args_log = {"len_texto": len(texto or ""), "fecha": fecha,
                "prioridad": prioridad}
    try:
        a = normalize_author(autor, allow_bris=False)
        if not texto or not texto.strip():
            raise ValueError("texto vacío")
        f = parse_date(fecha)
        if not f and fecha.lower() == "hoy":
            f = date.today()
        if not f and fecha.lower() in ("manana", "mañana"):
            f = date.today() + timedelta(days=1)
        if not f:
            raise ValueError(f"fecha inválida: {fecha!r}")
        prio = max(1, min(10, int(prioridad)))
        slug = slugify(texto)
        fname = f"{f.isoformat()}-{slug}.md"
        path = _recordatorios_dir() / fname
        if path.exists():
            # Evitar collision: añade sufijo
            i = 2
            while path.exists():
                path = _recordatorios_dir() / f"{f.isoformat()}-{slug}-{i}.md"
                i += 1
        meta = {
            "fecha": f.isoformat(),
            "autor": a,
            "prioridad": prio,
            "hecho": False,
            "creado": ts_iso(),
        }
        body = texto.strip() + "\n"
        atomic_write(path, dump_frontmatter(meta, body))
        log_call("recordatorio_crear", a, args_log, True,
                 {"path": str(path.relative_to(vault()))})
        return f"⏰ Recordatorio creado: «{texto.strip()[:60]}» para {f.isoformat()} (prio {prio})"
    except Exception as e:
        log_call("recordatorio_crear", autor or "?", args_log, False,
                 {"error": str(e)[:200]})
        return f"❌ {e}"


def recordatorios_listar(
    periodo: str = "proximos_7_dias",
    autor: str = "",
) -> str:
    """Lista recordatorios activos.

    Args:
        periodo: 'hoy' | 'mañana' | 'proximos_7_dias' | 'proximos_30_dias' | 'todos'
        autor: filtra por autor (vacío = todos los autores).
    """
    args_log = {"periodo": periodo, "autor": autor}
    try:
        hoy = date.today()
        rangos = {
            "hoy": (hoy, hoy),
            "manana": (hoy + timedelta(days=1), hoy + timedelta(days=1)),
            "mañana": (hoy + timedelta(days=1), hoy + timedelta(days=1)),
            "proximos_7_dias": (hoy, hoy + timedelta(days=7)),
            "proximos_30_dias": (hoy, hoy + timedelta(days=30)),
            "todos": (date(1970, 1, 1), date(2999, 12, 31)),
        }
        if periodo not in rangos:
            raise ValueError(
                f"periodo inválido: {periodo!r}. Valores: {sorted(rangos)}"
            )
        ini, fin = rangos[periodo]
        autor_norm = normalize_author(autor, allow_bris=False) if autor else ""

        base = _recordatorios_dir()
        if not base.exists():
            log_call("recordatorios_listar", autor_norm or "todos",
                     args_log, True, {"hits": 0})
            return "(sin recordatorios)"

        items: list[tuple[date, int, str, str, str]] = []  # (fecha, prio, autor, texto, slug)
        for fp in base.glob("*.md"):
            if fp.is_dir():
                continue
            try:
                text = fp.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            meta, body = parse_frontmatter(text)
            if meta.get("hecho") is True:
                continue
            f = parse_date(str(meta.get("fecha", "")))
            if not f:
                continue
            if not (ini <= f <= fin):
                continue
            au = str(meta.get("autor", "")).lower()
            if autor_norm and au != autor_norm:
                continue
            prio = int(meta.get("prioridad", 3))
            items.append((f, prio, au, body.strip(), fp.stem))

        items.sort(key=lambda x: (x[0], -x[1]))
        if not items:
            log_call("recordatorios_listar", autor_norm or "todos",
                     args_log, True, {"hits": 0})
            return f"(sin recordatorios en {periodo})"

        lines = [f"⏰ **Recordatorios · {periodo}** ({len(items)})"]
        for f, prio, au, texto, slug in items:
            icon = "🔴" if prio >= 8 else ("🟠" if prio >= 5 else "🟢")
            primer = texto.split("\n", 1)[0][:80]
            lines.append(f"  {icon} {f.isoformat()} · {au} · {primer}  `[{slug}]`")
        log_call("recordatorios_listar", autor_norm or "todos",
                 args_log, True, {"hits": len(items)})
        return "\n".join(lines)
    except Exception as e:
        log_call("recordatorios_listar", autor or "?", args_log, False,
                 {"error": str(e)[:200]})
        return f"❌ {e}"


def recordatorio_completar(id_o_slug: str) -> str:
    """Marca un recordatorio como hecho y lo mueve a completados/.

    Args:
        id_o_slug: nombre del archivo sin .md (ej '2026-06-12-cumpleanos-lucia').
                   Si no es el nombre exacto, se busca el primer match parcial.
    """
    args_log = {"id_o_slug": id_o_slug}
    try:
        base = _recordatorios_dir()
        if not base.exists():
            raise FileNotFoundError("dir recordatorios no existe")
        candidato = base / f"{id_o_slug}.md"
        if not candidato.exists():
            # Búsqueda parcial
            matches = [
                fp for fp in base.glob("*.md")
                if id_o_slug.lower() in fp.stem.lower()
            ]
            if not matches:
                raise FileNotFoundError(f"no encuentro recordatorio {id_o_slug!r}")
            if len(matches) > 1:
                names = ", ".join(m.stem for m in matches[:5])
                raise ValueError(f"ambiguo, varios matches: {names}")
            candidato = matches[0]

        text = candidato.read_text(encoding="utf-8", errors="replace")
        meta, body = parse_frontmatter(text)
        meta["hecho"] = True
        meta["completado"] = ts_iso()
        ensure_dir(_completados_dir())
        destino = _completados_dir() / candidato.name
        atomic_write(destino, dump_frontmatter(meta, body))
        candidato.unlink()
        log_call("recordatorio_completar", str(meta.get("autor", "?")),
                 args_log, True, {"slug": candidato.stem})
        return f"✅ Completado: {candidato.stem}"
    except Exception as e:
        log_call("recordatorio_completar", "?", args_log, False,
                 {"error": str(e)[:200]})
        return f"❌ {e}"


# ── Cumpleaños ───────────────────────────────────────────────
def familia_cumpleanos_listar(meses: int = 12) -> str:
    """Lista cumpleaños de los próximos `meses` meses.

    Lee `familia/cumpleanos.md` (formato `- MM-DD · Nombre · relación`).
    """
    args_log = {"meses": meses}
    try:
        m = max(1, min(12, int(meses)))
        path = vault() / "familia" / "cumpleanos.md"
        if not path.exists():
            log_call("familia_cumpleanos_listar", "compartido",
                     args_log, True, {"hits": 0})
            return "(sin lista de cumpleaños — crear familia/cumpleanos.md)"
        text = path.read_text(encoding="utf-8", errors="replace")
        hoy = date.today()
        limite = hoy + timedelta(days=m * 31)
        entry_re = re.compile(r"^-\s*(\d{2})-(\d{2})\s*·\s*([^·]+?)(?:\s*·\s*(.+))?\s*$")
        items: list[tuple[date, str, str]] = []
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("<!--"):
                continue
            mt = entry_re.match(line)
            if not mt:
                continue
            mo, dd, nombre, rel = mt.group(1), mt.group(2), mt.group(3), mt.group(4)
            try:
                f_anio = date(hoy.year, int(mo), int(dd))
            except ValueError:
                continue
            f = f_anio if f_anio >= hoy else date(hoy.year + 1, int(mo), int(dd))
            if f > limite:
                continue
            items.append((f, nombre.strip(), (rel or "").strip()))
        if not items:
            log_call("familia_cumpleanos_listar", "compartido",
                     args_log, True, {"hits": 0})
            return f"(sin cumpleaños en los próximos {m} meses)"
        items.sort(key=lambda x: x[0])
        lines = [f"🎂 **Cumpleaños · próximos {m} meses** ({len(items)})"]
        for f, nombre, rel in items:
            extra = f" — {rel}" if rel else ""
            dias = (f - hoy).days
            lines.append(f"  • {f.isoformat()} ({dias}d) · {nombre}{extra}")
        log_call("familia_cumpleanos_listar", "compartido",
                 args_log, True, {"hits": len(items)})
        return "\n".join(lines)
    except Exception as e:
        log_call("familia_cumpleanos_listar", "compartido",
                 args_log, False, {"error": str(e)[:200]})
        return f"❌ {e}"
