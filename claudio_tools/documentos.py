"""Tools de documentos (facturas, contratos, seguros, impuestos).

- documento_anotar(tipo, contenido_texto, fecha, fuente, autor)
- documentos_buscar(query, limite)
"""

from __future__ import annotations

import re
import unicodedata
from datetime import date
from pathlib import Path

from .common import (
    atomic_append, atomic_write, dump_frontmatter, ensure_dir, log_call,
    normalize_author, parse_date, parse_frontmatter, slugify, ts_iso, vault,
)

TIPOS = {"factura", "contrato", "seguro", "impuesto"}
TIPO_DIR = {
    "factura": "facturas",
    "contrato": "contratos",
    "seguro": "seguros",
    "impuesto": "impuestos",
}


def _docs_dir() -> Path:
    return vault() / "documentos"


def _strip(s: str) -> str:
    t = unicodedata.normalize("NFKD", s)
    return "".join(c for c in t if not unicodedata.combining(c)).lower()


def documento_anotar(
    tipo: str,
    contenido_texto: str,
    fecha: str,
    fuente: str,
    autor: str,
) -> str:
    """Guarda un documento en `documentos/<tipo_plural>/[YYYY/]<archivo>.md`.

    Args:
        tipo: factura | contrato | seguro | impuesto
        contenido_texto: cuerpo del documento (texto plano o transcripción).
        fecha: fecha del documento ('YYYY-MM-DD').
        fuente: emisor (ej "EDF", "AXA", "Trésor Public").
        autor: angel | africa.
    """
    args_log = {"tipo": tipo, "fecha": fecha, "fuente": fuente,
                "len_contenido": len(contenido_texto or "")}
    try:
        a = normalize_author(autor, allow_bris=False)
        t = (tipo or "").strip().lower()
        if t not in TIPOS:
            raise ValueError(f"tipo inválido: {tipo!r}. Permitidos: {sorted(TIPOS)}")
        f = parse_date(fecha)
        if not f:
            raise ValueError(f"fecha inválida: {fecha!r}")
        if not contenido_texto or not contenido_texto.strip():
            raise ValueError("contenido_texto vacío")
        if not fuente or not fuente.strip():
            raise ValueError("fuente vacía")

        slug = slugify(f"{f.isoformat()}-{fuente}", max_len=80)
        subdir = TIPO_DIR[t]
        # Facturas se subagrupan por año
        if t == "factura":
            target_dir = _docs_dir() / subdir / str(f.year)
        else:
            target_dir = _docs_dir() / subdir
        ensure_dir(target_dir)
        path = target_dir / f"{slug}.md"
        i = 2
        while path.exists():
            path = target_dir / f"{slug}-{i}.md"
            i += 1

        meta = {
            "tipo": t,
            "fecha": f.isoformat(),
            "fuente": fuente.strip(),
            "autor": a,
            "creado": ts_iso(),
        }
        atomic_write(path, dump_frontmatter(meta, contenido_texto.strip() + "\n"))

        # Actualizar INDEX
        rel = path.relative_to(_docs_dir())
        idx = _docs_dir() / "INDEX.md"
        if not idx.exists():
            ensure_dir(_docs_dir())
            atomic_append(idx, "# documentos · INDEX\n\n<!-- ENTRIES BELOW -->\n")
        # Insertar línea justo al principio de las entries (cronológico inverso)
        text = idx.read_text(encoding="utf-8", errors="replace")
        marker = "<!-- ENTRIES BELOW -->"
        entry = f"- {t} · {f.isoformat()} · {fuente.strip()} · {rel.as_posix()}\n"
        if marker in text:
            head, _, rest = text.partition(marker)
            new = head + marker + "\n" + entry + rest.lstrip("\n")
            atomic_write(idx, new)
        else:
            atomic_append(idx, entry)

        log_call("documento_anotar", a, args_log, True,
                 {"path": rel.as_posix()})
        return f"📄 Guardado: {t} · {f.isoformat()} · {fuente.strip()} → {rel.as_posix()}"
    except Exception as e:
        log_call("documento_anotar", autor or "?", args_log, False,
                 {"error": str(e)[:200]})
        return f"❌ {e}"


def documentos_buscar(query: str, limite: int = 20) -> str:
    """Grep recursivo sobre `documentos/` (case-insensitive, ignora diacríticos).

    Devuelve hasta `limite` matches con `tipo · fecha · fuente · ruta`.
    """
    args_log = {"len_query": len(query or ""), "limite": limite}
    try:
        q = _strip((query or "").strip())
        if not q:
            raise ValueError("query vacía")
        base = _docs_dir()
        if not base.exists():
            log_call("documentos_buscar", "compartido",
                     args_log, True, {"hits": 0})
            return "(sin documentos/)"
        matches: list[tuple[str, str, str, str]] = []  # (tipo, fecha, fuente, ruta)
        for fp in base.rglob("*.md"):
            if fp.name == "INDEX.md" or fp.name == "README.md":
                continue
            try:
                text = fp.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            meta, body = parse_frontmatter(text)
            haystack = _strip(
                " ".join([
                    str(meta.get("fuente", "")),
                    str(meta.get("tipo", "")),
                    body[:5000],
                ])
            )
            if q not in haystack:
                continue
            rel = fp.relative_to(base).as_posix()
            matches.append((
                str(meta.get("tipo", "?")),
                str(meta.get("fecha", "?")),
                str(meta.get("fuente", "?")),
                rel,
            ))
            if len(matches) >= limite * 2:
                break

        if not matches:
            log_call("documentos_buscar", "compartido",
                     args_log, True, {"hits": 0})
            return f"(sin matches para {query!r})"

        matches.sort(key=lambda x: x[1], reverse=True)
        matches = matches[:limite]
        lines = [f"🔎 **documentos · «{query}»** ({len(matches)})"]
        for t, fecha, fuente, rel in matches:
            lines.append(f"  • {t} · {fecha} · {fuente} · {rel}")
        log_call("documentos_buscar", "compartido",
                 args_log, True, {"hits": len(matches)})
        return "\n".join(lines)
    except Exception as e:
        log_call("documentos_buscar", "compartido",
                 args_log, False, {"error": str(e)[:200]})
        return f"❌ {e}"
