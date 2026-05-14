"""
tablero.v2.ws — WebSocket layer del cockpit (Fase D).

Broker en memoria + JWT por query param + workers asyncio + lifecycle.

Canales soportados: health, claude, activity, agentes, revenue, aegis, wake.

Cliente:
    {"type":"subscribe","channel":"health"}
    {"type":"unsubscribe","channel":"health"}
    {"type":"ping"}

Servidor:
    {"type":"snapshot","channel":"health","payload":{...},"ts":...}   # 1ª vez tras subscribe
    {"type":"update","channel":"health","payload":{...},"ts":...}     # cuando cambia
    {"type":"pong","ts":...}
    {"type":"error","code":"...","channel":"..."}
"""
from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import sys
import time
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

from starlette.websockets import WebSocket, WebSocketDisconnect

sys.path.insert(0, "/home/nosvers")
from voz.auth import validar_token  # noqa: E402

log = logging.getLogger("tablero.v2.ws")

# Canales válidos
VALID_CHANNELS = {
    "health", "claude", "activity", "agentes", "revenue", "aegis", "wake",
    "automation",
    # 006-claudio-voz-cockpit: familia/admin
    "recordatorios", "gastos", "compras", "medicacion", "coche", "menu_dia",
    "bris",
    # 007-claudio-pwa-contextos: contexto trabajo
    "trabajo",
    # 009-claudio-pwa-widgets-ricos
    "huerto_estado", "pedidos_stripe", "aappma_stock", "clima_neuvic",
    "chantiers_activos", "chantiers_agenda", "equipe", "documentos_trabajo",
    # 010-claudio-nosvers-completo
    "briefing_africa", "proxima_publicacion", "vermicultura", "composteur",
    "tareas_dia", "eisenia_run", "web_traffic", "search_console", "ahrefs",
    "engagement_redes", "comentarios_wp", "telegram_resumen", "logs_errores",
}

# Canales que requieren scope JWT específico (007 §FR-E-6).
# Si un cliente intenta suscribirse sin tener `available_contexts` que
# incluya el contexto, devolvemos error y NO entregamos snapshot.
CHANNEL_SCOPE = {
    "trabajo": "trabajo",
    # 009: tabs trabajo requieren scope
    "chantiers_activos": "trabajo",
    "chantiers_agenda": "trabajo",
    "equipe": "trabajo",
    "documentos_trabajo": "trabajo",
}


@dataclass(eq=False)
class Connection:
    websocket: WebSocket
    sub: str
    subscribed: set[str] = field(default_factory=set)
    connected_at: float = field(default_factory=time.time)
    available_contexts: list[str] = field(default_factory=list)

    def __hash__(self) -> int:
        return id(self)

    async def send(self, payload: dict) -> None:
        try:
            await self.websocket.send_text(json.dumps(payload, separators=(",", ":")))
        except Exception as e:
            log.debug(f"send failed sub={self.sub}: {e}")


class Broker:
    """In-memory pub/sub. Singleton via module-level instance `broker` abajo."""

    def __init__(self) -> None:
        self._connections: set[Connection] = set()
        self._channels: dict[str, set[Connection]] = {ch: set() for ch in VALID_CHANNELS}
        self._lock = asyncio.Lock()
        # cache del último snapshot por canal (para snapshot-on-subscribe)
        self._last_snapshots: dict[str, dict] = {}
        # listeners internos por canal — invocados en cada broadcast sin pasar
        # por WebSocket. Usados por el Automation Engine (proyecto 004) para
        # reaccionar a eventos publicados por los cockpit workers.
        self._internal_listeners: dict[str, list[Callable[[dict], Awaitable[None]]]] = {
            ch: [] for ch in VALID_CHANNELS
        }

    def add_internal_listener(self, channel: str, callback: "Callable[[dict], Awaitable[None]]") -> bool:
        """Registra un callback async que recibirá cada payload publicado en `channel`."""
        if channel not in VALID_CHANNELS:
            return False
        self._internal_listeners.setdefault(channel, []).append(callback)
        return True

    async def register(self, conn: Connection) -> None:
        async with self._lock:
            self._connections.add(conn)

    async def unregister(self, conn: Connection) -> None:
        async with self._lock:
            self._connections.discard(conn)
            for ch in list(conn.subscribed):
                self._channels.get(ch, set()).discard(conn)
            conn.subscribed.clear()

    async def subscribe(self, conn: Connection, channel: str) -> bool:
        if channel not in VALID_CHANNELS:
            return False
        # 007 §FR-E-6: gate por contexto si aplica
        scope = CHANNEL_SCOPE.get(channel)
        if scope is not None and scope not in (conn.available_contexts or []):
            return False
        async with self._lock:
            self._channels[channel].add(conn)
            conn.subscribed.add(channel)
        # enviar snapshot cached si lo hay
        snap = self._last_snapshots.get(channel)
        if snap is not None:
            await conn.send({
                "type": "snapshot",
                "channel": channel,
                "payload": snap,
                "ts": int(time.time()),
            })
        return True

    async def unsubscribe(self, conn: Connection, channel: str) -> None:
        async with self._lock:
            self._channels.get(channel, set()).discard(conn)
            conn.subscribed.discard(channel)

    async def broadcast(self, channel: str, payload: dict) -> int:
        """Broadcast a todos los subscritos. Devuelve cuántos recibieron."""
        if channel not in VALID_CHANNELS:
            return 0
        self._last_snapshots[channel] = payload
        msg = {"type": "update", "channel": channel, "payload": payload, "ts": int(time.time())}
        # snapshot de la lista bajo lock para evitar mutación durante iteración
        async with self._lock:
            targets = list(self._channels.get(channel, set()))
            listeners = list(self._internal_listeners.get(channel, []))
        for conn in targets:
            await conn.send(msg)
        # Dispatch a listeners internos — errores no rompen el broadcast.
        for cb in listeners:
            try:
                await cb(payload)
            except Exception as _e:  # noqa: BLE001
                log.debug(f"internal listener error on {channel}: {_e}")
        return len(targets)

    @property
    def stats(self) -> dict:
        return {
            "connections": len(self._connections),
            "channels": {ch: len(s) for ch, s in self._channels.items()},
        }


# Singleton
broker = Broker()


# ─── Worker base ─────────────────────────────────────────────────────────

WorkerTick = Callable[[], Awaitable[dict | None]]


@dataclass
class Worker:
    name: str
    interval_s: float
    tick: WorkerTick
    _task: asyncio.Task | None = None
    _last: dict | None = None

    async def loop(self) -> None:
        log.info(f"worker {self.name} started (interval={self.interval_s}s)")
        while True:
            try:
                snap = await self.tick()
                if snap is None:
                    pass
                elif snap != self._last:
                    self._last = snap
                    await broker.broadcast(self.name, snap)
            except asyncio.CancelledError:
                raise
            except Exception as e:
                log.exception(f"worker {self.name} tick error: {e}")
            await asyncio.sleep(self.interval_s)

    def start(self) -> None:
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self.loop(), name=f"worker:{self.name}")

    async def stop(self) -> None:
        if self._task and not self._task.done():
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task


# ─── Registro de workers (poblado por workers/__init__.py) ───────────────

_workers: list[Worker] = []


def register_worker(w: Worker) -> None:
    _workers.append(w)


async def start_all_workers() -> None:
    for w in _workers:
        w.start()


async def stop_all_workers() -> None:
    for w in _workers:
        await w.stop()


# ─── Handler WS ──────────────────────────────────────────────────────────

async def ws_main_handler(websocket: WebSocket) -> None:
    """Cockpit WebSocket: `wss://.../tablero/api/v2/ws?token=<JWT>`."""
    token = websocket.query_params.get("token", "")
    sub: str | None = None
    available_contexts: list[str] = []
    if token:
        try:
            payload = validar_token(token)
            if payload:
                sub = payload.get("sub")
                available_contexts = list(
                    payload.get("available_contexts") or ["casa", "nosvers"]
                )
        except Exception:
            sub = None
    if not sub:
        await websocket.close(code=4401)
        return

    await websocket.accept()
    conn = Connection(
        websocket=websocket, sub=sub,
        available_contexts=available_contexts,
    )
    await broker.register(conn)
    log.info(f"WS open sub={sub} stats={broker.stats}")

    try:
        while True:
            try:
                raw = await websocket.receive_text()
            except WebSocketDisconnect:
                break
            try:
                msg = json.loads(raw)
            except Exception:
                await conn.send({"type": "error", "code": "bad_message"})
                continue
            t = msg.get("type")
            ch = msg.get("channel")
            if t == "subscribe" and isinstance(ch, str):
                ok = await broker.subscribe(conn, ch)
                if not ok:
                    await conn.send({"type": "error", "code": "unknown_channel", "channel": ch})
            elif t == "unsubscribe" and isinstance(ch, str):
                await broker.unsubscribe(conn, ch)
            elif t == "ping":
                await conn.send({"type": "pong", "ts": int(time.time())})
            else:
                await conn.send({"type": "error", "code": "bad_message"})
    finally:
        await broker.unregister(conn)
        log.info(f"WS close sub={sub} stats={broker.stats}")
