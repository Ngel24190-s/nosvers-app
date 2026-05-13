"""tablero.v2.slug_resolver — resolución de wiki-links [[slug]] (D-002, D-012).

Pipeline determinístico:
1. Normalizar query: lowercase + Unicode NFKD + drop combining marks (acentos).
2. Match contra dict {slug_normalizado → [Path, ...]} reconstruido en startup.
3. Si una sola coincidencia → resuelve.
4. Si múltiples → la de modified_at más reciente; consumer ve N homónimos.
5. Si ninguna → None.

El "slug" es el filename basename sin .md ni prefijo de fecha YYYY-MM-DD-.
"""
from __future__ import annotations

import re
import unicodedata
from pathlib import Path


_DATE_PREFIX_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-")


def slug_de_archivo(path: Path) -> str:
    """Extrae el slug canónico del nombre del archivo:
    'dia/2026-05-13-lombrithé.md' → 'lombrithé'
    'proyectos/tienda.md' → 'tienda'
    """
    nombre = path.stem  # filename sin .md
    return _DATE_PREFIX_RE.sub("", nombre)


def normalizar_slug(s: str) -> str:
    """Lowercase + NFKD + drop combining marks (insensible a acentos)."""
    s = s.strip().lower()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s


def construir_indice_slug(vault_root: Path, excluir_dirs: set[str] | None = None) -> dict[str, list[Path]]:
    """Escanea recursivamente el vault y devuelve dict slug_normalizado → lista de paths.

    excluir_dirs: nombres de carpetas a omitir (p.ej. {'archivo'} para excluir notas archivadas).
    """
    excluir = excluir_dirs or {"archivo"}
    indice: dict[str, list[Path]] = {}

    for archivo in vault_root.rglob("*.md"):
        # Skip si algún ancestro está en la lista de exclusión
        partes = archivo.relative_to(vault_root).parts
        if any(p in excluir for p in partes):
            continue

        slug = slug_de_archivo(archivo)
        norm = normalizar_slug(slug)
        indice.setdefault(norm, []).append(archivo)

    return indice


def resolver(query: str, indice: dict[str, list[Path]]) -> tuple[Path | None, int]:
    """Resuelve un slug query contra el índice.

    Devuelve (path, n_homonimos). Si no hay match, (None, 0). Si hay múltiples,
    devuelve la más reciente por mtime y n_homonimos > 1 para que el caller
    muestre un tooltip "N homónimos".
    """
    norm = normalizar_slug(query)
    candidatos = indice.get(norm, [])
    if not candidatos:
        return None, 0
    if len(candidatos) == 1:
        return candidatos[0], 1
    # múltiples — elegir más reciente por mtime
    candidatos_ordenados = sorted(candidatos, key=lambda p: p.stat().st_mtime, reverse=True)
    return candidatos_ordenados[0], len(candidatos)
