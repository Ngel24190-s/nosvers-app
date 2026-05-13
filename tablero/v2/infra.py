"""tablero.v2.infra — GET /tablero/api/v2/infra/status (US10).

Agrega badges de estado de servicios externos:
  - vps (uptime + loadavg)
  - wp (HEAD a nosvers.com)
  - stripe (lee cache /var/cache/nosvers/stripe_daily.json si existe)
  - aegis (mtime de /home/nosvers/agents/aegis.last_briefing)
  - cron (touchfiles agt*.last_run vs EXPECTED_INTERVALS)
  - freqtrade (lee cache /var/cache/nosvers/freqtrade_pnl.json si existe)

Cachea 30s server-side. Cada fuente puede fallar individualmente; un
fallo aislado se reporta como warn/error en su badge sin afectar las demás.
"""
from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
from starlette.requests import Request
from starlette.responses import JSONResponse

from tablero.log import get_logger

log = get_logger("tablero.v2.infra")

# Configuración (D-009 / R-015)
EXPECTED_INTERVALS = {
    "agt05_africa": 6 * 3600,
    "agt07_diario": 24 * 3600,
    "agt_eisenia": 12 * 3600,
    "orchestrator": 3600,
}
AGENTS_DIR = Path("/home/nosvers/agents")
CACHE_DIR = Path("/var/cache/nosvers")
WP_URL = "https://nosvers.com"

# Cache server-side 30s para no martillear los servicios externos
_CACHE_TTL = 30.0
_cache: dict[str, Any] = {"timestamp": 0.0, "data": None}


def _badge_vps() -> dict[str, Any]:
    try:
        with open("/proc/uptime") as f:
            uptime_s = float(f.read().split()[0])
        with open("/proc/loadavg") as f:
            load1 = float(f.read().split()[0])
        days = int(uptime_s / 86400)
        return {
            "id": "vps",
            "status": "ok" if load1 < 4 else "warn",
            "value": f"uptime {days}d · load {load1:.2f}",
            "last_check": _now_iso(),
        }
    except Exception as e:  # noqa: BLE001
        return {"id": "vps", "status": "error", "detail": str(e), "last_check": _now_iso()}


def _badge_wp() -> dict[str, Any]:
    try:
        r = httpx.head(WP_URL, timeout=5.0, follow_redirects=True)
        ok = 200 <= r.status_code < 400
        return {
            "id": "wp",
            "status": "ok" if ok else "error",
            "value": f"HTTP {r.status_code}",
            "link": WP_URL,
            "last_check": _now_iso(),
        }
    except Exception as e:  # noqa: BLE001
        return {"id": "wp", "status": "error", "detail": str(e), "link": WP_URL, "last_check": _now_iso()}


def _badge_from_cache_json(badge_id: str, archivo: Path, formatter) -> dict[str, Any]:
    try:
        if not archivo.exists():
            return {"id": badge_id, "status": "warn", "detail": "sin datos", "last_check": _now_iso()}
        data = json.loads(archivo.read_text(encoding="utf-8"))
        return {**formatter(data), "id": badge_id, "last_check": _now_iso()}
    except Exception as e:  # noqa: BLE001
        return {"id": badge_id, "status": "error", "detail": str(e), "last_check": _now_iso()}


def _badge_stripe() -> dict[str, Any]:
    def fmt(d: dict[str, Any]) -> dict[str, Any]:
        revenue = d.get("revenue_eur", 0)
        return {"status": "ok", "value": f"€{revenue}"}
    return _badge_from_cache_json("stripe", CACHE_DIR / "stripe_daily.json", fmt)


def _badge_freqtrade() -> dict[str, Any]:
    def fmt(d: dict[str, Any]) -> dict[str, Any]:
        pnl = d.get("pnl_pct", 0.0)
        return {
            "status": "ok" if pnl >= 0 else ("warn" if pnl > -2 else "error"),
            "value": f"{pnl:+.2f}%",
        }
    return _badge_from_cache_json("freqtrade", CACHE_DIR / "freqtrade_pnl.json", fmt)


def _badge_aegis() -> dict[str, Any]:
    archivo = AGENTS_DIR / "aegis.last_briefing"
    try:
        if not archivo.exists():
            return {"id": "aegis", "status": "warn", "detail": "nunca corrió", "last_check": _now_iso()}
        mtime = archivo.stat().st_mtime
        edad_s = time.time() - mtime
        edad_h = edad_s / 3600
        status = "ok" if edad_h < 24 else ("warn" if edad_h < 48 else "error")
        return {
            "id": "aegis",
            "status": status,
            "value": f"hace {edad_h:.1f}h",
            "last_check": _now_iso(),
        }
    except Exception as e:  # noqa: BLE001
        return {"id": "aegis", "status": "error", "detail": str(e), "last_check": _now_iso()}


def _badge_cron() -> dict[str, Any]:
    crones = []
    overall = "ok"
    for slug, intervalo in EXPECTED_INTERVALS.items():
        archivo = AGENTS_DIR / f"{slug}.last_run"
        try:
            if not archivo.exists():
                crones.append({
                    "name": slug,
                    "status": "warn",
                    "detail": "nunca corrió",
                    "expected_interval_s": intervalo,
                })
                if overall == "ok":
                    overall = "warn"
                continue
            mtime = archivo.stat().st_mtime
            edad_s = time.time() - mtime
            status = "ok" if edad_s < intervalo * 1.5 else ("warn" if edad_s < intervalo * 3 else "error")
            crones.append({
                "name": slug,
                "status": status,
                "last_run": datetime.fromtimestamp(mtime, tz=timezone.utc).isoformat(timespec="seconds"),
                "expected_interval_s": intervalo,
            })
            if status == "error":
                overall = "error"
            elif status == "warn" and overall != "error":
                overall = "warn"
        except Exception as e:  # noqa: BLE001
            crones.append({"name": slug, "status": "error", "detail": str(e)})
    return {"id": "cron", "status": overall, "crones": crones, "last_check": _now_iso()}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _agregar() -> dict[str, Any]:
    badges = [
        _badge_vps(),
        _badge_wp(),
        _badge_stripe(),
        _badge_aegis(),
        _badge_cron(),
        _badge_freqtrade(),
    ]
    return {"ok": True, "generated_at": _now_iso(), "badges": badges}


async def infra_handler(request: Request, autenticador, cors_headers, log_line) -> JSONResponse:
    t0 = time.perf_counter()
    rid = request.headers.get("x-request-id") or "anon"
    payload = await autenticador(request)
    if not payload:
        log_line(rid, "", "v2/infra", 401, (time.perf_counter() - t0) * 1000)
        return JSONResponse({"ok": False, "error": "auth_invalido"}, status_code=401, headers=cors_headers())

    sub = str(payload.get("sub", ""))

    now = time.time()
    if _cache["data"] and (now - _cache["timestamp"]) < _CACHE_TTL:
        body = _cache["data"]
    else:
        body = _agregar()
        _cache["data"] = body
        _cache["timestamp"] = now

    log_line(rid, sub, "v2/infra", 200, (time.perf_counter() - t0) * 1000)
    return JSONResponse(body, headers=cors_headers())
