"""
tablero.v2.health — Endpoint síncrono /tablero/api/v2/health (psutil snapshot).

Si psutil no está disponible, retorna 503. El worker WS de health usa la misma
función `health_snapshot()`.
"""
from __future__ import annotations

import os
import time
import logging
from typing import Optional

from starlette.requests import Request
from starlette.responses import JSONResponse

log = logging.getLogger("tablero.v2.health")

try:
    import psutil  # type: ignore
    _PSUTIL_OK = True
    # warm-up para que el primer cpu_percent(interval=None) sea válido
    try:
        psutil.cpu_percent(interval=None)
    except Exception:
        pass
except ImportError:
    psutil = None  # type: ignore
    _PSUTIL_OK = False


# Para cálculo de delta de red (kbps)
_last_net: dict | None = None


def health_snapshot() -> Optional[dict]:
    """Snapshot psutil. Devuelve None si psutil no está disponible."""
    if not _PSUTIL_OK:
        return None
    global _last_net
    try:
        cpu = psutil.cpu_percent(interval=None)
        ram = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        net = psutil.net_io_counters()
        try:
            load = os.getloadavg()
        except (AttributeError, OSError):
            load = (0.0, 0.0, 0.0)
        now = time.time()
        net_in_kbps = 0.0
        net_out_kbps = 0.0
        if _last_net is not None:
            dt = max(now - _last_net["ts"], 0.001)
            net_in_kbps = (net.bytes_recv - _last_net["recv"]) / dt / 1024
            net_out_kbps = (net.bytes_sent - _last_net["sent"]) / dt / 1024
        _last_net = {"ts": now, "recv": net.bytes_recv, "sent": net.bytes_sent}
        try:
            uptime_s = int(now - psutil.boot_time())
        except Exception:
            uptime_s = 0
        return {
            "cpu_pct": round(cpu, 1),
            "ram_pct": round(ram.percent, 1),
            "ram_used_mb": int(ram.used // 1024 // 1024),
            "ram_total_mb": int(ram.total // 1024 // 1024),
            "disk_pct": round(disk.percent, 1),
            "disk_used_gb": round(disk.used / 1e9, 1),
            "disk_total_gb": round(disk.total / 1e9, 1),
            "load_1": round(load[0], 2),
            "load_5": round(load[1], 2),
            "load_15": round(load[2], 2),
            "net_in_kbps": round(max(net_in_kbps, 0), 1),
            "net_out_kbps": round(max(net_out_kbps, 0), 1),
            "uptime_s": uptime_s,
        }
    except Exception as e:
        log.exception(f"health_snapshot error: {e}")
        return None


_CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, OPTIONS",
    "Access-Control-Allow-Headers": "Authorization, Content-Type",
}


async def health_handler(request: Request) -> JSONResponse:
    snap = health_snapshot()
    if snap is None:
        return JSONResponse(
            {"error": "psutil_unavailable", "detalle": "module 'psutil' not installed"},
            status_code=503,
            headers=_CORS_HEADERS,
        )
    return JSONResponse(snap, status_code=200, headers=_CORS_HEADERS)
