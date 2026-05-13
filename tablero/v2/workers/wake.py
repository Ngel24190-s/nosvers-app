"""Worker wake: lee /tmp/nosvers_wake_state.json + check service nosvers-voice."""
from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path

STATE_FILE = Path("/tmp/nosvers_wake_state.json")


async def _voice_active() -> bool:
    try:
        proc = await asyncio.create_subprocess_exec(
            "systemctl", "is-active", "nosvers-voice",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        out, _ = await asyncio.wait_for(proc.communicate(), timeout=2.0)
        return out.decode().strip() == "active"
    except Exception:
        return False


async def wake_tick() -> dict:
    active = await _voice_active()
    state = "idle"
    last_wake_ts = 0
    if STATE_FILE.exists():
        try:
            d = json.loads(STATE_FILE.read_text())
            s = d.get("state")
            if s in ("idle", "listening", "processing"):
                state = s
            last_wake_ts = int(d.get("last_wake_ts", 0))
        except Exception:
            pass
    if not active:
        state = "idle"
    return {
        "state": state,
        "last_wake_ts": last_wake_ts,
        "voice_service_active": active,
    }
