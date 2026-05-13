"""
voz.speaker_id — Identificación de hablante (Angel / África).

BRIEF §14.1 (decisión Angel 2026-05-13):
- Enrollment one-shot: ~30s por usuario → embedding promedio guardado en
  knowledge_base/system/speakers/{angel,africa}.npy
- En cada captura: extraer embedding del audio, cosine similarity contra
  los enrolled.
- Umbrales:
    >= 0.75            → identidad asignada
    [0.55, 0.75)       → preguntar ("¿Eres Angel o África?")
    <  0.55            → no_reconocido (registrar + fallback al default)

Backend: Resemblyzer (light, ~30 MB, CPU OK, embeddings 256-d). Más
ligero que pyannote y suficiente para 2 voces.
"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from . import vault_io
from .vault_io import AUTORES_VALIDOS

log = logging.getLogger("voz.speaker_id")

UMBRAL_ACEPTAR = 0.75
UMBRAL_PREGUNTAR = 0.55


@dataclass(frozen=True)
class IdentResult:
    autor: str | None      # "angel" | "africa" | None si sin enrollment
    similarity: float      # similitud máxima encontrada
    accion: str            # "aceptar" | "preguntar" | "rechazar" | "sin_enrollment"


# Encoder se carga lazy (Resemblyzer descarga modelo en primera invocación)
_ENCODER_LOCK = threading.Lock()
_ENCODER = None


def _encoder():
    global _ENCODER
    with _ENCODER_LOCK:
        if _ENCODER is None:
            from resemblyzer import VoiceEncoder
            log.info("cargando Resemblyzer VoiceEncoder")
            _ENCODER = VoiceEncoder()
        return _ENCODER


def _path_emb(autor: str) -> Path:
    # vault_io.SPEAKERS_DIR se referencia dinámicamente para respetar
    # monkeypatches en tests.
    return vault_io.SPEAKERS_DIR / f"{autor}.npy"


def _preprocess(audio: bytes | np.ndarray | str | Path) -> np.ndarray:
    """Convierte entrada a float32 mono 16k normalizado para Resemblyzer."""
    from resemblyzer import preprocess_wav

    if isinstance(audio, (str, Path)):
        return preprocess_wav(audio)
    if isinstance(audio, np.ndarray):
        # Resemblyzer espera float32 normalizado [-1, 1]
        arr = audio.astype(np.float32)
        if np.max(np.abs(arr)) > 1.5:
            arr = arr / 32768.0
        return preprocess_wav(arr, source_sr=16000)
    if isinstance(audio, (bytes, bytearray)):
        # Asume WAV/Opus/cualquier formato soportable por soundfile.
        import io, soundfile as sf
        data, sr = sf.read(io.BytesIO(audio), dtype="float32", always_2d=False)
        if data.ndim > 1:
            data = data.mean(axis=1)
        return preprocess_wav(data, source_sr=sr)
    raise TypeError(f"audio tipo no soportado: {type(audio)}")


def enroll(autor: str, audio: bytes | np.ndarray | str | Path) -> dict:
    """Calcula y persiste el embedding de referencia de un usuario.

    Recibe audio crudo (ideal: 30s+) y guarda el embedding 256-d en
    knowledge_base/system/speakers/{autor}.npy.
    """
    autor = autor.strip().lower()
    if autor not in AUTORES_VALIDOS:
        raise ValueError(f"autor inválido: {autor}. Esperado: {sorted(AUTORES_VALIDOS)}")
    vault_io.SPEAKERS_DIR.mkdir(parents=True, exist_ok=True)
    wav = _preprocess(audio)
    if len(wav) < 16000 * 5:  # < 5 segundos
        log.warning("enrollment %s: audio muy corto (%.1fs). Recomendado 30s+.", autor, len(wav) / 16000)
    emb = _encoder().embed_utterance(wav)
    np.save(_path_emb(autor), emb)
    log.info("enrollment OK %s: embedding %dd guardado en %s", autor, len(emb), _path_emb(autor))
    return {"ok": True, "autor": autor, "dim": len(emb), "path": str(_path_emb(autor))}


def _cargar_referencias() -> dict[str, np.ndarray]:
    refs: dict[str, np.ndarray] = {}
    for autor in AUTORES_VALIDOS:
        fp = _path_emb(autor)
        if fp.exists():
            try:
                refs[autor] = np.load(fp)
            except (OSError, ValueError) as e:
                log.error("error cargando embedding %s: %s", autor, e)
    return refs


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    na = float(np.linalg.norm(a))
    nb = float(np.linalg.norm(b))
    if na < 1e-9 or nb < 1e-9:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def identificar(audio: bytes | np.ndarray | str | Path) -> IdentResult:
    """Identifica al hablante de un audio comparando con embeddings enrolled.

    Devuelve IdentResult con autor, similarity y acción a tomar.
    """
    refs = _cargar_referencias()
    if not refs:
        return IdentResult(autor=None, similarity=0.0, accion="sin_enrollment")
    wav = _preprocess(audio)
    emb = _encoder().embed_utterance(wav)
    similares = {a: _cosine(emb, r) for a, r in refs.items()}
    mejor_autor = max(similares, key=lambda a: similares[a])
    mejor_sim = similares[mejor_autor]
    if mejor_sim >= UMBRAL_ACEPTAR:
        accion = "aceptar"
    elif mejor_sim >= UMBRAL_PREGUNTAR:
        accion = "preguntar"
    else:
        accion = "rechazar"
        mejor_autor = None
    log.info(
        "identificar similarities=%s → autor=%s sim=%.3f accion=%s",
        {a: round(s, 3) for a, s in similares.items()},
        mejor_autor, mejor_sim, accion,
    )
    return IdentResult(autor=mejor_autor, similarity=mejor_sim, accion=accion)


def listar_enrolled() -> list[dict]:
    """Devuelve qué autores tienen embedding registrado."""
    out = []
    for autor in sorted(AUTORES_VALIDOS):
        fp = _path_emb(autor)
        if fp.exists():
            out.append({
                "autor": autor,
                "path": str(fp),
                "tamano_bytes": fp.stat().st_size,
                "modificado": fp.stat().st_mtime,
            })
    return out
