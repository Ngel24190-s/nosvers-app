"""
Tests para voz.stt — Transcripción con faster-whisper.

T016: validamos la API (`transcribir`), el manejo de path/bytes, y la
lectura de env vars, sin descargar el modelo real (~480MB).

El test E2E con un WAV de fixture queda diferido a un job de integración
manual; aquí mockeamos `WhisperModel` para asegurar el contrato del módulo.
"""
from __future__ import annotations

import importlib
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock

import pytest


class FakeSegment:
    def __init__(self, text: str):
        self.text = text


class FakeInfo:
    def __init__(self, language: str = "es", duration: float = 1.23):
        self.language = language
        self.duration = duration


class FakeWhisperModel:
    instances = []

    def __init__(self, name, device, compute_type):
        self.name = name
        self.device = device
        self.compute_type = compute_type
        type(self).instances.append(self)

    def transcribe(self, audio, language=None, beam_size=5):
        # Simula un único segmento.
        if language == "fr":
            return iter([FakeSegment("Bonjour le sol vivant. ")]), FakeInfo("fr", 0.8)
        return iter([FakeSegment("Hola mundo. ")]), FakeInfo("es", 1.23)


@pytest.fixture
def stub_faster_whisper(monkeypatch):
    """Inserta un módulo fake `faster_whisper` y resetea el caché del modelo."""
    fake_mod = types.ModuleType("faster_whisper")
    fake_mod.WhisperModel = FakeWhisperModel
    monkeypatch.setitem(sys.modules, "faster_whisper", fake_mod)
    FakeWhisperModel.instances.clear()

    # Recargar voz.stt para que _MODEL = None empiece limpio.
    from voz import stt
    monkeypatch.setattr(stt, "_MODEL", None)
    return stt


def test_transcribir_path(stub_faster_whisper, tmp_path):
    stt = stub_faster_whisper
    audio = tmp_path / "nota.wav"
    audio.write_bytes(b"RIFF\x00\x00\x00\x00WAVEfmt ")
    res = stt.transcribir(audio)
    assert isinstance(res, dict)
    assert res["texto"] == "Hola mundo."
    assert res["idioma_detectado"] == "es"
    assert res["duracion"] == pytest.approx(1.23)


def test_transcribir_bytes(stub_faster_whisper):
    stt = stub_faster_whisper
    audio_bytes = b"OggS" + b"\x00" * 64
    res = stt.transcribir(audio_bytes)
    assert res["texto"] == "Hola mundo."
    assert res["idioma_detectado"] == "es"


def test_transcribir_idioma_forzado(stub_faster_whisper, tmp_path):
    stt = stub_faster_whisper
    audio = tmp_path / "fr.wav"
    audio.write_bytes(b"RIFF\x00\x00\x00\x00WAVEfmt ")
    res = stt.transcribir(audio, idioma="fr")
    assert res["idioma_detectado"] == "fr"
    assert "Bonjour" in res["texto"]


def test_model_singleton_caché(stub_faster_whisper, tmp_path):
    """Segunda llamada NO instancia un segundo WhisperModel."""
    stt = stub_faster_whisper
    audio = tmp_path / "a.wav"
    audio.write_bytes(b"RIFF")
    stt.transcribir(audio)
    stt.transcribir(audio)
    assert len(FakeWhisperModel.instances) == 1


def test_env_vars_respetadas(stub_faster_whisper, monkeypatch, tmp_path):
    monkeypatch.setenv("VOZ_STT_MODEL", "tiny")
    monkeypatch.setenv("VOZ_STT_DEVICE", "cpu")
    monkeypatch.setenv("VOZ_STT_COMPUTE", "int8")
    stt = stub_faster_whisper
    audio = tmp_path / "a.wav"
    audio.write_bytes(b"RIFF")
    stt.transcribir(audio)
    assert FakeWhisperModel.instances[0].name == "tiny"
    assert FakeWhisperModel.instances[0].compute_type == "int8"


def test_import_error_propaga(monkeypatch):
    """Si faster-whisper no está disponible, lanza RuntimeError descriptivo."""
    # Forzar ImportError quitando el módulo fake si existiera.
    monkeypatch.delitem(sys.modules, "faster_whisper", raising=False)
    # Asegurarnos de que importar realmente falla bloqueando el path real
    import builtins
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "faster_whisper":
            raise ImportError("simulado")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    from voz import stt
    monkeypatch.setattr(stt, "_MODEL", None)
    with pytest.raises(RuntimeError, match="faster-whisper no está instalado"):
        stt.transcribir(b"\x00\x00\x00\x00")
