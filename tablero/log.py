"""
tablero.log — structured logger + Telegram critical alerter for the dashboard backend.

Mirrors the logging style of `voz.rest` so a single grep across `journalctl -u nosvers-mcp`
returns rows from both extensions. The `alert_critical()` helper de-duplicates alerts to
once per minute per `error_key` so a flood of 500s doesn't spam Angel's phone.
"""
from __future__ import annotations

import logging
import threading
import time
from typing import Optional

_dedupe_lock = threading.Lock()
_dedupe_window_s = 60
_last_alert: dict[str, float] = {}

_LOG_FORMAT = "%(asctime)s [%(name)s] %(levelname)s %(message)s"
_logger_cache: dict[str, logging.Logger] = {}


def get_logger(name: str) -> logging.Logger:
    """Return a logger configured like the voz ones (single stream handler, INFO+)."""
    if name in _logger_cache:
        return _logger_cache[name]
    log = logging.getLogger(name)
    if not log.handlers:
        h = logging.StreamHandler()
        h.setFormatter(logging.Formatter(_LOG_FORMAT))
        log.addHandler(h)
        log.setLevel(logging.INFO)
        log.propagate = False
    _logger_cache[name] = log
    return log


def alert_critical(error_key: str, message: str, *, dedupe_window_s: int = _dedupe_window_s) -> bool:
    """Send a Telegram alert via mcp_server.notify(), throttled per error_key.

    Returns True if the alert was actually sent, False if suppressed by dedupe.
    Imports `notify` lazily to avoid a circular import at module load time.
    """
    now = time.monotonic()
    with _dedupe_lock:
        last = _last_alert.get(error_key, 0.0)
        if now - last < dedupe_window_s:
            return False
        _last_alert[error_key] = now

    try:
        import sys
        sys.path.insert(0, "/home/nosvers")
        from mcp_server import notify  # type: ignore[import]
        return bool(notify(f"⚠️ tablero · {error_key}\n{message}"))
    except Exception as e:  # pragma: no cover — best-effort alert path
        get_logger("tablero.log").warning(f"alert_critical fallback (no Telegram): {e}")
        return False


__all__ = ["get_logger", "alert_critical"]
