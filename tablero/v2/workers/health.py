"""Worker health: poll psutil cada 2s + history últimos 30 valores de CPU."""
from __future__ import annotations

from tablero.v2.health import health_snapshot

_cpu_history: list[float] = []
_MAX_HISTORY = 30


async def health_tick() -> dict | None:
    snap = health_snapshot()
    if snap is None:
        return None
    _cpu_history.append(snap["cpu_pct"])
    if len(_cpu_history) > _MAX_HISTORY:
        del _cpu_history[: len(_cpu_history) - _MAX_HISTORY]
    snap["cpu_history"] = list(_cpu_history)
    return snap
