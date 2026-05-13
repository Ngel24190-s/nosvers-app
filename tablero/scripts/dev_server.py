#!/usr/bin/env python3
"""Local dev server — mounts voz.rest + tablero.rest on a Starlette app at :8766.

Does NOT load FastMCP (that runs in the prod process). For local smoke and tests only.
Run:  TABLERO_DEV=1 MCP_TOKEN=... python3 tablero/scripts/dev_server.py
"""
from __future__ import annotations

import asyncio
import os
import sys
from contextlib import asynccontextmanager

sys.path.insert(0, "/home/nosvers")

import uvicorn
from starlette.applications import Starlette

from voz.rest import ROUTES as voz_routes
from tablero.rest import ROUTES as tablero_routes
from tablero.v2.workers import register_all, start_activity_worker
from tablero.v2.ws import start_all_workers, stop_all_workers


@asynccontextmanager
async def lifespan(app):
    register_all()
    await start_all_workers()
    activity_task = None
    try:
        activity_task = await start_activity_worker()
    except Exception as e:
        import logging
        logging.getLogger("tablero.v2.workers").warning(f"activity worker no arrancó: {e}")
    try:
        yield
    finally:
        if activity_task and not activity_task.done():
            activity_task.cancel()
            try:
                await activity_task
            except (asyncio.CancelledError, Exception):
                pass
        await stop_all_workers()


def build_app() -> Starlette:
    return Starlette(routes=list(voz_routes) + list(tablero_routes), lifespan=lifespan)


if __name__ == "__main__":
    port = int(os.getenv("TABLERO_PORT", "8766"))
    os.environ.setdefault("TABLERO_DEV", "1")
    uvicorn.run(build_app(), host="127.0.0.1", port=port, log_level="info")
