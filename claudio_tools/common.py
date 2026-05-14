"""Helpers compartidos por todos los tools de Claudio.

- VAULT path (configurable via env VAULT_PATH)
- Fechas: ts_iso, ts_human, today_iso, parse_date_natural
- Strings: slugify, normalize_author
- I/O: atomic_write, atomic_append, ensure_dir
- Frontmatter: parse_frontmatter, dump_frontmatter
- Logging estructurado: log_call (JSONL en claudio/logs/)
"""

from __future__ import annotations

import json
import os
import re
import tempfile
import unicodedata
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

# ── Vault paths ──────────────────────────────────────────────
VAULT = Path(os.getenv("VAULT_PATH", "/home/nosvers/public_html/knowledge_base"))


def vault() -> Path:
    """Devuelve la raíz del vault (re-lee env por si los tests la cambian)."""
    return Path(os.getenv("VAULT_PATH", str(VAULT)))


def claudio_dir() -> Path:
    return vault() / "claudio"


def logs_dir() -> Path:
    return claudio_dir() / "logs"


# ── Autores ──────────────────────────────────────────────────
AUTORES = {"angel", "africa", "compartido", "bris"}
AUTORES_HUMANOS = {"angel", "africa"}  # los que pueden ser sujeto financiero


def normalize_author(autor: str, *, allow_bris: bool = True) -> str:
    if not autor:
        raise ValueError("autor es obligatorio")
    a = autor.strip().lower()
    # Normalizar tilde de África
    a = a.replace("á", "a")
    if a not in AUTORES:
        raise ValueError(
            f"autor desconocido: {autor!r}. Permitidos: {sorted(AUTORES)}"
        )
    if a == "bris" and not allow_bris:
        raise ValueError("este tool no acepta 'bris' como autor")
    return a


# ── Fechas ───────────────────────────────────────────────────
def ts_iso() -> str:
    """Timestamp ISO con offset local."""
    return datetime.now().astimezone().isoformat(timespec="seconds")


def ts_human() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def today_iso() -> str:
    return date.today().isoformat()


def month_iso() -> str:
    return date.today().strftime("%Y-%m")


_DATE_RE = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")


def parse_date(s: str) -> date | None:
    """Parsea 'YYYY-MM-DD' o 'YYYY/MM/DD' o 'DD-MM-YYYY' o 'DD/MM/YYYY'."""
    if not s:
        return None
    s = s.strip()
    m = _DATE_RE.search(s)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            pass
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def parse_date_natural(text: str) -> tuple[date | None, str]:
    """Extrae una fecha del principio de `text`. Devuelve (fecha, resto).

    Acepta: 'hoy', 'mañana', 'pasado mañana', 'lunes', 'martes'... 'YYYY-MM-DD'.
    Si no encuentra fecha al inicio, devuelve (None, text).
    """
    if not text:
        return None, ""
    raw = text.strip()
    low = raw.lower()
    hoy = date.today()

    # Frases relativas
    PATRONES = [
        (r"^pasado\s+mañana\b", hoy + timedelta(days=2)),
        (r"^pasado\s+manana\b", hoy + timedelta(days=2)),
        (r"^mañana\b", hoy + timedelta(days=1)),
        (r"^manana\b", hoy + timedelta(days=1)),
        (r"^hoy\b", hoy),
    ]
    for pat, fecha in PATRONES:
        m = re.match(pat, low)
        if m:
            resto = raw[m.end():].strip()
            return fecha, resto

    # Día de la semana
    DIAS = ["lunes", "martes", "miércoles", "miercoles", "jueves",
            "viernes", "sábado", "sabado", "domingo"]
    DIAS_IDX = {"lunes": 0, "martes": 1, "miércoles": 2, "miercoles": 2,
                "jueves": 3, "viernes": 4, "sábado": 5, "sabado": 5, "domingo": 6}
    for d in DIAS:
        if low.startswith(d + " ") or low == d:
            target = DIAS_IDX[d]
            delta = (target - hoy.weekday()) % 7
            if delta == 0:
                delta = 7  # "lunes" dicho un lunes = el próximo
            fecha = hoy + timedelta(days=delta)
            resto = raw[len(d):].strip()
            return fecha, resto

    # ISO al principio
    m = re.match(r"^(\d{4}-\d{2}-\d{2})\b", raw)
    if m:
        f = parse_date(m.group(1))
        if f:
            return f, raw[m.end():].strip()

    # DD/MM o DD-MM (asume año actual)
    m = re.match(r"^(\d{1,2})[-/](\d{1,2})(?:[-/](\d{2,4}))?\b", raw)
    if m:
        d_, mo, y = m.group(1), m.group(2), m.group(3)
        year = int(y) if y else hoy.year
        if year < 100:
            year += 2000
        try:
            f = date(year, int(mo), int(d_))
            return f, raw[m.end():].strip()
        except ValueError:
            pass

    return None, raw


# ── Strings ──────────────────────────────────────────────────
def slugify(text: str, max_len: int = 60) -> str:
    if not text:
        return "sin-titulo"
    # Quita acentos
    t = unicodedata.normalize("NFKD", text)
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = t.lower()
    t = re.sub(r"[^a-z0-9]+", "-", t)
    t = t.strip("-")
    if not t:
        return "sin-titulo"
    return t[:max_len].rstrip("-")


# ── I/O ──────────────────────────────────────────────────────
def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def atomic_write(path: Path, content: str) -> None:
    """Escribe content en path de forma atómica (tempfile + os.replace)."""
    ensure_dir(path.parent)
    fd, tmp = tempfile.mkstemp(
        prefix=path.name + ".", suffix=".tmp", dir=str(path.parent)
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def atomic_append(path: Path, chunk: str) -> None:
    """Append simple con creación segura si el fichero no existe.

    No es estrictamente "atomic" como reemplazo, pero garantiza que la dir
    existe y que la escritura es síncrona en UTF-8.
    """
    ensure_dir(path.parent)
    with open(path, "a", encoding="utf-8") as f:
        f.write(chunk)


# ── Frontmatter ──────────────────────────────────────────────
def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Extrae frontmatter YAML simple ('---\\n...\\n---\\n').

    Si no hay frontmatter, devuelve ({}, text).
    Parser tolerante: claves `nombre: valor` por línea, listas inline `[a, b]`,
    valores `true|false|null|<int>|<float>|<str>`.
    """
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end < 0:
        return {}, text
    head = text[3:end].strip("\n")
    rest = text[end + 4:].lstrip("\n")
    meta: dict[str, Any] = {}
    for line in head.split("\n"):
        line = line.rstrip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        k, _, v = line.partition(":")
        k = k.strip()
        v = v.strip()
        meta[k] = _coerce(v)
    return meta, rest


def _coerce(v: str) -> Any:
    if v == "":
        return ""
    if v.lower() in ("true", "yes"):
        return True
    if v.lower() in ("false", "no"):
        return False
    if v.lower() == "null":
        return None
    # Lista inline
    if v.startswith("[") and v.endswith("]"):
        inner = v[1:-1].strip()
        if not inner:
            return []
        return [_coerce(x.strip().strip('"').strip("'")) for x in inner.split(",")]
    # Strings entrecomilladas
    if (v.startswith('"') and v.endswith('"')) or (
        v.startswith("'") and v.endswith("'")
    ):
        return v[1:-1]
    # Numérico
    try:
        if "." in v:
            return float(v)
        return int(v)
    except ValueError:
        pass
    return v


def dump_frontmatter(meta: dict, body: str) -> str:
    lines = ["---"]
    for k, v in meta.items():
        lines.append(f"{k}: {_yaml_val(v)}")
    lines.append("---\n")
    return "\n".join(lines) + body


def _yaml_val(v: Any) -> str:
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, list):
        return "[" + ", ".join(_yaml_val(x) for x in v) + "]"
    s = str(v)
    if ":" in s or s.startswith(("[", "{", "&", "*", "!", "|", ">")):
        return f"'{s}'"
    return s


# ── Logging estructurado ─────────────────────────────────────
_SENSITIVE_TOOLS = {
    "claudio_recordar",
    "claudio_contexto",
    "cita_medica_anotar",
    "medicacion_recordar",
}


def log_call(
    tool: str,
    autor: str,
    args: dict,
    ok: bool,
    extra: dict | None = None,
) -> None:
    """Escribe una línea JSONL en claudio/logs/YYYY-MM-DD.jsonl.

    Para tools sensibles (salud, memorias), solo se loguea metadata: el
    contenido nunca toca el log.
    """
    try:
        logs_dir().mkdir(parents=True, exist_ok=True)
        if tool in _SENSITIVE_TOOLS:
            args_logged = {
                k: (
                    f"<{len(str(v))} chars>"
                    if k in ("hecho", "contenido_texto", "notas", "query")
                    else v
                )
                for k, v in args.items()
            }
        else:
            args_logged = args
        line = {
            "ts": ts_iso(),
            "tool": tool,
            "autor": autor,
            "args": args_logged,
            "ok": ok,
        }
        if extra:
            line.update(extra)
        path = logs_dir() / f"{date.today().isoformat()}.jsonl"
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(line, ensure_ascii=False) + "\n")
    except Exception:
        # Logging NUNCA tira al tool
        pass
