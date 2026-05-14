"""Worker medicación: lee salud/medicacion.yaml + salud/citas/* para próximas tomas."""
from __future__ import annotations

from datetime import date, datetime, time, timedelta
from pathlib import Path

from claudio_tools.common import vault


def _yaml_file() -> Path:
    return vault() / "salud" / "medicacion.yaml"


def _citas_dir() -> Path:
    return vault() / "salud" / "citas"


def _parse_hora(s: str) -> time | None:
    try:
        h, m = s.split(":", 1)
        return time(int(h), int(m))
    except Exception:
        return None


def _next_toma(items: list[dict], now: datetime) -> dict | None:
    """Devuelve la próxima toma (mínimo positivo) entre todos los items activos."""
    best: tuple[int, dict] | None = None
    hoy_d = now.date()
    for it in items:
        if not it.get("activo", True):
            continue
        cada_n = int(it.get("cada_n_dias", 1) or 1)
        desde_s = str(it.get("desde", ""))
        try:
            desde = date.fromisoformat(desde_s) if desde_s else hoy_d
        except ValueError:
            desde = hoy_d
        delta_dias = (hoy_d - desde).days
        if cada_n > 1 and delta_dias % cada_n != 0:
            continue
        horas = it.get("horas") or []
        for hraw in horas:
            t = _parse_hora(str(hraw))
            if not t:
                continue
            target = datetime.combine(hoy_d, t)
            if target < now:
                # próxima: mañana misma hora (si toca por ciclo)
                next_day = hoy_d + timedelta(days=1)
                delta_next = (next_day - desde).days
                if cada_n > 1 and delta_next % cada_n != 0:
                    continue
                target = datetime.combine(next_day, t)
            mins = int((target - now).total_seconds() // 60)
            if mins < 0:
                continue
            entry = {
                "quien": str(it.get("quien", "")),
                "medicamento": str(it.get("medicamento", "")),
                "dosis": str(it.get("dosis", "")),
                "hora": t.strftime("%H:%M"),
                "minutos_hasta": mins,
            }
            if best is None or mins < best[0]:
                best = (mins, entry)
    return best[1] if best else None


async def medicacion_tick() -> dict | None:
    path = _yaml_file()
    if not path.exists():
        return {"empty": True}
    try:
        import yaml
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {"empty": True}
    items = data.get("items") or []
    if not items:
        return {"empty": True}
    now = datetime.now()
    proxima = _next_toma(items, now)
    # Citas próximas
    citas: list[dict] = []
    try:
        cdir = _citas_dir()
        if cdir.exists():
            for f in sorted(cdir.glob("*.md")):
                # Nombre típico: YYYY-MM-DD-<quien>-<especialista>.md
                stem = f.stem
                partes = stem.split("-")
                if len(partes) >= 5:
                    fecha_s = "-".join(partes[:3])
                    try:
                        if date.fromisoformat(fecha_s) >= now.date():
                            citas.append({
                                "fecha": fecha_s,
                                "quien": partes[3],
                                "especialista": "-".join(partes[4:]),
                            })
                    except ValueError:
                        pass
    except Exception:
        pass
    return {
        "proxima": proxima,
        "n_items_activos": sum(1 for it in items if it.get("activo", True)),
        "proximas_citas": citas[:5],
    }
