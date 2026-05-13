"""Worker activity: tail journalctl + broadcast deltas en ring buffer."""
from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import time

from tablero.v2.ws import broker

log = logging.getLogger("tablero.v2.workers.activity")

_buffer: list[dict] = []
_MAX_BUFFER = 50
_task: asyncio.Task | None = None


def _priority_to_level(p) -> str:
    """syslog priority 0-7 → level string."""
    try:
        n = int(p)
    except Exception:
        return "INFO"
    if n <= 3:
        return "ERROR"
    if n == 4:
        return "WARN"
    if n == 5:
        return "NOTICE"
    return "INFO"


def _push_line(line: dict) -> None:
    _buffer.append(line)
    if len(_buffer) > _MAX_BUFFER:
        del _buffer[: len(_buffer) - _MAX_BUFFER]


async def _broadcast_buffer() -> None:
    await broker.broadcast("activity", {"lines": list(_buffer)})


async def _journalctl_loop() -> None:
    cmd = [
        "journalctl",
        "--follow",
        "-u", "nosvers-mcp",
        "-u", "nosvers-voice",
        "-u", "nosvers-bot",
        "--output=json",
        "--no-pager",
        "-n", "20",
    ]
    while True:
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
            )
        except FileNotFoundError:
            log.warning("journalctl no disponible; activity worker dormido")
            _push_line({
                "ts": int(time.time()),
                "unit": "system",
                "level": "INFO",
                "msg": "journalctl no disponible — activity stream limitado",
            })
            await _broadcast_buffer()
            return
        log.info("activity worker started (journalctl --follow)")
        try:
            assert proc.stdout is not None
            while True:
                line = await proc.stdout.readline()
                if not line:
                    break
                try:
                    record = json.loads(line)
                except Exception:
                    continue
                ts_us = record.get("__REALTIME_TIMESTAMP", "0")
                try:
                    ts = int(int(ts_us) // 1_000_000)
                except Exception:
                    ts = int(time.time())
                unit = record.get("_SYSTEMD_UNIT", "?")
                if isinstance(unit, str) and unit.endswith(".service"):
                    unit = unit[: -len(".service")]
                msg = record.get("MESSAGE", "")
                if isinstance(msg, list):
                    msg = "".join(chr(b) for b in msg if isinstance(b, int))
                level = _priority_to_level(record.get("PRIORITY", "6"))
                _push_line({
                    "ts": ts,
                    "unit": str(unit)[:32],
                    "level": level,
                    "msg": str(msg)[:200],
                })
                await _broadcast_buffer()
        except asyncio.CancelledError:
            proc.kill()
            raise
        except Exception as e:
            log.exception(f"journalctl loop error: {e}")
        with contextlib.suppress(Exception):
            proc.kill()
        await asyncio.sleep(2.0)  # backoff antes de re-spawn


def start_activity_worker() -> None:
    global _task
    if _task is None or _task.done():
        _task = asyncio.create_task(_journalctl_loop(), name="worker:activity")


async def stop_activity_worker() -> None:
    global _task
    if _task and not _task.done():
        _task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await _task
