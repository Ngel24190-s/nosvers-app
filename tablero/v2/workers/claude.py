"""Worker claude: estado del nosvers-voice service + tokens acumulados hoy."""
from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path

TOKENS_FILE = Path("/home/nosvers/logs/claude_tokens.json")
STATE_FILE = Path("/tmp/nosvers_voz_state.json")
_tokens_history: list[int] = []
_MAX_HISTORY = 24  # 24 muestras (1/h durante 24h)
_last_sample_hour: int = -1


async def _is_voice_service_active() -> bool:
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


def _read_tokens_today() -> int:
    try:
        if not TOKENS_FILE.exists():
            return 0
        data = json.loads(TOKENS_FILE.read_text())
        today = time.strftime("%Y-%m-%d")
        return int(data.get(today, 0))
    except Exception:
        return 0


def _read_state() -> dict:
    """Lee /tmp/nosvers_voz_state.json si existe (escrito por voz service)."""
    try:
        if STATE_FILE.exists():
            return json.loads(STATE_FILE.read_text())
    except Exception:
        pass
    return {}


async def claude_tick() -> dict:
    global _last_sample_hour
    active = await _is_voice_service_active()
    state_data = _read_state()
    last_interaction = state_data.get("last_interaction_ts", 0)
    vstate = state_data.get("state")
    if not active:
        ui_state = "offline"
    elif vstate == "speaking":
        ui_state = "speaking"
    elif vstate in ("thinking", "processing"):
        ui_state = "thinking"
    elif vstate == "listening":
        ui_state = "listening"
    else:
        # online si interaction < 5 min, sino online tenue
        ui_state = "online"
    tokens_today = _read_tokens_today()
    # Muestreo 1/h
    hour = int(time.time() // 3600)
    if hour != _last_sample_hour:
        _last_sample_hour = hour
        _tokens_history.append(tokens_today)
        if len(_tokens_history) > _MAX_HISTORY:
            del _tokens_history[: len(_tokens_history) - _MAX_HISTORY]
    return {
        "state": ui_state,
        "service_active": active,
        "last_interaction_ts": int(last_interaction),
        "tokens_today": tokens_today,
        "tokens_history": list(_tokens_history),
    }
