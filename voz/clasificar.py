"""
voz.clasificar — Clasificador de etiquetas con Haiku.

Lee el prompt desde el vault (editable sin redeploy) y llama a Claude Haiku
con response_format JSON. Fallback a etiqueta `otro` si timeout o error.
"""
from __future__ import annotations

import json
import logging
import os
import re
import time

import requests

from .vault_io import ETIQUETAS_VALIDAS, PROMPTS_DIR

log = logging.getLogger("voz.clasificar")

API_URL = "https://api.anthropic.com/v1/messages"
DEFAULT_MODEL = "claude-haiku-4-5"
DEFAULT_TIMEOUT_S = 3.0
PROMPT_FILE = PROMPTS_DIR / "clasificar_nota.md"


def _cargar_prompt() -> str:
    if not PROMPT_FILE.exists():
        raise FileNotFoundError(f"No existe el prompt en {PROMPT_FILE}")
    contenido = PROMPT_FILE.read_text(encoding="utf-8")
    # Quita frontmatter si está al inicio
    contenido = re.sub(r"^---\n.*?\n---\n+", "", contenido, count=1, flags=re.DOTALL)
    return contenido.strip()


def _fallback(razon: str) -> dict:
    return {"etiqueta": "otro", "confianza": 0.0, "razon": razon, "modelo": "fallback"}


def clasificar(texto: str, timeout: float = DEFAULT_TIMEOUT_S, modelo: str = DEFAULT_MODEL) -> dict:
    """Clasifica una nota y devuelve dict con etiqueta/confianza/razon/modelo.

    Hook de test: si env CLASIFICADOR_FORCE_FAIL=1, devuelve fallback sin llamar API.
    """
    texto = (texto or "").strip()
    if not texto:
        return _fallback("texto vacío")

    if os.getenv("CLASIFICADOR_FORCE_FAIL") == "1":
        return _fallback("forzado por CLASIFICADOR_FORCE_FAIL")

    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        log.warning("ANTHROPIC_API_KEY no configurada — fallback")
        return _fallback("API key ausente")

    try:
        prompt = _cargar_prompt()
    except Exception as e:
        log.error(f"Error cargando prompt: {e}")
        return _fallback("prompt no disponible")

    t0 = time.monotonic()
    try:
        r = requests.post(
            API_URL,
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            json={
                "model": modelo,
                "max_tokens": 200,
                "system": prompt,
                "messages": [{"role": "user", "content": texto}],
            },
            timeout=timeout,
        )
    except requests.RequestException as e:
        log.warning(f"timeout/error red clasificando ({time.monotonic()-t0:.2f}s): {e}")
        return _fallback(f"red: {type(e).__name__}")

    if r.status_code != 200:
        log.warning(f"Anthropic API status {r.status_code}: {r.text[:200]}")
        return _fallback(f"status {r.status_code}")

    try:
        data = r.json()
        content = data["content"][0]["text"].strip()
        # Limpia code-fence si Haiku lo metió
        content = re.sub(r"^```(?:json)?\s*|\s*```$", "", content, flags=re.DOTALL).strip()
        parsed = json.loads(content)
        etiqueta = parsed.get("etiqueta", "otro")
        if etiqueta not in ETIQUETAS_VALIDAS:
            etiqueta = "otro"
        confianza = float(parsed.get("confianza", 0.0))
        confianza = max(0.0, min(1.0, confianza))
        razon = str(parsed.get("razon", ""))[:120]
        return {"etiqueta": etiqueta, "confianza": confianza, "razon": razon, "modelo": modelo}
    except (json.JSONDecodeError, KeyError, ValueError, TypeError) as e:
        log.warning(f"Respuesta no parseable: {e} — body={r.text[:200]}")
        return _fallback(f"parse: {type(e).__name__}")
