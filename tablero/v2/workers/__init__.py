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
# 007: contexto trabajo (DI Environnement)
from tablero.v2.workers.trabajo import trabajo_tick
# 009: widgets ricos — NosVers
from tablero.v2.workers.huerto_estado import huerto_estado_tick
from tablero.v2.workers.pedidos_stripe import pedidos_stripe_tick
from tablero.v2.workers.aappma_stock import aappma_stock_tick
from tablero.v2.workers.clima_neuvic import clima_neuvic_tick
# 009: widgets ricos — Trabajo
from tablero.v2.workers.chantiers_activos import chantiers_activos_tick
from tablero.v2.workers.chantiers_agenda import chantiers_agenda_tick
from tablero.v2.workers.equipe_status import equipe_tick
from tablero.v2.workers.documentos_trabajo import documentos_trabajo_tick

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
    # 007 — contexto trabajo
    register_worker(Worker(name="trabajo", interval_s=60.0, tick=trabajo_tick))
    # 009 — widgets ricos NosVers
    register_worker(Worker(name="huerto_estado", interval_s=300.0,
                           tick=huerto_estado_tick))
    register_worker(Worker(name="pedidos_stripe", interval_s=120.0,
                           tick=pedidos_stripe_tick))
    register_worker(Worker(name="aappma_stock", interval_s=600.0,
                           tick=aappma_stock_tick))
    register_worker(Worker(name="clima_neuvic", interval_s=1800.0,
                           tick=clima_neuvic_tick))
    # 009 — widgets ricos Trabajo
    register_worker(Worker(name="chantiers_activos", interval_s=60.0,
                           tick=chantiers_activos_tick))
    register_worker(Worker(name="chantiers_agenda", interval_s=60.0,
                           tick=chantiers_agenda_tick))
    register_worker(Worker(name="equipe", interval_s=60.0, tick=equipe_tick))
    register_worker(Worker(name="documentos_trabajo", interval_s=300.0,
                           tick=documentos_trabajo_tick))
    log.info(
        "workers registrados: health, claude, agentes, revenue, aegis, wake, "
        "recordatorios, gastos, compras, medicacion, coche, menu_dia, bris, "
        "trabajo, huerto_estado, pedidos_stripe, aappma_stock, clima_neuvic, "
        "chantiers_activos, chantiers_agenda, equipe, documentos_trabajo "
        "(+activity bg)"
    )


__all__ = ["register_all", "start_activity_worker"]
