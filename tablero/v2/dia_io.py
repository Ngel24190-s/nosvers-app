"""tablero.v2.dia_io — IO a nivel de ENTRADA dentro de archivos-por-día.

Fase A almacena las notas como N entradas en `dia/<fecha>.md`. Para Fase B+C,
necesitamos editar/archivar/restaurar entradas individualmente preservando
todos los campos del frontmatter inline (incluidos los nuevos: modified_at,
archived_at, archive_reason) — algo que `voz.vault_io.parsear_dia` no hace
(destruye campos extras al re-serializar como `Nota` dataclass).

Este módulo opera con dicts plenos y preserva cualquier campo del frontmatter
no listado explícitamente.

Identidad: una entrada se identifica por (fecha, ts). El ts es inmutable.
El campo `modified_at` se añade/actualiza solo al editar (D-003).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

import yaml

from tablero.v2.atomic_write import escribir_atomico
from tablero.v2.frontmatter import _StringTimestampLoader


_HEADER_RE = re.compile(r"^#\s+Diario[^\n]*\n+")
_SPLIT_RE = re.compile(r"^---\s*$", re.MULTILINE)


@dataclass
class Entrada:
    """Una entrada de un archivo dia/<fecha>.md, con todo el frontmatter preservado."""
    ts: str                                   # inmutable, anchor de identidad
    meta: dict[str, Any] = field(default_factory=dict)   # frontmatter completo (incluye ts)
    texto: str = ""

    @property
    def autor(self) -> str:
        return str(self.meta.get("autor", "angel"))

    @property
    def etiqueta(self) -> str:
        return str(self.meta.get("etiqueta", "otro"))

    @property
    def modified_at(self) -> str | None:
        v = self.meta.get("modified_at")
        return str(v) if v is not None else None

    @property
    def archived_at(self) -> str | None:
        v = self.meta.get("archived_at")
        return str(v) if v is not None else None

    @property
    def concurrency_token(self) -> str:
        """Token usado para If-Match (D-003).

        Si la entrada nunca ha sido editada, el token es el `ts` (inmutable).
        Tras la primera edición, el token es `modified_at` (refrescado en cada edit).
        """
        return self.modified_at or self.ts

    def serializar_bloque(self) -> str:
        """Reserializa la entrada (frontmatter + cuerpo) en formato del día."""
        yaml_block = yaml.safe_dump(
            self.meta,
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False,
        ).strip()
        return f"---\n{yaml_block}\n---\n\n{self.texto.strip()}\n"


def parsear_dia(contenido: str) -> list[Entrada]:
    """Parsea archivo `dia/<fecha>.md` preservando TODOS los campos del frontmatter.

    Distinto de `voz.vault_io.parsear_dia`: este no convierte a la dataclass
    `Nota` (que descarta campos extras). Devuelve lista ordenada por aparición
    en el archivo.
    """
    entradas: list[Entrada] = []
    if not contenido.strip():
        return entradas

    body = contenido
    head_match = _HEADER_RE.match(body)
    if head_match:
        body = body[head_match.end():]

    blocks = _SPLIT_RE.split(body)
    i = 0
    while i < len(blocks):
        chunk = blocks[i].strip()
        if not chunk:
            i += 1
            continue
        if i + 1 >= len(blocks):
            break

        yaml_str = chunk
        texto = blocks[i + 1].strip()

        try:
            meta = yaml.load(yaml_str, Loader=_StringTimestampLoader) or {}
        except yaml.YAMLError:
            i += 2
            continue
        if not isinstance(meta, dict) or "ts" not in meta:
            i += 2
            continue

        entradas.append(Entrada(ts=str(meta["ts"]), meta=meta, texto=texto))
        i += 2

    return entradas


def serializar_dia(fecha: date, entradas: list[Entrada]) -> str:
    """Serializa una lista de entradas como archivo `dia/<fecha>.md`.

    Ordena por ts ascendente para mantener orden cronológico de creación.
    """
    header = f"# Diario — {fecha.isoformat()}\n\n"
    entradas_orden = sorted(entradas, key=lambda e: e.ts)
    body = "\n".join(e.serializar_bloque() for e in entradas_orden)
    return header + body


def path_dia(vault_root: Path, fecha: date) -> Path:
    """Ruta absoluta del archivo del día relativa a vault_root."""
    return Path(vault_root) / "dia" / f"{fecha.isoformat()}.md"


def leer_dia(vault_root: Path, fecha: date) -> list[Entrada]:
    fp = path_dia(vault_root, fecha)
    if not fp.exists():
        return []
    return parsear_dia(fp.read_text(encoding="utf-8"))


def escribir_dia(vault_root: Path, fecha: date, entradas: list[Entrada]) -> Path:
    """Reescribe el archivo del día atómicamente."""
    fp = path_dia(vault_root, fecha)
    contenido = serializar_dia(fecha, entradas)
    escribir_atomico(fp, contenido)
    return fp


def buscar_entrada(entradas: list[Entrada], ts: str) -> Entrada | None:
    """Encuentra una entrada por ts exacto."""
    for e in entradas:
        if e.ts == ts:
            return e
    return None
