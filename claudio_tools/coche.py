"""Tools del coche: estado vivo + eventos (gasolina, mantenimiento, ITV).

- coche_estado()
- coche_evento(tipo, fecha, monto_eur, notas, autor)
"""

from __future__ import annotations

import re
from datetime import date, timedelta
from pathlib import Path

from .common import (
    atomic_append, atomic_write, dump_frontmatter, ensure_dir, log_call,
    month_iso, normalize_author, parse_date, parse_frontmatter, today_iso,
    ts_iso, vault,
)

EVENTO_TIPOS = {
    "gasolina", "mantenimiento", "itv", "seguro", "multa", "reparacion",
    "lavado", "neumaticos", "otros",
}


def _index_path() -> Path:
    return vault() / "coche" / "INDEX.md"


def _gastos_path() -> Path:
    return vault() / "coche" / "gastos" / f"{month_iso()}.md"


def coche_estado() -> str:
    """Lee coche/INDEX.md y devuelve un resumen humano."""
    args_log = {}
    try:
        path = _index_path()
        if not path.exists():
            log_call("coche_estado", "compartido",
                     args_log, True, {"existe": False})
            return "(sin coche/INDEX.md — crear con frontmatter)"
        text = path.read_text(encoding="utf-8", errors="replace")
        meta, _body = parse_frontmatter(text)
        if not meta:
            return "(coche/INDEX.md sin frontmatter — revisar formato)"

        mat = str(meta.get("matricula", "—")) or "—"
        modelo = str(meta.get("modelo", "—")) or "—"
        km = meta.get("kilometros", 0)
        itv_s = str(meta.get("itv_proxima", "")).strip()
        seg_s = str(meta.get("seguro_renovacion", "")).strip()
        mant_s = str(meta.get("ultimo_mantenimiento", "")).strip()
        hoy = date.today()

        def _delta_str(d_str: str) -> str:
            d = parse_date(d_str)
            if not d:
                return "—"
            delta = (d - hoy).days
            sufijo = "vencida" if delta < 0 else f"en {delta}d"
            return f"{d_str} ({sufijo})"

        lines = [
            "🚗 **Estado coche**",
            f"  • Matrícula: {mat}",
            f"  • Modelo: {modelo}",
            f"  • Kilómetros: {km}",
            f"  • ITV próxima: {_delta_str(itv_s) if itv_s else '—'}",
            f"  • Seguro renueva: {_delta_str(seg_s) if seg_s else '—'}",
            f"  • Último mantenimiento: {mant_s or '—'}",
        ]

        # Gastos del mes actual
        gp = _gastos_path()
        if gp.exists():
            total = 0.0
            n = 0
            for raw in gp.read_text(encoding="utf-8", errors="replace").splitlines():
                m = re.match(r"^- \S+ · ([\d.]+)€", raw.strip())
                if m:
                    try:
                        total += float(m.group(1))
                        n += 1
                    except ValueError:
                        pass
            if n:
                lines.append(f"  • Gastos mes {month_iso()}: {total:.2f}€ ({n} eventos)")
        log_call("coche_estado", "compartido",
                 args_log, True, {"existe": True})
        return "\n".join(lines)
    except Exception as e:
        log_call("coche_estado", "compartido",
                 args_log, False, {"error": str(e)[:200]})
        return f"❌ {e}"


def coche_evento(
    tipo: str,
    fecha: str,
    monto_eur: float = 0.0,
    notas: str = "",
    autor: str = "angel",
) -> str:
    """Registra un evento del coche y, si procede, actualiza INDEX.md.

    Args:
        tipo: gasolina | mantenimiento | itv | seguro | multa | reparacion |
              lavado | neumaticos | otros.
        fecha: 'YYYY-MM-DD' o 'hoy'.
        monto_eur: gasto en euros (0 si no aplica).
        notas: detalles libres.
        autor: angel | africa.
    """
    args_log = {"tipo": tipo, "fecha": fecha, "monto": monto_eur}
    try:
        a = normalize_author(autor, allow_bris=False)
        t = (tipo or "").strip().lower()
        if t not in EVENTO_TIPOS:
            raise ValueError(
                f"tipo inválido: {tipo!r}. Permitidos: {sorted(EVENTO_TIPOS)}"
            )
        f = parse_date(fecha) or (date.today() if fecha.lower() == "hoy" else None)
        if not f:
            raise ValueError(f"fecha inválida: {fecha!r}")
        try:
            monto = float(monto_eur or 0.0)
        except (TypeError, ValueError):
            monto = 0.0

        # Append en gastos del mes
        gp = _gastos_path()
        if not gp.exists():
            ensure_dir(gp.parent)
            atomic_append(gp, f"# Coche · gastos {month_iso()}\n\n")
        notas_clean = notas.strip().replace("\n", " ")[:200]
        atomic_append(
            gp,
            f"- {f.isoformat()} · {monto:.2f}€ · {t} · {a} · {notas_clean}\n",
        )

        # Actualizar INDEX si es mantenimiento/ITV/seguro
        idx = _index_path()
        if idx.exists():
            text = idx.read_text(encoding="utf-8", errors="replace")
            meta, body = parse_frontmatter(text)
            changed = False
            if t == "mantenimiento":
                meta["ultimo_mantenimiento"] = f.isoformat()
                changed = True
            elif t == "itv":
                # ITV vale 2 años para vehículos de turismo. Aproximación: +2 años.
                try:
                    proxima = f.replace(year=f.year + 2)
                except ValueError:
                    proxima = f + timedelta(days=730)
                meta["itv_proxima"] = proxima.isoformat()
                changed = True
            elif t == "seguro":
                try:
                    proxima = f.replace(year=f.year + 1)
                except ValueError:
                    proxima = f + timedelta(days=365)
                meta["seguro_renovacion"] = proxima.isoformat()
                changed = True
            if changed:
                meta["ultima_actualizacion"] = today_iso()
                atomic_write(idx, dump_frontmatter(meta, body))

        log_call("coche_evento", a, args_log, True, {"monto": round(monto, 2)})
        extra = f" · {monto:.2f}€" if monto > 0 else ""
        return f"🚗 Anotado: {t} · {f.isoformat()}{extra} ({a})"
    except Exception as e:
        log_call("coche_evento", autor or "?", args_log, False,
                 {"error": str(e)[:200]})
        return f"❌ {e}"
