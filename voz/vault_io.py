"""
voz.vault_io — Lectura y escritura segura de los archivos del diario.

Contrato: ver specs/001-voice-assistant/contracts/vault_schema.md

Multi-usuario (BRIEF §14, 2026-05-13): pool común en knowledge_base/dia/.
Cada nota lleva campo `autor` en el frontmatter. Audio con sufijo _{autor}.
"""
from __future__ import annotations

import fcntl
import re
import time
from dataclasses import dataclass, field, asdict
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Iterator

import yaml

VAULT_BASE = Path("/home/nosvers/public_html/knowledge_base")
DIA_DIR = VAULT_BASE / "dia"
AUDIO_DIR = DIA_DIR / "audio"
RESUMENES_DIR = DIA_DIR / "resumenes"
PROMPTS_DIR = VAULT_BASE / "prompts"
SYSTEM_DIR = VAULT_BASE / "system"
SPEAKERS_DIR = SYSTEM_DIR / "speakers"

ETIQUETAS_VALIDAS = {"trabajo", "nosvers", "familia", "mental", "idea", "otro"}
ORIGENES_VALIDOS = {"voz_movil", "voz_linux", "texto_directo", "otro"}
AUTORES_VALIDOS = {"angel", "africa"}

LOCK_TIMEOUT_S = 5.0
LOCK_RETRIES = 3
LOCK_BACKOFF_S = [1.0, 2.0, 4.0]


class VaultLockedError(Exception):
    pass


@dataclass
class Nota:
    ts: str
    autor: str                 # "angel" | "africa"  (BRIEF §14.2)
    etiqueta: str
    origen: str
    audio: str | None
    clasificador_confianza: float
    clasificador_modelo: str
    texto: str

    @property
    def dt(self) -> datetime:
        return datetime.fromisoformat(self.ts)

    def to_frontmatter_block(self) -> str:
        meta = {
            "ts": self.ts,
            "autor": self.autor,
            "etiqueta": self.etiqueta,
            "origen": self.origen,
            "audio": self.audio,
            "clasificador_confianza": round(self.clasificador_confianza, 3),
            "clasificador_modelo": self.clasificador_modelo,
        }
        yaml_block = yaml.safe_dump(meta, allow_unicode=True, sort_keys=False).strip()
        return f"---\n{yaml_block}\n---\n\n{self.texto.strip()}\n"


def _normalize_etiqueta(value: str | None) -> str:
    if not value or value == "auto":
        return "otro"
    return value if value in ETIQUETAS_VALIDAS else "otro"


def _normalize_origen(value: str | None) -> str:
    if not value:
        return "otro"
    return value if value in ORIGENES_VALIDOS else "otro"


def _normalize_autor(value: str | None) -> str:
    """Normaliza el campo autor. Default 'angel' para compatibilidad con
    notas antiguas mono-usuario (pre-§14)."""
    if not value:
        return "angel"
    v = str(value).strip().lower()
    if v in {"africa", "áfrica", "ÁFRICA"}:
        return "africa"
    if v == "angel":
        return "angel"
    return "angel"


def _open_with_lock(path: Path, mode: str, exclusive: bool):
    lock_op = fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH
    last_err = None
    for attempt in range(LOCK_RETRIES + 1):
        try:
            fh = path.open(mode, encoding="utf-8" if "b" not in mode else None)
            try:
                fcntl.flock(fh.fileno(), lock_op | fcntl.LOCK_NB)
                return fh
            except BlockingIOError as e:
                fh.close()
                last_err = e
                if attempt < LOCK_RETRIES:
                    time.sleep(LOCK_BACKOFF_S[attempt])
                continue
        except FileNotFoundError:
            raise
    raise VaultLockedError(f"No pude bloquear {path}: {last_err}")


_NOTE_SPLIT_RE = re.compile(r"^---\s*$", re.MULTILINE)


def parsear_dia(contenido: str) -> list[Nota]:
    """Parsea el contenido de un archivo del día en notas."""
    notas: list[Nota] = []
    if not contenido.strip():
        return notas
    # Quita la cabecera "# Diario — YYYY-MM-DD\n" si está
    body = contenido
    head_match = re.match(r"^#\s+Diario[^\n]*\n+", body)
    if head_match:
        body = body[head_match.end():]
    # Divide por bloques ---\n<yaml>\n---\n<texto>
    blocks = _NOTE_SPLIT_RE.split(body)
    # Saltamos vacíos del split. Patrón: ['', yaml1, texto1, yaml2, texto2, ...]
    i = 0
    while i < len(blocks):
        chunk = blocks[i].strip()
        if not chunk:
            i += 1
            continue
        # chunk es YAML, siguiente es texto
        if i + 1 < len(blocks):
            yaml_str = chunk
            texto = blocks[i + 1].strip()
            try:
                meta = yaml.safe_load(yaml_str) or {}
            except yaml.YAMLError:
                i += 2
                continue
            if not isinstance(meta, dict) or "ts" not in meta:
                i += 2
                continue
            try:
                notas.append(Nota(
                    ts=str(meta["ts"]),
                    autor=_normalize_autor(meta.get("autor")),
                    etiqueta=_normalize_etiqueta(meta.get("etiqueta")),
                    origen=_normalize_origen(meta.get("origen")),
                    audio=meta.get("audio") if meta.get("audio") not in (None, "null", "") else None,
                    clasificador_confianza=float(meta.get("clasificador_confianza", 0.0)),
                    clasificador_modelo=str(meta.get("clasificador_modelo", "fallback")),
                    texto=texto,
                ))
            except (ValueError, TypeError):
                pass
            i += 2
        else:
            i += 1
    return notas


def _serializar_dia(fecha: date, notas: list[Nota]) -> str:
    header = f"# Diario — {fecha.isoformat()}\n\n"
    body = "\n".join(n.to_frontmatter_block() for n in sorted(notas, key=lambda n: n.dt))
    return header + body


def path_dia(fecha: date) -> Path:
    return DIA_DIR / f"{fecha.isoformat()}.md"


def leer_dia(fecha: date) -> list[Nota]:
    fp = path_dia(fecha)
    if not fp.exists():
        return []
    fh = _open_with_lock(fp, "r", exclusive=False)
    try:
        return parsear_dia(fh.read())
    finally:
        fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
        fh.close()


def escribir_nota(nota: Nota, fecha: date | None = None) -> Path:
    """Escribe una nota en el archivo del día. Idempotente por (ts, texto).

    Reordena el archivo por ts si la nota es anterior a las existentes.
    """
    if fecha is None:
        fecha = nota.dt.date()
    DIA_DIR.mkdir(parents=True, exist_ok=True)
    fp = path_dia(fecha)
    # Touch para que open(r+) funcione
    if not fp.exists():
        fp.write_text("", encoding="utf-8")
    fh = _open_with_lock(fp, "r+", exclusive=True)
    try:
        existentes = parsear_dia(fh.read())
        # Idempotencia por (ts, texto)
        for n in existentes:
            if n.ts == nota.ts and n.texto.strip() == nota.texto.strip():
                return fp  # ya está
        todas = existentes + [nota]
        contenido = _serializar_dia(fecha, todas)
        fh.seek(0)
        fh.truncate()
        fh.write(contenido)
    finally:
        fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
        fh.close()
    return fp


def listar_dias(desde: date | None = None, hasta: date | None = None) -> list[date]:
    if not DIA_DIR.exists():
        return []
    fechas: list[date] = []
    for fp in DIA_DIR.glob("*.md"):
        m = re.match(r"^(\d{4}-\d{2}-\d{2})\.md$", fp.name)
        if not m:
            continue
        try:
            f = date.fromisoformat(m.group(1))
        except ValueError:
            continue
        if desde and f < desde:
            continue
        if hasta and f > hasta:
            continue
        fechas.append(f)
    return sorted(fechas)


def guardar_audio_opus(
    audio_bytes: bytes, fecha: date, hora_min_sec: str, autor: str
) -> Path:
    """Guarda audio en dia/audio/YYYY-MM-DD/HH-MM-SS_{autor}.opus.

    El sufijo _{autor} permite identificar al hablante sin abrir el archivo
    markdown asociado (BRIEF §14.2 redacción 2).
    """
    autor = _normalize_autor(autor)
    sub = AUDIO_DIR / fecha.isoformat()
    sub.mkdir(parents=True, exist_ok=True)
    fp = sub / f"{hora_min_sec}_{autor}.opus"
    fp.write_bytes(audio_bytes)
    return fp


def ruta_audio_relativa(audio_path: Path) -> str:
    """Convierte path absoluto en path relativo al vault, para frontmatter.

    Devuelve algo como 'dia/audio/2026-05-13/17-23-45_angel.opus'.
    """
    try:
        return str(audio_path.relative_to(VAULT_BASE))
    except ValueError:
        return str(audio_path)
