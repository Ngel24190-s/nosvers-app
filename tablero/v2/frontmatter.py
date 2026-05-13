"""tablero.v2.frontmatter — parse/serialize seguro de frontmatter YAML.

Wrapper alrededor de la utilidad de voz.vault_io para garantizar que escrituras
al vault preservan todos los campos del frontmatter excepto los explícitamente
modificados. Importante para FR-004 (modified_at) y D-003 (concurrencia).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import yaml


FRONTMATTER_DELIM = "---"


class _StringTimestampLoader(yaml.SafeLoader):
    """SafeLoader que NO convierte timestamps a datetime — los deja como string.

    Esto preserva `modified_at: 2026-05-13T10:00:00+00:00` como string para
    que la comparación con header If-Match sea string-vs-string exacta (D-003).
    """


# Remover el resolver implicito de timestamps
_StringTimestampLoader.yaml_implicit_resolvers = {
    k: [(tag, regexp) for tag, regexp in v if tag != "tag:yaml.org,2002:timestamp"]
    for k, v in _StringTimestampLoader.yaml_implicit_resolvers.items()
}


def parse(text: str) -> tuple[dict[str, Any], str]:
    """Devuelve (meta, body). Si el frontmatter es malformado o ausente,
    devuelve ({}, text) sin levantar excepción (FR-015 graceful handling)."""
    if not text.startswith(FRONTMATTER_DELIM + "\n") and not text.startswith(FRONTMATTER_DELIM + "\r\n"):
        return {}, text

    # Encuentra el cierre del frontmatter
    lines = text.splitlines(keepends=True)
    if not lines or not lines[0].rstrip("\r\n") == FRONTMATTER_DELIM:
        return {}, text

    end_idx = None
    for i, line in enumerate(lines[1:], start=1):
        if line.rstrip("\r\n") == FRONTMATTER_DELIM:
            end_idx = i
            break

    if end_idx is None:
        # Frontmatter sin cierre — tratar todo como body
        return {}, text

    yaml_text = "".join(lines[1:end_idx])
    body = "".join(lines[end_idx + 1:])

    try:
        meta = yaml.load(yaml_text, Loader=_StringTimestampLoader) or {}
        if not isinstance(meta, dict):
            meta = {}
    except yaml.YAMLError:
        meta = {}

    return meta, body


def serialize(meta: dict[str, Any], body: str) -> str:
    """Serializa frontmatter + body. Usa yaml.safe_dump con sort_keys=False
    para preservar orden cuando sea posible."""
    if not meta:
        return body

    # YAML safe_dump por defecto añade un \n al final del documento
    yaml_text = yaml.safe_dump(
        meta,
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
    )

    return f"{FRONTMATTER_DELIM}\n{yaml_text}{FRONTMATTER_DELIM}\n{body}"


def now_modified_at() -> str:
    """ISO 8601 con tz Europe/Madrid o UTC. Aceptamos UTC con sufijo Z para
    simplicidad y porque el cliente lo formatea con Intl.DateTimeFormat."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def actualizar_modified_at(meta: dict[str, Any]) -> dict[str, Any]:
    """Devuelve una copia con `modified_at` refrescado."""
    nuevo = dict(meta)
    nuevo["modified_at"] = now_modified_at()
    return nuevo
