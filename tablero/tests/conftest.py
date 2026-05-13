"""Pytest config for tablero — boots an in-process Starlette app and gives a TestClient."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from starlette.applications import Starlette
from starlette.testclient import TestClient

sys.path.insert(0, "/home/nosvers")

from voz.auth import emitir_token  # noqa: E402
from tablero.rest import ROUTES  # noqa: E402


@pytest.fixture(scope="session")
def app() -> Starlette:
    return Starlette(routes=ROUTES)


@pytest.fixture()
def client(app: Starlette) -> TestClient:
    return TestClient(app)


@pytest.fixture()
def angel_token() -> str:
    return emitir_token("pytest-angel", ttl_days=1, autor="angel")["jwt"]


@pytest.fixture()
def africa_token() -> str:
    return emitir_token("pytest-africa", ttl_days=1, autor="africa")["jwt"]
