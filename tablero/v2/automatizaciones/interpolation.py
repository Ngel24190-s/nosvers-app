"""Interpolación de {{vars}} en strings.

Soporta:
- {{trigger.X}}
- {{paso_<n>.X}}
- {{env.VAR}}   (whitelist)
- {{now}}, {{today}}

Faltante = "" y registra warning vía callback opcional.
"""
from __future__ import annotations

import os
import re
from datetime import datetime, timezone
from typing import Any, Callable

_VAR_RE = re.compile(r"\{\{\s*([\w.]+)\s*\}\}")

# Whitelist de env vars que pueden interpolarse (no filtrar secretos).
ENV_WHITELIST = {
    "ANGEL_CHAT_ID",
    "ALERTES_CHAT_ID",
    "HQ_GROUP_ID",
    "CLUB_GROUP_ID",
    "WP_API",
    "APP_URL",
}


def _lookup(path: str, ctx: dict[str, Any]) -> Any:
    parts = path.split(".")
    if parts[0] == "env":
        if len(parts) != 2 or parts[1] not in ENV_WHITELIST:
            return None
        return os.environ.get(parts[1])
    if path == "now":
        return datetime.now(timezone.utc).isoformat()
    if path == "today":
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")
    cur: Any = ctx
    for p in parts:
        if isinstance(cur, dict) and p in cur:
            cur = cur[p]
        elif hasattr(cur, p):
            cur = getattr(cur, p)
        else:
            return None
    return cur


def resolve(template: str, ctx: dict[str, Any], on_missing: Callable[[str], None] | None = None) -> str:
    """Sustituye {{vars}} en `template` con valores de ctx."""
    def repl(m: re.Match) -> str:
        path = m.group(1)
        val = _lookup(path, ctx)
        if val is None:
            if on_missing:
                on_missing(path)
            return ""
        return str(val)
    return _VAR_RE.sub(repl, template)


def resolve_dict(obj: Any, ctx: dict[str, Any], on_missing: Callable[[str], None] | None = None) -> Any:
    """Resuelve recursivamente {{vars}} en strings dentro de dict/list."""
    if isinstance(obj, str):
        return resolve(obj, ctx, on_missing)
    if isinstance(obj, dict):
        return {k: resolve_dict(v, ctx, on_missing) for k, v in obj.items()}
    if isinstance(obj, list):
        return [resolve_dict(v, ctx, on_missing) for v in obj]
    return obj
