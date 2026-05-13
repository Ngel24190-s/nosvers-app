"""Motor de automatizaciones.

Arranca:
- cron_loop: tick cada 30s, comprueba qué automatizaciones cron deben dispararse.
- listeners en canales WS: nota_capturada → activity, agente_terminado → agentes, etc.
- en cada disparo: ejecuta cadena, publica eventos por canal `automation`, escribe log.

Suscriptor del broker via `broker.add_internal_listener(channel, cb)`.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import time
from datetime import datetime, timezone
from typing import Any

from tablero.v2.automatizaciones import storage
from tablero.v2.automatizaciones.logs import append_log
from tablero.v2.automatizaciones.models import Automation
from tablero.v2.automatizaciones.runner import run_chain
from tablero.v2.automatizaciones.triggers import (
    cron_should_fire,
    matches_aegis_alerta,
    matches_agente_terminado,
    matches_nota_capturada,
    matches_voz_keyword,
    matches_vps_threshold,
)

log = logging.getLogger("tablero.v2.automatizaciones.motor")


class Motor:
    """Estado del motor en memoria. Singleton via `motor` abajo."""

    def __init__(self) -> None:
        self.automations: list[Automation] = []
        self.errores: dict[str, str] = {}
        self._last_run_summary: dict[str, dict[str, Any]] = {}  # automation_id -> {ts, status}
        self._recent_executions: list[dict] = []  # últimas 10 ejecuciones (resúmenes)
        self._dedup: dict[tuple[str, str], float] = {}
        self._dedup_ttl_s = 5.0
        self._cron_last_fire: dict[str, float] = {}
        self._broker = None  # se asigna en start()
        self._running = False
        self._tasks: list[asyncio.Task] = []
        self._lock = asyncio.Lock()

    # ── Lifecycle ─────────────────────────────────────────────────────────

    def reload(self) -> dict[str, Any]:
        items, errors = storage.load_all()
        self.automations = items
        self.errores = errors
        log.info(f"motor reload: {len(items)} automatizaciones, {len(errors)} errores")
        return {"loaded": len(items), "errors": list(errors.keys())}

    async def start(self, broker) -> None:
        if self._running:
            return
        self._broker = broker
        self.reload()
        # Registrar listeners en canales WS
        broker.add_internal_listener("activity", self._on_activity)
        broker.add_internal_listener("agentes", self._on_agentes)
        broker.add_internal_listener("aegis", self._on_aegis)
        broker.add_internal_listener("health", self._on_health)
        # Lanzar loop de cron
        self._tasks.append(asyncio.create_task(self._cron_loop()))
        self._running = True
        log.info("motor automation arrancado")

    async def stop(self) -> None:
        for t in self._tasks:
            t.cancel()
        self._tasks = []
        self._running = False

    # ── Public API ────────────────────────────────────────────────────────

    async def run_one(
        self,
        automation_id: str,
        trigger_payload: dict | None = None,
        dry_run: bool = False,
        autor_trigger: str | None = None,
    ) -> dict:
        """Lanza una automatización manualmente."""
        a = next((x for x in self.automations if x.id == automation_id), None)
        if a is None:
            # intentar cargar fresh por si fue recién creada
            self.reload()
            a = next((x for x in self.automations if x.id == automation_id), None)
            if a is None:
                return {"ok": False, "error": "not_found"}
        return await self._exec(a, trigger_payload or {"manual": True}, dry_run, autor_trigger=autor_trigger or "manual")

    def get_last_run(self, automation_id: str) -> dict | None:
        return self._last_run_summary.get(automation_id)

    def get_recent_executions(self, n: int = 10) -> list[dict]:
        return self._recent_executions[-n:]

    # ── Internals ─────────────────────────────────────────────────────────

    async def _exec(self, automation: Automation, trigger_payload: dict, dry_run: bool, autor_trigger: str = "system") -> dict:
        # Idempotencia
        key = (automation.id, hashlib.sha1(json.dumps(trigger_payload, sort_keys=True, default=str).encode()).hexdigest())
        now = time.time()
        self._gc_dedup(now)
        if not dry_run and key in self._dedup:
            log.debug(f"dedup skip {automation.id}")
            return {"ok": False, "skipped": "dedup"}
        if not dry_run:
            self._dedup[key] = now

        async def broadcast(evt: dict) -> None:
            if self._broker is not None:
                await self._broker.broadcast("automation", evt)

        entry = await run_chain(automation, trigger_payload, dry_run=dry_run, broadcast=broadcast, autor_trigger=autor_trigger)

        if not dry_run:
            try:
                await append_log(entry)
            except Exception as e:  # noqa: BLE001
                log.warning(f"append_log falló: {e}")
            self._last_run_summary[automation.id] = {
                "ts": entry["ended_at"],
                "status": entry["status"],
                "duration_ms": entry["duration_ms"],
            }
            self._recent_executions.append({
                "execution_id": entry["execution_id"],
                "automation_id": automation.id,
                "automation_nombre": automation.nombre,
                "ts": entry["ended_at"],
                "status": entry["status"],
                "duration_ms": entry["duration_ms"],
            })
            if len(self._recent_executions) > 50:
                self._recent_executions = self._recent_executions[-50:]
        return entry

    def _gc_dedup(self, now: float) -> None:
        if not self._dedup:
            return
        cutoff = now - self._dedup_ttl_s
        self._dedup = {k: v for k, v in self._dedup.items() if v >= cutoff}

    async def _cron_loop(self) -> None:
        log.info("cron loop iniciado")
        while True:
            try:
                await asyncio.sleep(30)
                now = datetime.now(timezone.utc)
                for a in self.automations:
                    if not a.activo or a.trigger.tipo != "cron":
                        continue
                    rrule = a.trigger.rrule  # type: ignore[attr-defined]
                    # Evitar disparar dos veces en la misma ventana de 60s
                    last = self._cron_last_fire.get(a.id, 0)
                    if now.timestamp() - last < 50:
                        continue
                    if cron_should_fire(rrule, now):
                        self._cron_last_fire[a.id] = now.timestamp()
                        asyncio.create_task(self._exec(a, {"cron_at": now.isoformat(), "rrule": rrule}, dry_run=False, autor_trigger="cron"))
            except asyncio.CancelledError:
                raise
            except Exception as e:  # noqa: BLE001
                log.exception(f"cron loop error: {e}")
                await asyncio.sleep(5)

    async def _on_activity(self, payload: dict) -> None:
        items = payload.get("items") if isinstance(payload, dict) else None
        if not items:
            return
        for ev in items if isinstance(items, list) else [items]:
            for a in self.automations:
                if not a.activo:
                    continue
                if a.trigger.tipo == "nota_capturada":
                    ok, norm = matches_nota_capturada(getattr(a.trigger, "filtros", {}) or {}, ev)
                    if ok:
                        asyncio.create_task(self._exec(a, norm, dry_run=False, autor_trigger="nota_capturada"))
                elif a.trigger.tipo == "voz_keyword":
                    ok, norm = matches_voz_keyword(getattr(a.trigger, "keywords", []) or [], ev)
                    if ok:
                        asyncio.create_task(self._exec(a, norm, dry_run=False, autor_trigger="voz_keyword"))

    async def _on_agentes(self, payload: dict) -> None:
        for a in self.automations:
            if not a.activo or a.trigger.tipo != "agente_terminado":
                continue
            ok, norm = matches_agente_terminado(getattr(a.trigger, "filtros", {}) or {}, payload)
            if ok:
                asyncio.create_task(self._exec(a, norm, dry_run=False, autor_trigger="agente_terminado"))

    async def _on_aegis(self, payload: dict) -> None:
        for a in self.automations:
            if not a.activo or a.trigger.tipo != "aegis_alerta":
                continue
            ok, norm = matches_aegis_alerta(getattr(a.trigger, "filtros", {}) or {}, payload)
            if ok:
                asyncio.create_task(self._exec(a, norm, dry_run=False, autor_trigger="aegis_alerta"))

    async def _on_health(self, payload: dict) -> None:
        for a in self.automations:
            if not a.activo or a.trigger.tipo != "vps_threshold":
                continue
            ok, norm = matches_vps_threshold(
                getattr(a.trigger, "metrica"),
                getattr(a.trigger, "umbral_pct"),
                getattr(a.trigger, "comparador"),
                payload,
            )
            if ok:
                asyncio.create_task(self._exec(a, norm, dry_run=False, autor_trigger="vps_threshold"))

    async def fire_webhook_stripe(self, payload: dict) -> dict:
        """Llamado por el endpoint REST cuando llega un webhook Stripe."""
        from tablero.v2.automatizaciones.triggers import matches_webhook_stripe
        fired = 0
        for a in self.automations:
            if not a.activo or a.trigger.tipo != "webhook_stripe":
                continue
            evento = getattr(a.trigger, "evento", "payment_intent.succeeded")
            filtros = getattr(a.trigger, "filtros", {}) or {}
            ok, norm = matches_webhook_stripe(evento, filtros, payload)
            if ok:
                asyncio.create_task(self._exec(a, norm, dry_run=False, autor_trigger="webhook_stripe"))
                fired += 1
        return {"fired": fired}


# Singleton
motor = Motor()
