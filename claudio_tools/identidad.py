"""Tools de identidad/memoria personal de Claudio.

- claudio_recordar(autor, hecho, importancia): añade hecho a memorias del autor
- claudio_contexto(autor, query): busca memorias relevantes para una query
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

from .common import (
    claudio_dir, ensure_dir, log_call, month_iso, normalize_author,
    ts_human, ts_iso, atomic_append,
)


def _memorias_dir(autor: str) -> Path:
    return claudio_dir() / "memorias" / autor


def _strip_accents(s: str) -> str:
    t = unicodedata.normalize("NFKD", s)
    return "".join(c for c in t if not unicodedata.combining(c)).lower()


def claudio_recordar(autor: str, hecho: str, importancia: int = 5) -> str:
    """Guarda un hecho personal en `claudio/memorias/{autor}/YYYY-MM.md`.

    Args:
        autor: angel | africa | compartido | bris (validado)
        hecho: texto del hecho a recordar (1 línea preferida)
        importancia: 1 (anecdótico) a 10 (clave). Default 5.

    Returns:
        Confirmación corta.
    """
    args_log = {"importancia": importancia, "len_hecho": len(hecho or "")}
    try:
        a = normalize_author(autor)
        if not hecho or not hecho.strip():
            raise ValueError("hecho vacío")
        imp = max(1, min(10, int(importancia)))
        path = _memorias_dir(a) / f"{month_iso()}.md"
        if not path.exists():
            ensure_dir(path.parent)
            header = f"# Memorias · {a} · {month_iso()}\n\n"
            atomic_append(path, header)
        line = f"- {ts_human()} · [imp:{imp}] {hecho.strip()}\n"
        atomic_append(path, line)
        log_call("claudio_recordar", a, args_log, True)
        return f"📝 Recordado para {a}: «{hecho.strip()[:80]}» (imp {imp})"
    except Exception as e:
        log_call("claudio_recordar", autor or "?", args_log, False,
                 {"error": str(e)[:200]})
        return f"❌ {e}"


def claudio_contexto(autor: str, query: str, limite: int = 10) -> str:
    """Busca memorias relevantes del autor para una query (case-insensitive,
    ignora diacríticos). Devuelve hasta `limite` líneas ordenadas por
    importancia desc, luego por recencia desc.
    """
    args_log = {"limite": limite, "len_query": len(query or "")}
    try:
        a = normalize_author(autor)
        q = _strip_accents(query.strip()) if query else ""
        base = _memorias_dir(a)
        if not base.exists():
            log_call("claudio_contexto", a, args_log, True, {"hits": 0})
            return f"(sin memorias para {a})"

        # Recorrer archivos mensuales en orden inverso de fecha
        archivos = sorted(base.glob("*.md"), reverse=True)
        matches: list[tuple[int, str, str]] = []  # (imp, ts_str, line)
        line_re = re.compile(r"^- (\d{4}-\d{2}-\d{2} \d{2}:\d{2}) · \[imp:(\d+)\] (.*)$")
        for fp in archivos:
            try:
                text = fp.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for raw in text.splitlines():
                m = line_re.match(raw)
                if not m:
                    continue
                ts_str, imp_str, hecho = m.group(1), m.group(2), m.group(3)
                if q and q not in _strip_accents(hecho):
                    continue
                matches.append((int(imp_str), ts_str, hecho))
            if len(matches) > limite * 4:
                break  # ya tenemos suficiente material

        # Orden: imp desc, ts desc
        matches.sort(key=lambda x: (-x[0], x[1]), reverse=False)
        matches.sort(key=lambda x: (-x[0], -_ts_to_key(x[1])))
        matches = matches[:limite]
        if not matches:
            log_call("claudio_contexto", a, args_log, True, {"hits": 0})
            return f"(sin memorias para {a} que matcheen {query!r})"

        lines = [f"🧠 **{a}** · memorias relevantes ({len(matches)}):"]
        for imp, ts_str, hecho in matches:
            lines.append(f"  • [{imp}] {ts_str} — {hecho}")
        log_call("claudio_contexto", a, args_log, True, {"hits": len(matches)})
        return "\n".join(lines)
    except Exception as e:
        log_call("claudio_contexto", autor or "?", args_log, False,
                 {"error": str(e)[:200]})
        return f"❌ {e}"


def _ts_to_key(ts_str: str) -> int:
    """'2026-05-14 15:32' → entero comparable (sin parsear datetime completo)."""
    try:
        s = ts_str.replace("-", "").replace(":", "").replace(" ", "")
        return int(s)
    except ValueError:
        return 0
