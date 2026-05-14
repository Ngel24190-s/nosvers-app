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
# 006: familia/admin
from tablero.v2.workers.recordatorios import recordatorios_tick
from tablero.v2.workers.gastos import gastos_tick
from tablero.v2.workers.compras import compras_tick
from tablero.v2.workers.medicacion import medicacion_tick
from tablero.v2.workers.coche import coche_tick
from tablero.v2.workers.menu_dia import menu_dia_tick
from tablero.v2.workers.bris import bris_tick

log = logging.getLogger("tablero.v2.workers")


def register_all() -> None:
    """Registra workers de loop simple. Activity tiene loop especial (subprocess)."""
    register_worker(Worker(name="health", interval_s=2.0, tick=health_tick))
    register_worker(Worker(name="claude", interval_s=5.0, tick=claude_tick))
    register_worker(Worker(name="agentes", interval_s=5.0, tick=agentes_tick))
    register_worker(Worker(name="revenue", interval_s=30.0, tick=revenue_tick))
    register_worker(Worker(name="aegis", interval_s=60.0, tick=aegis_tick))
    register_worker(Worker(name="wake", interval_s=2.0, tick=wake_tick))
    # 006 — familia/admin
    register_worker(Worker(name="recordatorios", interval_s=30.0,
                           tick=recordatorios_tick))
    register_worker(Worker(name="gastos", interval_s=60.0, tick=gastos_tick))
    register_worker(Worker(name="compras", interval_s=30.0, tick=compras_tick))
    register_worker(Worker(name="medicacion", interval_s=60.0,
                           tick=medicacion_tick))
    register_worker(Worker(name="coche", interval_s=300.0, tick=coche_tick))
    register_worker(Worker(name="menu_dia", interval_s=600.0,
                           tick=menu_dia_tick))
    register_worker(Worker(name="bris", interval_s=300.0, tick=bris_tick))
    log.info(
        "workers registrados: health, claude, agentes, revenue, aegis, wake, "
        "recordatorios, gastos, compras, medicacion, coche, menu_dia, bris "
        "(+activity bg)"
    )


__all__ = ["register_all", "start_activity_worker"]
