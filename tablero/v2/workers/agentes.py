"""Worker agentes: estado del unified-agent."""
from __future__ import annotations

import time
from pathlib import Path

AGENTS_PATH = Path("/home/nosvers/agents")
LOG_PATH = Path("/home/nosvers/logs")

# Lista canónica del MCP server + ampliada con los visibles
KNOWN_AGENTES = [
    "orchestrator",
    "agt01_visual",
    "agt02_instagram",
    "agt04_seo",
    "agt05_africa",
    "agt06_infoproduct",
    "agt07_youtube",
    "agt08_facebook",
    "agt10_community",
    "agt_aegis",
    "agt_agronome",
    "agt_analyste",
    "agt_berger",
    "agt_directeur",
    "agt_eisenia",
    "agt_infra",
]


def _agent_state(name: str) -> dict:
    py = AGENTS_PATH / f"{name}.py"
    logf = LOG_PATH / f"{name}.log"
    last_run_ts = 0
    last_status: str | None = None
    state = "idle"
    if not py.exists():
        return {"id": name, "state": "missing", "last_run_ts": 0, "last_status": None}
    if logf.exists():
        try:
            mtime = int(logf.stat().st_mtime)
            last_run_ts = mtime
            # Si fue modificado <30s, asumimos running
            if (time.time() - mtime) < 30:
                state = "running"
            else:
                state = "idle"
            # Leer última línea para inferir status
            try:
                with logf.open("rb") as f:
                    f.seek(0, 2)
                    size = f.tell()
                    f.seek(max(size - 1024, 0))
                    tail = f.read().decode("utf-8", errors="replace").strip()
                if tail:
                    line = tail.splitlines()[-1] if tail else ""
                    upper = line.upper()
                    if "ERROR" in upper or "FAIL" in upper or "EXCEPTION" in upper:
                        last_status = "error"
                        state = "error"
                    elif "OK" in upper or "DONE" in upper or "SUCCESS" in upper:
                        last_status = "ok"
                    else:
                        last_status = line[:80]
            except Exception:
                pass
        except Exception:
            pass
    return {
        "id": name,
        "state": state,
        "last_run_ts": last_run_ts,
        "last_status": last_status,
    }


async def agentes_tick() -> dict:
    return {"agentes": [_agent_state(n) for n in KNOWN_AGENTES]}
