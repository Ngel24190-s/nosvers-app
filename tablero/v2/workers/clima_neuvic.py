"""Worker clima_neuvic: open-meteo (gratis, sin API key) para Neuvic 24190."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, date, timedelta

import urllib.request
import urllib.error
import json

log = logging.getLogger("tablero.v2.workers.clima_neuvic")

# Neuvic, Dordogne
LAT = 45.0944
LON = 0.4711
URL = (
    f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}"
    "&current=temperature_2m,apparent_temperature,weather_code,wind_speed_10m,precipitation"
    "&daily=temperature_2m_min,temperature_2m_max,weather_code"
    "&forecast_days=3&timezone=Europe%2FParis"
)

WEATHER_LABELS = {
    0: "Ciel clair", 1: "Peu nuageux", 2: "Nuageux", 3: "Couvert",
    45: "Brouillard", 48: "Brouillard givrant",
    51: "Bruine légère", 53: "Bruine", 55: "Bruine forte",
    61: "Pluie faible", 63: "Pluie", 65: "Pluie forte",
    71: "Neige faible", 73: "Neige", 75: "Neige forte",
    80: "Averses faibles", 81: "Averses", 82: "Averses violentes",
    95: "Orage", 96: "Orage grêle léger", 99: "Orage grêle fort",
}


def _mock() -> dict:
    hoy = date.today()
    return {
        "ciudad": "Neuvic",
        "temperatura_c": 18.5,
        "sensacion_c": 17.0,
        "weather_code": 2,
        "weather_label": "Nuageux",
        "viento_kmh": 12.0,
        "precipitacion_mm": 0.0,
        "pronostico": [
            {"fecha": (hoy + timedelta(days=i)).isoformat(),
             "min": 11 + i, "max": 21 - i, "code": 2}
            for i in range(3)
        ],
        "ts": datetime.now().isoformat(timespec="seconds"),
        "mock": True,
    }


def _fetch_sync() -> dict | None:
    try:
        req = urllib.request.Request(URL, headers={"User-Agent": "nosvers/1.0"})
        with urllib.request.urlopen(req, timeout=5) as r:
            return json.loads(r.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as e:
        log.debug(f"open-meteo: {e}")
        return None


async def clima_neuvic_tick() -> dict | None:
    loop = asyncio.get_event_loop()
    raw = await loop.run_in_executor(None, _fetch_sync)
    if not raw:
        return _mock()
    cur = raw.get("current") or {}
    daily = raw.get("daily") or {}
    code = int(cur.get("weather_code", 0) or 0)
    pronostico = []
    times = daily.get("time", []) or []
    tmin = daily.get("temperature_2m_min", []) or []
    tmax = daily.get("temperature_2m_max", []) or []
    codes = daily.get("weather_code", []) or []
    for i, fecha in enumerate(times[:3]):
        try:
            pronostico.append({
                "fecha": fecha,
                "min": float(tmin[i]),
                "max": float(tmax[i]),
                "code": int(codes[i]),
            })
        except (IndexError, TypeError, ValueError):
            continue
    return {
        "ciudad": "Neuvic",
        "temperatura_c": float(cur.get("temperature_2m", 0) or 0),
        "sensacion_c": float(cur.get("apparent_temperature", 0) or 0),
        "weather_code": code,
        "weather_label": WEATHER_LABELS.get(code, "—"),
        "viento_kmh": float(cur.get("wind_speed_10m", 0) or 0),
        "precipitacion_mm": float(cur.get("precipitation", 0) or 0),
        "pronostico": pronostico,
        "ts": datetime.now().isoformat(timespec="seconds"),
    }
