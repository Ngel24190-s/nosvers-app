"""Tools de finanzas: gastos, resúmenes, cargos recurrentes.

- gasto_anotar(monto_eur, concepto, categoria, autor)
- gastos_resumen(periodo, categoria)
- recurrente_alertar(dias)
"""

from __future__ import annotations

import calendar
import re
from datetime import date, datetime, timedelta
from pathlib import Path

from .common import (
    atomic_append, ensure_dir, log_call, normalize_author, month_iso,
    today_iso, ts_human, vault,
)

CATEGORIAS = {
    "alimentacion", "transporte", "coche", "hogar", "ocio", "salud",
    "nosvers", "ropa", "regalos", "viajes", "otros",
}


def _gastos_file(yyyy_mm: str) -> Path:
    return vault() / "finanzas" / "gastos" / f"{yyyy_mm}.md"


def gasto_anotar(
    monto_eur: float,
    concepto: str,
    categoria: str,
    autor: str,
) -> str:
    """Apunta un gasto en finanzas/gastos/YYYY-MM.md.

    Args:
        monto_eur: float en euros.
        concepto: descripción corta (ej "gasolina coche").
        categoria: alimentacion | transporte | coche | hogar | ocio | salud |
                   nosvers | ropa | regalos | viajes | otros.
        autor: angel | africa (sin default — informa quién hizo el gasto).
    """
    args_log = {"monto": monto_eur, "categoria": categoria,
                "len_concepto": len(concepto or "")}
    try:
        a = normalize_author(autor, allow_bris=False)
        try:
            monto = float(monto_eur)
        except (TypeError, ValueError):
            raise ValueError(f"monto inválido: {monto_eur!r}")
        if monto <= 0:
            raise ValueError("monto debe ser > 0")
        if not concepto or not concepto.strip():
            raise ValueError("concepto vacío")
        cat = (categoria or "otros").strip().lower()
        if cat not in CATEGORIAS:
            cat = "otros"
        path = _gastos_file(month_iso())
        if not path.exists():
            ensure_dir(path.parent)
            atomic_append(path, f"# Gastos · {month_iso()}\n\n")
        line = f"- {ts_human()} · {monto:.2f}€ · {concepto.strip()} · {cat} · {a}\n"
        atomic_append(path, line)

        # Cálculo rápido del total del mes para feedback
        total = _total_mes(month_iso())
        log_call("gasto_anotar", a, args_log, True, {"total_mes": round(total, 2)})
        return (
            f"💸 Apuntado: {monto:.2f}€ · {concepto.strip()} ({cat}). "
            f"Mes {month_iso()}: {total:.2f}€."
        )
    except Exception as e:
        log_call("gasto_anotar", autor or "?", args_log, False,
                 {"error": str(e)[:200]})
        return f"❌ {e}"


_LINE_RE = re.compile(
    r"^- (\d{4}-\d{2}-\d{2}) \d{2}:\d{2} · ([\d.]+)€ · (.+?) · (\w+) · (\w+)\s*$"
)


def _total_mes(yyyy_mm: str) -> float:
    path = _gastos_file(yyyy_mm)
    if not path.exists():
        return 0.0
    tot = 0.0
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        m = _LINE_RE.match(line.strip())
        if m:
            try:
                tot += float(m.group(2))
            except ValueError:
                pass
    return tot


def gastos_resumen(periodo: str = "mes_actual", categoria: str = "") -> str:
    """Agrega gastos del periodo, por categoría.

    Args:
        periodo: 'mes_actual' | 'mes_anterior' | 'YYYY-MM' | 'ultimos_30_dias'
        categoria: vacío = todas, o una de CATEGORIAS para filtrar.
    """
    args_log = {"periodo": periodo, "categoria": categoria}
    try:
        hoy = date.today()
        meses_objetivo: list[str] = []
        fecha_min: date | None = None
        if periodo == "mes_actual":
            meses_objetivo = [hoy.strftime("%Y-%m")]
        elif periodo == "mes_anterior":
            primer = hoy.replace(day=1) - timedelta(days=1)
            meses_objetivo = [primer.strftime("%Y-%m")]
        elif re.match(r"^\d{4}-\d{2}$", periodo):
            meses_objetivo = [periodo]
        elif periodo == "ultimos_30_dias":
            fecha_min = hoy - timedelta(days=30)
            meses_objetivo = [
                hoy.strftime("%Y-%m"),
                (hoy.replace(day=1) - timedelta(days=1)).strftime("%Y-%m"),
            ]
        else:
            raise ValueError(f"periodo inválido: {periodo!r}")

        cat_filter = (categoria or "").strip().lower()
        if cat_filter and cat_filter not in CATEGORIAS:
            raise ValueError(f"categoria inválida: {categoria!r}")

        agregados: dict[str, float] = {}
        por_autor: dict[str, float] = {"angel": 0.0, "africa": 0.0}
        total = 0.0
        n_lineas = 0

        for ym in meses_objetivo:
            path = _gastos_file(ym)
            if not path.exists():
                continue
            for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
                m = _LINE_RE.match(raw.strip())
                if not m:
                    continue
                fecha_s, monto_s, _conc, cat, au = m.groups()
                if fecha_min:
                    try:
                        f = date.fromisoformat(fecha_s)
                        if f < fecha_min:
                            continue
                    except ValueError:
                        continue
                if cat_filter and cat != cat_filter:
                    continue
                try:
                    monto = float(monto_s)
                except ValueError:
                    continue
                agregados[cat] = agregados.get(cat, 0.0) + monto
                if au in por_autor:
                    por_autor[au] += monto
                total += monto
                n_lineas += 1

        if n_lineas == 0:
            log_call("gastos_resumen", "compartido", args_log, True,
                     {"total": 0})
            extra = f" ({cat_filter})" if cat_filter else ""
            return f"(sin gastos en {periodo}{extra})"

        lines = [
            f"💸 **Resumen · {periodo}**{' · '+cat_filter if cat_filter else ''}",
            f"  Total: **{total:.2f}€** ({n_lineas} apuntes)",
        ]
        if not cat_filter:
            lines.append("\n  *Por categoría:*")
            for cat, m in sorted(agregados.items(), key=lambda x: -x[1]):
                pct = (m / total) * 100 if total else 0
                lines.append(f"  • {cat}: {m:.2f}€ ({pct:.0f}%)")
        lines.append("\n  *Por autor:*")
        for au, m in por_autor.items():
            if m > 0:
                lines.append(f"  • {au}: {m:.2f}€")
        log_call("gastos_resumen", "compartido", args_log, True,
                 {"total": round(total, 2)})
        return "\n".join(lines)
    except Exception as e:
        log_call("gastos_resumen", "?", args_log, False, {"error": str(e)[:200]})
        return f"❌ {e}"


def recurrente_alertar(dias: int = 7) -> str:
    """Lee `finanzas/recurrentes.yaml` y devuelve cargos próximos en `dias`.

    Asume schema:
      items:
        - nombre, monto_eur, dia_mes, cada_n_meses (def 1), categoria,
          autor, desde (opt), activo (def true)
    """
    args_log = {"dias": dias}
    try:
        path = vault() / "finanzas" / "recurrentes.yaml"
        if not path.exists():
            log_call("recurrente_alertar", "compartido",
                     args_log, True, {"hits": 0})
            return "(sin recurrentes.yaml)"

        try:
            import yaml  # noqa
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except Exception as e:
            return f"❌ YAML inválido: {e}"

        items = data.get("items") or []
        if not items:
            log_call("recurrente_alertar", "compartido",
                     args_log, True, {"hits": 0})
            return "(sin recurrentes definidos)"

        hoy = date.today()
        limite = hoy + timedelta(days=max(1, int(dias)))
        alertas: list[tuple[date, str, float, str]] = []
        for it in items:
            if not it.get("activo", True):
                continue
            nombre = str(it.get("nombre", "?"))
            try:
                monto = float(it.get("monto_eur", 0.0))
            except (TypeError, ValueError):
                continue
            dia_mes = int(it.get("dia_mes", 1))
            cada_n = max(1, int(it.get("cada_n_meses", 1)))
            categoria = str(it.get("categoria", "otros"))
            desde_s = str(it.get("desde", ""))
            desde = None
            try:
                if desde_s:
                    desde = date.fromisoformat(desde_s)
            except ValueError:
                desde = None

            # Próximas ocurrencias hasta el límite
            anchor = desde or hoy.replace(day=1)
            cursor_anio, cursor_mes = anchor.year, anchor.month
            # Avanzar el cursor hasta justo antes de hoy
            while True:
                # Día efectivo (clamp si febrero, etc.)
                last = calendar.monthrange(cursor_anio, cursor_mes)[1]
                dia_ef = min(dia_mes, last)
                cand = date(cursor_anio, cursor_mes, dia_ef)
                if cand >= hoy:
                    break
                cursor_mes += cada_n
                while cursor_mes > 12:
                    cursor_mes -= 12
                    cursor_anio += 1
            # Iterar próximas hasta `limite`
            while True:
                last = calendar.monthrange(cursor_anio, cursor_mes)[1]
                dia_ef = min(dia_mes, last)
                cand = date(cursor_anio, cursor_mes, dia_ef)
                if cand > limite:
                    break
                alertas.append((cand, nombre, monto, categoria))
                cursor_mes += cada_n
                while cursor_mes > 12:
                    cursor_mes -= 12
                    cursor_anio += 1

        if not alertas:
            log_call("recurrente_alertar", "compartido",
                     args_log, True, {"hits": 0})
            return f"(sin cargos recurrentes en los próximos {dias} días)"

        alertas.sort(key=lambda x: x[0])
        lines = [f"📅 **Cargos próximos · {dias}d** ({len(alertas)})"]
        for f, nombre, monto, cat in alertas:
            dias_falta = (f - hoy).days
            lines.append(
                f"  • {f.isoformat()} ({dias_falta}d) · {monto:.2f}€ · {nombre} ({cat})"
            )
        total = sum(a[2] for a in alertas)
        lines.append(f"\n  Total previsto: **{total:.2f}€**")
        log_call("recurrente_alertar", "compartido",
                 args_log, True, {"hits": len(alertas), "total": round(total, 2)})
        return "\n".join(lines)
    except Exception as e:
        log_call("recurrente_alertar", "compartido", args_log, False,
                 {"error": str(e)[:200]})
        return f"❌ {e}"
