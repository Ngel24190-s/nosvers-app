"""
Fixtures compartidas para tests del módulo `voz/`.

Redirige paths del vault y la base de datos de tokens a `tmp_path` para
aislar completamente cada test del estado de producción del VPS.

T002 (parcial completado por esta conftest).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

# Asegúrate de que `import voz` funciona aunque pytest se llame fuera de /home/nosvers
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture(autouse=True)
def voz_jwt_secret(monkeypatch):
    """Inyecta un secret JWT determinista para todos los tests."""
    monkeypatch.setenv("VOZ_JWT_SECRET", "test-secret-only-for-pytest-do-not-use-in-prod")


@pytest.fixture
def vault_temporal(monkeypatch, tmp_path):
    """Redirige TODA la I/O del vault a tmp_path.

    Pool común multi-usuario (BRIEF §14): estructura plana
    ``base/dia/``, ``base/dia/audio/``, ``base/dia/resumenes/``,
    ``base/prompts/``, ``base/system/speakers/`` (sin ``/angel/`` segmentado).
    """
    base = tmp_path / "knowledge_base"
    dia = base / "dia"
    audio = dia / "audio"
    resumenes = dia / "resumenes"
    prompts = base / "prompts"
    speakers = base / "system" / "speakers"
    for d in (dia, audio, resumenes, prompts, speakers):
        d.mkdir(parents=True, exist_ok=True)

    real_prompt = Path("/home/nosvers/public_html/knowledge_base/prompts/clasificar_nota.md")
    if real_prompt.exists():
        (prompts / "clasificar_nota.md").write_bytes(real_prompt.read_bytes())
    else:
        (prompts / "clasificar_nota.md").write_text(
            "# Prompt clasificar (test stub)\n", encoding="utf-8"
        )

    from voz import vault_io
    monkeypatch.setattr(vault_io, "VAULT_BASE", base)
    monkeypatch.setattr(vault_io, "DIA_DIR", dia)
    monkeypatch.setattr(vault_io, "AUDIO_DIR", audio)
    monkeypatch.setattr(vault_io, "RESUMENES_DIR", resumenes)
    monkeypatch.setattr(vault_io, "PROMPTS_DIR", prompts)
    monkeypatch.setattr(vault_io, "SYSTEM_DIR", base / "system")
    monkeypatch.setattr(vault_io, "SPEAKERS_DIR", speakers)

    # capturar.py importó DIA_DIR y VAULT_BASE — override referencias locales
    try:
        from voz import capturar
        if hasattr(capturar, "DIA_DIR"):
            monkeypatch.setattr(capturar, "DIA_DIR", dia)
        if hasattr(capturar, "VAULT_BASE"):
            monkeypatch.setattr(capturar, "VAULT_BASE", base)
    except ImportError:
        pass

    # clasificar.py importó PROMPTS_DIR; reconstruye PROMPT_FILE
    try:
        from voz import clasificar as _clasif
        monkeypatch.setattr(_clasif, "PROMPT_FILE", prompts / "clasificar_nota.md")
    except ImportError:
        pass

    # buscar y contexto pueden referenciar DIA_DIR localmente
    for mod_name in ("buscar", "contexto"):
        try:
            mod = __import__(f"voz.{mod_name}", fromlist=[mod_name])
            for cname in ("DIA_DIR", "AUDIO_DIR"):
                if hasattr(mod, cname):
                    monkeypatch.setattr(mod, cname, dia if cname == "DIA_DIR" else audio)
        except ImportError:
            pass

    class Vault:
        pass
    v = Vault()
    v.base = base
    v.dia = dia
    v.audio = audio
    v.resumenes = resumenes
    v.prompts = prompts
    v.speakers = speakers
    return v


@pytest.fixture
def auth_temporal(monkeypatch, tmp_path):
    """Redirige la SQLite de tokens a tmp_path."""
    from voz import auth
    test_dir = tmp_path / "voz-data"
    test_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(auth, "DATA_DIR", test_dir)
    monkeypatch.setattr(auth, "DB_PATH", test_dir / "tokens.sqlite")
    return test_dir / "tokens.sqlite"


@pytest.fixture
def clasif_off(monkeypatch):
    """Fuerza fallback de clasificador (etiqueta='otro') sin llamar API."""
    monkeypatch.setenv("CLASIFICADOR_FORCE_FAIL", "1")


@pytest.fixture
def clean_idem_cache():
    """Limpia el cache LRU de idempotencia entre tests."""
    from voz.capturar import _IDEM_CACHE, _IDEM_LOCK
    with _IDEM_LOCK:
        _IDEM_CACHE.clear()
    yield
    with _IDEM_LOCK:
        _IDEM_CACHE.clear()


@pytest.fixture
def token_de_prueba(auth_temporal):
    """Emite un token y devuelve (jwt_string, jti, device_label)."""
    from voz import auth
    res = auth.emitir_token("test-device", ttl_days=1)
    return res["jwt"], res["jti"], "test-device"
