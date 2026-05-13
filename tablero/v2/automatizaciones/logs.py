"""Logs JSONL diarios para ejecuciones de automatizaciones."""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from tablero.v2.automatizaciones import LOGS_DIR

log = logging.getLogger("tablero.v2.automatizaciones.logs")

_lock = asyncio.Lock()


def _log_path(date: str | None = None) -> Path:
    d = date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return Path(LOGS_DIR) / f"{d}.jsonl"


async def append_log(entry: dict) -> None:
    path = _log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(entry, ensure_ascii=False, separators=(",", ":"))
    async with _lock:
        await asyncio.to_thread(_append_sync, path, line)


def _append_sync(path: Path, line: str) -> None:
    with open(path, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def read_logs(date: str | None = None, automation_id: str | None = None, limit: int = 200) -> list[dict]:
    path = _log_path(date)
    if not path.exists():
        return []
    items: list[dict] = []
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if automation_id and rec.get("automation_id") != automation_id:
                continue
            items.append(rec)
    except Exception as e:  # noqa: BLE001
        log.warning(f"read_logs falló: {e}")
    return items[-limit:]
