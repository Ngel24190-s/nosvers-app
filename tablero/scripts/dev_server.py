#!/usr/bin/env python3
"""Local dev server — mounts voz.rest + tablero.rest on a Starlette app at :8766.

Does NOT load FastMCP (that runs in the prod process). For local smoke and tests only.
Run:  TABLERO_DEV=1 MCP_TOKEN=... python3 tablero/scripts/dev_server.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, "/home/nosvers")

import uvicorn
from starlette.applications import Starlette

from voz.rest import ROUTES as voz_routes
from tablero.rest import ROUTES as tablero_routes


def build_app() -> Starlette:
    return Starlette(routes=list(voz_routes) + list(tablero_routes))


if __name__ == "__main__":
    port = int(os.getenv("TABLERO_PORT", "8766"))
    os.environ.setdefault("TABLERO_DEV", "1")
    uvicorn.run(build_app(), host="127.0.0.1", port=port, log_level="info")
