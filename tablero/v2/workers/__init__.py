"""tablero.v2.workers — Workers asyncio del cockpit.

Importar este módulo registra los workers vía `register_worker(...)`.
Lanzar con `await start_all_workers()` desde el startup de la app.
"""
from __future__ import annotations

import logging

from tablero.v2.ws import register_worker, Worker
from tablero.v2.workers.health import health_tick
from tablero.v2.workers.claude import claude_tick
from tablero.v2.workers.agentes import agentes_tick
from tablero.v2.workers.activity import start_activity_worker
from tablero.v2.workers.revenue import revenue_tick
from tablero.v2.workers.aegis import aegis_tick
from tablero.v2.workers.wake import wake_tick

log = logging.getLogger("tablero.v2.workers")


def register_all() -> None:
    """Registra workers de loop simple. Activity tiene loop especial (subprocess)."""
    register_worker(Worker(name="health", interval_s=2.0, tick=health_tick))
    register_worker(Worker(name="claude", interval_s=5.0, tick=claude_tick))
    register_worker(Worker(name="agentes", interval_s=5.0, tick=agentes_tick))
    register_worker(Worker(name="revenue", interval_s=30.0, tick=revenue_tick))
    register_worker(Worker(name="aegis", interval_s=60.0, tick=aegis_tick))
    register_worker(Worker(name="wake", interval_s=2.0, tick=wake_tick))
    log.info("workers registrados: health, claude, agentes, revenue, aegis, wake (+activity bg)")


__all__ = ["register_all", "start_activity_worker"]
