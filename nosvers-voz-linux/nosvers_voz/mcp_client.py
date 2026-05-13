"""Cliente HTTPS contra el MCP server del VPS NosVers.

Usa los endpoints REST `/voz/api/...` (mismo binario que el MCP, ver
contracts/rest_endpoints.md). Auth Bearer JWT.

Asíncrono con httpx para no bloquear el loop de la sesión voz.
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Any

import httpx

from .config import Config, load_config

log = logging.getLogger(__name__)


class MCPClientError(RuntimeError):
    pass


class MCPClient:
    def __init__(self, cfg: Config | None = None) -> None:
        self.cfg = cfg or load_config()
        if not self.cfg.mcp_url or not self.cfg.mcp_token:
            raise MCPClientError(
                "mcp_url o mcp_token no configurados. Editar "
                "~/.config/nosvers-voz/config.toml"
            )
        self._client = httpx.AsyncClient(
            base_url=self.cfg.mcp_url.rstrip("/"),
            headers={"Authorization": f"Bearer {self.cfg.mcp_token}"},
            timeout=30.0,
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "MCPClient":
        return self

    async def __aexit__(self, *exc) -> None:
        await self.aclose()

    # -------- métodos públicos --------

    async def capturar(
        self,
        texto: str,
        *,
        ts_iso: str | None = None,
        etiqueta: str = "auto",
        origen: str = "voz_linux",
        device_label: str = "pc-casa-angel",
        client_uuid: str | None = None,
    ) -> dict[str, Any]:
        body = {
            "texto": texto,
            "ts_iso": ts_iso or datetime.now().astimezone().isoformat(),
            "etiqueta": etiqueta,
            "origen": origen,
            "device_label": device_label,
            "client_uuid": client_uuid or str(uuid.uuid4()),
        }
        return await self._post_json("/voz/api/capturar", body)

    async def contexto(
        self,
        dias: int = 7,
        *,
        calendario: bool = True,
        agentes: bool = True,
        etiquetas: list[str] | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {
            "dias": dias,
            "calendario": int(calendario),
            "agentes": int(agentes),
        }
        if etiquetas:
            params["etiquetas"] = ",".join(etiquetas)
        return await self._get_json("/voz/api/contexto", params)

    async def buscar(
        self,
        query: str,
        *,
        desde: str | None = None,
        hasta: str | None = None,
        limite: int = 10,
        etiqueta: str | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"q": query, "limite": limite}
        if desde:
            params["desde"] = desde
        if hasta:
            params["hasta"] = hasta
        if etiqueta:
            params["etiqueta"] = etiqueta
        return await self._get_json("/voz/api/buscar", params)

    # -------- internals --------

    async def _post_json(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        try:
            r = await self._client.post(path, json=body)
        except httpx.HTTPError as e:
            raise MCPClientError(f"network: {e}") from e
        return self._parse(r)

    async def _get_json(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        try:
            r = await self._client.get(path, params=params)
        except httpx.HTTPError as e:
            raise MCPClientError(f"network: {e}") from e
        return self._parse(r)

    def _parse(self, r: httpx.Response) -> dict[str, Any]:
        if r.status_code == 401:
            raise MCPClientError("auth_invalido — token revocado o expirado")
        if r.status_code >= 500:
            raise MCPClientError(f"server {r.status_code}: {r.text[:200]}")
        try:
            data = r.json()
        except json.JSONDecodeError as e:
            raise MCPClientError(f"respuesta no-JSON: {r.text[:200]}") from e
        if not data.get("ok", False):
            raise MCPClientError(
                f"server-error: {data.get('error')} / {data.get('detalle', '')}"
            )
        return data


# -------- modo CLI rápido para sanity check --------

async def _cli() -> None:
    import argparse

    p = argparse.ArgumentParser(description="MCP client test")
    sub = p.add_subparsers(dest="cmd", required=True)
    pc = sub.add_parser("capturar")
    pc.add_argument("--texto", required=True)
    pctx = sub.add_parser("contexto")
    pctx.add_argument("--dias", type=int, default=7)
    pb = sub.add_parser("buscar")
    pb.add_argument("--q", required=True)
    args = p.parse_args()

    logging.basicConfig(level=logging.INFO)
    async with MCPClient() as cli:
        if args.cmd == "capturar":
            print(await cli.capturar(args.texto))
        elif args.cmd == "contexto":
            print(await cli.contexto(args.dias))
        elif args.cmd == "buscar":
            print(await cli.buscar(args.q))


def main() -> None:
    asyncio.run(_cli())


if __name__ == "__main__":
    main()
