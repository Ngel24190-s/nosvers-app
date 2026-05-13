"""tablero.v2.wiki_index — índice in-memory de wiki-links [[slug]] (D-004).

Construido en startup escaneando knowledge_base/ recursivamente. Excluye
dia/archivo/ (notas archivadas no cuentan).

Cada operación de write (capturar / editar / archivar / restaurar / mover)
actualiza el índice in-process tras flushear el archivo (write-through).

Sin watchdog FS, sin polling. Como solo hay un worker uvicorn, el índice
in-memory es siempre coherente.

Tras restart, se reconstruye en startup (medido < 2 s para 5.000 notas).
"""
from __future__ import annotations

import re
import threading
from dataclasses import dataclass
from pathlib import Path

from tablero.v2.slug_resolver import slug_de_archivo, normalizar_slug


# [[slug]] o [[slug|texto]]
_WIKILINK_RE = re.compile(r"\[\[([^\]\|]+)(?:\|[^\]]*)?\]\]")
_CONTEXT_RADIUS = 50


@dataclass
class BacklinkEntry:
    source_slug: str
    source_path: str  # relativa al vault
    source_autor: str | None
    source_modified_at: str | None
    context: str


class WikiIndex:
    """Mantiene el índice de backlinks.

    Estructura interna:
        _by_target: { target_slug_norm: { source_slug_norm: BacklinkEntry } }
        _by_source: { source_slug_norm: set[target_slug_norm] }
    """

    def __init__(self, vault_root: Path, excluir_dirs: set[str] | None = None):
        self.vault_root = Path(vault_root)
        self.excluir = excluir_dirs or {"archivo"}
        self._by_target: dict[str, dict[str, BacklinkEntry]] = {}
        self._by_source: dict[str, set[str]] = {}
        self._lock = threading.RLock()
        self._generated_at: str | None = None

    # -------------------------------------------------------------------------
    # Build / rebuild
    # -------------------------------------------------------------------------
    def build(self) -> None:
        """Reconstruye el índice completo desde disco."""
        with self._lock:
            self._by_target.clear()
            self._by_source.clear()
            if not self.vault_root.exists():
                return
            for archivo in self.vault_root.rglob("*.md"):
                if self._archivo_excluido(archivo):
                    continue
                try:
                    contenido = archivo.read_text(encoding="utf-8")
                except OSError:
                    continue
                self._indexar_archivo(archivo, contenido)
            from datetime import datetime, timezone
            self._generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

    def _archivo_excluido(self, archivo: Path) -> bool:
        try:
            partes = archivo.relative_to(self.vault_root).parts
        except ValueError:
            return True
        return any(p in self.excluir for p in partes)

    def _indexar_archivo(self, archivo: Path, contenido: str) -> None:
        """Sin lock — caller debe tener el lock."""
        source_slug_norm = normalizar_slug(slug_de_archivo(archivo))
        # Resetear cualquier link previo de este source
        self._eliminar_source_sin_lock(source_slug_norm)

        # Extraer autor y modified_at del frontmatter (best-effort)
        autor = None
        modified_at = None
        try:
            from tablero.v2.frontmatter import parse
            meta, _ = parse(contenido)
            autor = meta.get("autor")
            modified_at = meta.get("modified_at")
        except Exception:
            pass

        rel_path = str(archivo.relative_to(self.vault_root))

        for match in _WIKILINK_RE.finditer(contenido):
            target = match.group(1).strip()
            target_norm = normalizar_slug(target)
            start = max(0, match.start() - _CONTEXT_RADIUS)
            end = min(len(contenido), match.end() + _CONTEXT_RADIUS)
            context = contenido[start:end].replace("\n", " ").strip()

            entry = BacklinkEntry(
                source_slug=slug_de_archivo(archivo),
                source_path=rel_path,
                source_autor=str(autor) if autor else None,
                source_modified_at=str(modified_at) if modified_at else None,
                context=context,
            )
            self._by_target.setdefault(target_norm, {})[source_slug_norm] = entry
            self._by_source.setdefault(source_slug_norm, set()).add(target_norm)

    def _eliminar_source_sin_lock(self, source_slug_norm: str) -> None:
        targets = self._by_source.pop(source_slug_norm, set())
        for t in targets:
            bucket = self._by_target.get(t)
            if bucket and source_slug_norm in bucket:
                del bucket[source_slug_norm]
                if not bucket:
                    del self._by_target[t]

    # -------------------------------------------------------------------------
    # Write-through API (D-004)
    # -------------------------------------------------------------------------
    def actualizar_nota(self, archivo: Path, contenido: str) -> None:
        """Llamado tras escribir una nota. Si la nota está en una carpeta
        excluida (p.ej. archivo/), elimina sus referencias del índice."""
        with self._lock:
            if self._archivo_excluido(archivo):
                source_slug_norm = normalizar_slug(slug_de_archivo(archivo))
                self._eliminar_source_sin_lock(source_slug_norm)
            else:
                self._indexar_archivo(archivo, contenido)

    def eliminar_nota(self, archivo: Path) -> None:
        """Llamado tras archivar o eliminar una nota."""
        with self._lock:
            source_slug_norm = normalizar_slug(slug_de_archivo(archivo))
            self._eliminar_source_sin_lock(source_slug_norm)

    def mover_nota(self, src: Path, dst: Path, contenido: str) -> None:
        """Llamado tras mover. Slug puede no cambiar (D-012); si cambia, re-indexa."""
        with self._lock:
            src_slug = normalizar_slug(slug_de_archivo(src))
            dst_slug = normalizar_slug(slug_de_archivo(dst))
            if src_slug != dst_slug:
                # cambio de slug → eliminar referencias del viejo + indexar nuevo
                self._eliminar_source_sin_lock(src_slug)
            if not self._archivo_excluido(dst):
                self._indexar_archivo(dst, contenido)

    # -------------------------------------------------------------------------
    # Read API
    # -------------------------------------------------------------------------
    def backlinks_de(self, target_slug: str) -> list[BacklinkEntry]:
        with self._lock:
            target_norm = normalizar_slug(target_slug)
            return list(self._by_target.get(target_norm, {}).values())

    def indice_completo(self) -> dict[str, list[BacklinkEntry]]:
        with self._lock:
            return {
                t: list(bucket.values())
                for t, bucket in self._by_target.items()
            }

    @property
    def generated_at(self) -> str | None:
        return self._generated_at

    def stats(self) -> dict:
        with self._lock:
            n_links = sum(len(b) for b in self._by_target.values())
            return {
                "n_target_slugs": len(self._by_target),
                "n_source_slugs": len(self._by_source),
                "n_links_total": n_links,
                "generated_at": self._generated_at,
            }


# -----------------------------------------------------------------------------
# Singleton para el proceso uvicorn (sin estado cross-instance — un solo worker)
# -----------------------------------------------------------------------------
_INSTANCE: WikiIndex | None = None


def get_index() -> WikiIndex:
    """Devuelve el singleton; crea uno apuntando al vault default si no existe."""
    global _INSTANCE
    if _INSTANCE is None:
        from voz.vault_io import VAULT_BASE
        _INSTANCE = WikiIndex(VAULT_BASE)
    return _INSTANCE


def set_index(idx: WikiIndex) -> None:
    """Permite a tests inyectar un índice con vault temporal."""
    global _INSTANCE
    _INSTANCE = idx
