"""Tools de salud — dominio sensible.

- medicacion_recordar()  → qué toca hoy
- cita_medica_anotar(quien, especialista, fecha, notas, autor)
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path

from .common import (
    atomic_write, dump_frontmatter, ensure_dir, log_call, normalize_author,
    parse_date, slugify, ts_iso, vault,
)


def _medicacion_path() -> Path:
    return vault() / "salud" / "medicacion.yaml"


def _citas_dir() -> Path:
    return vault() / "salud" / "citas"


def medicacion_recordar() -> str:
    """Devuelve qué medicación toca hoy, leyendo `salud/medicacion.yaml`.

    Calcula si toca hoy: `(hoy - desde).days % cada_n_dias == 0`.
    """
    args_log = {}
    try:
        path = _medicacion_path()
        if not path.exists():
            log_call("medicacion_recordar", "compartido",
                     args_log, True, {"hits": 0})
            return "(sin medicacion.yaml)"
        try:
            import yaml
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except Exception as e:
            return f"❌ YAML inválido: {e}"
        items = data.get("items") or []
        hoy = date.today()
        ahora = datetime.now()
        pendientes: list[tuple[str, str, str, str, str]] = []
        # (quien, medicamento, dosis, hora, estado)
        for it in items:
            if not it.get("activo", True):
                continue
            quien = str(it.get("quien", "?"))
            medic = str(it.get("medicamento", "?"))
            dosis = str(it.get("dosis", ""))
            horas = it.get("horas") or []
            if isinstance(horas, str):
                horas = [h.strip() for h in horas.split(",") if h.strip()]
            cada_n = max(1, int(it.get("cada_n_dias", 1)))
            desde = parse_date(str(it.get("desde", ""))) or hoy
            hasta = parse_date(str(it.get("hasta", "")))
            if hasta and hoy > hasta:
                continue
            delta_dias = (hoy - desde).days
            if delta_dias < 0:
                continue
            if delta_dias % cada_n != 0:
                continue
            for h in horas:
                try:
                    hh, mm = h.split(":")
                    target = ahora.replace(hour=int(hh), minute=int(mm),
                                           second=0, microsecond=0)
                    estado = "pendiente" if target >= ahora else "pasada"
                except Exception:
                    target = None
                    estado = "?"
                pendientes.append((quien, medic, dosis, h, estado))

        if not pendientes:
            log_call("medicacion_recordar", "compartido",
                     args_log, True, {"hits": 0})
            return "(no toca medicación hoy)"

        pendientes.sort(key=lambda x: (x[0], x[3]))
        lines = [f"💊 **Medicación hoy** ({len(pendientes)})"]
        for quien, medic, dosis, h, estado in pendientes:
            icon = "🟢" if estado == "pendiente" else "⚪"
            extra = f" · {dosis}" if dosis else ""
            lines.append(f"  {icon} {h} · {quien} · {medic}{extra} ({estado})")
        log_call("medicacion_recordar", "compartido",
                 args_log, True, {"hits": len(pendientes)})
        return "\n".join(lines)
    except Exception as e:
        log_call("medicacion_recordar", "compartido",
                 args_log, False, {"error": str(e)[:200]})
        return f"❌ {e}"


def cita_medica_anotar(
    quien: str,
    especialista: str,
    fecha: str,
    notas: str = "",
    autor: str = "",
) -> str:
    """Apunta una cita médica.

    Args:
        quien: angel | africa | bris.
        especialista: ej "veterinario", "ginecóloga", "fisio".
        fecha: 'YYYY-MM-DD' o con hora 'YYYY-MM-DD HH:MM'.
        notas: detalles libres.
        autor: quién apunta (angel | africa). OBLIGATORIO en salud.

    Se guarda en `salud/citas/<YYYY-MM-DD>-<quien>-<especialista>.md`.
    """
    args_log = {"quien": quien, "fecha": fecha, "len_notas": len(notas or "")}
    try:
        if not autor or not autor.strip():
            raise ValueError("autor es obligatorio en dominio salud")
        a = normalize_author(autor, allow_bris=False)
        q = normalize_author(quien, allow_bris=True)
        if not especialista or not especialista.strip():
            raise ValueError("especialista vacío")
        # Permitir 'YYYY-MM-DD HH:MM'
        hora_str = ""
        fecha_s = fecha.strip()
        if " " in fecha_s and len(fecha_s) > 10:
            head, _, tail = fecha_s.partition(" ")
            f = parse_date(head)
            hora_str = tail.strip()
        else:
            f = parse_date(fecha_s)
        if not f:
            raise ValueError(f"fecha inválida: {fecha!r}")

        slug = slugify(f"{f.isoformat()}-{q}-{especialista}")
        path = _citas_dir() / f"{slug}.md"
        ensure_dir(path.parent)
        i = 2
        while path.exists():
            path = _citas_dir() / f"{slug}-{i}.md"
            i += 1

        meta = {
            "quien": q,
            "especialista": especialista.strip(),
            "fecha": f.isoformat(),
            "hora": hora_str,
            "autor": a,
            "creado": ts_iso(),
        }
        body = (notas.strip() or "—") + "\n"
        atomic_write(path, dump_frontmatter(meta, body))
        log_call("cita_medica_anotar", a, args_log, True,
                 {"slug": path.stem})
        hora_extra = f" · {hora_str}" if hora_str else ""
        return (
            f"🏥 Apuntada cita: {f.isoformat()}{hora_extra} · {q} · {especialista.strip()}"
        )
    except Exception as e:
        log_call("cita_medica_anotar", autor or "?", args_log, False,
                 {"error": str(e)[:200]})
        return f"❌ {e}"
