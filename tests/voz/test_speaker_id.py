"""R8 — Tests de voz.speaker_id (mockean Resemblyzer para no instalar la dep).

La librería Resemblyzer pesa ~30MB (PyTorch implícito). Para CI/tests rápidos
mockeamos el VoiceEncoder y preprocess_wav. La instalación real solo es
necesaria en producción (VPS) cuando Angel ejecute el enrollment one-shot.
"""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import numpy as np
import pytest


# ---------------- mocks ----------------

class _FakeEncoder:
    """Devuelve un embedding 256-d determinista por 'firma' del audio."""

    def embed_utterance(self, wav):  # noqa: D401
        # Si wav es una marca específica, devuelve el vector matching.
        if isinstance(wav, np.ndarray) and wav.size > 0:
            seed = int(abs(wav.sum() * 1000)) % (2**32)
        else:
            seed = 0
        rng = np.random.default_rng(seed)
        v = rng.standard_normal(256).astype(np.float32)
        return v / (np.linalg.norm(v) + 1e-9)


@pytest.fixture(autouse=True)
def stub_resemblyzer(monkeypatch):
    """Sustituye `resemblyzer` por un módulo fake antes de que speaker_id lo importe."""
    fake = SimpleNamespace(
        VoiceEncoder=_FakeEncoder,
        preprocess_wav=lambda x, source_sr=None: (
            x if isinstance(x, np.ndarray) else np.ones(16000 * 6, dtype=np.float32)
        ),
    )
    monkeypatch.setitem(sys.modules, "resemblyzer", fake)
    # Resetea el encoder cacheado en speaker_id.
    from voz import speaker_id
    monkeypatch.setattr(speaker_id, "_ENCODER", None)
    yield


# ---------------- tests ----------------

def test_enroll_crea_archivo_npy(vault_temporal):
    from voz import speaker_id

    wav = np.linspace(-0.5, 0.5, 16000 * 10, dtype=np.float32)
    res = speaker_id.enroll("angel", wav)
    assert res["ok"] is True
    assert res["autor"] == "angel"
    assert res["dim"] == 256
    assert Path(res["path"]).exists()
    assert Path(res["path"]).name == "angel.npy"


def test_enroll_autor_invalido_falla(vault_temporal):
    from voz import speaker_id

    wav = np.zeros(16000 * 6, dtype=np.float32)
    with pytest.raises(ValueError):
        speaker_id.enroll("desconocido", wav)


def test_identificar_sin_enrollments_devuelve_sin_enrollment(vault_temporal):
    from voz import speaker_id

    wav = np.linspace(-0.5, 0.5, 16000 * 4, dtype=np.float32)
    res = speaker_id.identificar(wav)
    assert res.accion == "sin_enrollment"
    assert res.autor is None


def test_identificar_acepta_si_mismo_audio(vault_temporal):
    """Cosine-sim con uno mismo = 1.0 → acción 'aceptar'."""
    from voz import speaker_id

    wav_angel = np.linspace(-0.5, 0.5, 16000 * 10, dtype=np.float32)
    speaker_id.enroll("angel", wav_angel)

    # mismo wav → mismo embedding → similarity 1.0
    res = speaker_id.identificar(wav_angel)
    assert res.autor == "angel"
    assert res.similarity > 0.95
    assert res.accion == "aceptar"


def test_identificar_rechaza_audio_muy_distinto(vault_temporal):
    """Audio cuya 'firma' aleatoria da embedding ortogonal → 'rechazar'."""
    from voz import speaker_id

    wav_angel = np.full(16000 * 10, 0.1, dtype=np.float32)  # seed 1600
    speaker_id.enroll("angel", wav_angel)

    wav_otro = np.full(16000 * 10, -0.3, dtype=np.float32)  # seed distinto
    res = speaker_id.identificar(wav_otro)
    # Con embeddings aleatorios 256-d, la similarity esperada es ~0
    assert res.accion in ("rechazar", "preguntar")
    if res.accion == "rechazar":
        assert res.autor is None


def test_listar_enrolled_refleja_archivos(vault_temporal):
    from voz import speaker_id

    items = speaker_id.listar_enrolled()
    assert items == []

    wav = np.linspace(-0.5, 0.5, 16000 * 8, dtype=np.float32)
    speaker_id.enroll("africa", wav)
    items = speaker_id.listar_enrolled()
    assert len(items) == 1
    assert items[0]["autor"] == "africa"
