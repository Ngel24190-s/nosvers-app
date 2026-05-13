"""tablero.v2.atomic_write — escritura atómica al vault (D-013).

Patrón tmp-en-mismo-dir + os.replace para garantizar zero-corruption ante crash.
POSIX rename(2) es atómico dentro del mismo filesystem; al crear el tmp en el
mismo directorio que el destino, garantizamos mismo FS por construcción.
"""
from __future__ import annotations

import os
import uuid
from pathlib import Path


def escribir_atomico(destino: Path, contenido: bytes | str, encoding: str = "utf-8") -> None:
    """Escribe `contenido` en `destino` de forma atómica.

    Crea un archivo tmp en el mismo directorio, escribe + flush + fsync, y luego
    lo renombra al destino con os.replace (atómico en POSIX).

    En caso de error a mitad: el tmp queda y se intenta limpiar; el destino
    conserva su contenido previo (o no existe si era nueva).
    """
    destino = Path(destino)
    if isinstance(contenido, str):
        data = contenido.encode(encoding)
    else:
        data = contenido

    destino.parent.mkdir(parents=True, exist_ok=True)

    tmp = destino.parent / f".{destino.name}.tmp.{os.getpid()}.{uuid.uuid4().hex[:8]}"
    try:
        with open(tmp, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, destino)
    except Exception:
        try:
            tmp.unlink(missing_ok=True)
        except Exception:
            pass
        raise


def mover_atomico(src: Path, dst: Path) -> None:
    """Mueve `src` a `dst` atómicamente. Requiere mismo filesystem."""
    src = Path(src)
    dst = Path(dst)
    if not src.exists():
        raise FileNotFoundError(f"src no existe: {src}")
    if dst.exists():
        raise FileExistsError(f"dst ya existe: {dst}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    os.replace(src, dst)
