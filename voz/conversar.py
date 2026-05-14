"""
voz.conversar — Modo conversación libre. Cuando el intent_router NO
encuentra una tool concreta y el texto NO parece comando, llama a
Claude Haiku con system prompt contextual y devuelve respuesta natural.

Mantiene historial conversacional en memoria por (autor, contexto):
últimos 8 turnos (4 user + 4 assistant). Caduca a los 10 minutos.
"""
from __future__ import annotations

import logging
import os
import time
from collections import deque

import requests

log = logging.getLogger("voz.conversar")

API_URL = "https://api.anthropic.com/v1/messages"
MODEL = os.getenv("VOZ_CONVERSAR_MODEL", "claude-haiku-4-5")
MAX_TOKENS = 220
TIMEOUT_S = 6.0
HISTORY_TURNS = 8
HISTORY_TTL_S = 600

_HISTORY: dict[tuple[str, str], tuple[float, deque]] = {}

SYSTEM_BASE = (
    "Eres Claudio, asistente familiar de Angel y África. Responde SIEMPRE "
    "muy breve (1-3 frases, máximo 30 palabras). Tono cálido pero directo, "
    "sin floritura. Hablas español castellano peninsular SIEMPRE. "
    "Bris es el perro boxer de la familia.\n\n"
)

SYSTEM_BY_CONTEXT = {
    "casa": (
        "Contexto activo: CASA (vida familiar, gastos, salud, recados, hogar). "
        "Si Angel/África te saludan, responde con un saludo breve y pregunta "
        "qué necesitan. Si te preguntan algo personal, responde como "
        "alguien que les conoce bien."
    ),
    "nosvers": (
        "Contexto activo: NOSVERS (granja agroecológica en Neuvic-sur-l'Isle, "
        "Dordogne; vermicultura; productos: Guide du Sol Vivant, Club Sol Vivant, "
        "lombrices Dendrobaena para AAPPMA pesca). Habla con criterio técnico "
        "agroecológico pero sin tecnicismos innecesarios."
    ),
    "trabajo": (
        "Contexto activo: TRABAJO (DI Environnement Sud Ouest, désamiantage). "
        "Angel es Conducteur de travaux. Términos clave: chantier, PPSPS, "
        "plan de retrait, devis, équipe, désamiantage, déplombage, "
        "décontamination, décapage UHP. Puedes mezclar español y términos "
        "técnicos en francés."
    ),
}


def _history_key(autor: str, contexto: str) -> tuple[str, str]:
    return (autor or "angel", contexto or "casa")


def _get_history(autor: str, contexto: str) -> list[dict]:
    key = _history_key(autor, contexto)
    entry = _HISTORY.get(key)
    if not entry:
        return []
    last_ts, msgs = entry
    if time.monotonic() - last_ts > HISTORY_TTL_S:
        _HISTORY.pop(key, None)
        return []
    return list(msgs)


def _push_history(autor: str, contexto: str, user_text: str, assistant_text: str) -> None:
    key = _history_key(autor, contexto)
    entry = _HISTORY.get(key)
    if not entry:
        msgs = deque(maxlen=HISTORY_TURNS * 2)
    else:
        _, msgs = entry
    msgs.append({"role": "user", "content": user_text})
    msgs.append({"role": "assistant", "content": assistant_text})
    _HISTORY[key] = (time.monotonic(), msgs)


def conversar(texto: str, autor: str = "angel", contexto: str = "casa") -> dict:
    """Conversación libre con Claudio. Devuelve {ok, texto, model, latency_ms}."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return {"ok": False, "error": "anthropic_key_missing",
                "texto": "Lo siento, no puedo conversar ahora mismo."}

    system = SYSTEM_BASE + SYSTEM_BY_CONTEXT.get(contexto, SYSTEM_BY_CONTEXT["casa"])
    messages = _get_history(autor, contexto)
    messages.append({"role": "user", "content": texto})

    t0 = time.monotonic()
    try:
        r = requests.post(
            API_URL,
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": MODEL,
                "max_tokens": MAX_TOKENS,
                "system": system,
                "messages": messages,
            },
            timeout=TIMEOUT_S,
        )
        r.raise_for_status()
        data = r.json()
        reply = (data.get("content") or [{}])[0].get("text", "").strip()
    except requests.Timeout:
        return {"ok": False, "error": "timeout",
                "texto": "Tardé demasiado, prueba otra vez."}
    except Exception as e:
        log.exception(f"conversar error: {e}")
        return {"ok": False, "error": "api_error",
                "texto": "Algo ha fallado, prueba otra vez."}

    if not reply:
        return {"ok": False, "error": "empty_reply",
                "texto": "No supe qué decir, repite por favor."}

    _push_history(autor, contexto, texto, reply)
    return {
        "ok": True,
        "texto": reply,
        "model": MODEL,
        "latency_ms": int((time.monotonic() - t0) * 1000),
    }
