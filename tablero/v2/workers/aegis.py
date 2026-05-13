"""Worker aegis: último briefing de AEGIS + alertas activas."""
from __future__ import annotations

import re
import time
from pathlib import Path

KB_AEGIS_DIRS = [
    Path("/home/nosvers/public_html/knowledge_base/aegis"),
    Path("/home/nosvers/public_html/knowledge_base/agentes/aegis"),
    Path("/home/nosvers/public_html/knowledge_base/agentes"),
]

_BRIEFING_RE = re.compile(r"briefing.*\.md$", re.IGNORECASE)
_FM_RE = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.DOTALL)


def _find_latest_briefing() -> Path | None:
    candidates: list[Path] = []
    for d in KB_AEGIS_DIRS:
        if not d.exists():
            continue
        for p in d.rglob("*.md"):
            if _BRIEFING_RE.search(p.name) or "briefing" in p.name.lower():
                candidates.append(p)
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


def _parse_briefing(path: Path) -> dict:
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return {}
    level = "info"
    summary = ""
    m = _FM_RE.match(text)
    body = text
    if m:
        fm = m.group(1)
        body = m.group(2)
        for line in fm.splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                if k.strip().lower() in ("level", "severity", "nivel"):
                    level = v.strip().lower()
    # summary = primer línea no vacía del body
    for line in body.splitlines():
        s = line.strip().lstrip("#").strip()
        if s:
            summary = s[:200]
            break
    return {
        "path": str(path.relative_to(Path("/home/nosvers/public_html"))),
        "ts": int(path.stat().st_mtime),
        "level": level if level in ("info", "warn", "warning", "critical") else "info",
        "summary": summary,
    }


async def aegis_tick() -> dict:
    latest = _find_latest_briefing()
    if latest is None:
        return {
            "last_briefing": None,
            "alerts_active": [],
        }
    briefing = _parse_briefing(latest)
    alerts: list[dict] = []
    if briefing.get("level") in ("warn", "warning", "critical"):
        alerts.append({
            "id": briefing.get("path", "?"),
            "level": briefing["level"],
            "msg": briefing.get("summary", ""),
        })
    return {
        "last_briefing": briefing,
        "alerts_active": alerts,
    }
