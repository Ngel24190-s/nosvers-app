"""
voz.intent_router — Decide qué tool MCP ejecutar para un texto dictado.

Patrón: igual que `voz.clasificar`. Llama a Claude Haiku con un prompt
editable en el vault (`prompts/intent_router.md`) y parsea JSON.

Si timeout, error de red, JSON corrupto, confidence < threshold o tool
fuera del whitelist → fallback a `dia_capturar` (nota normal).

Hook de test: env `INTENT_ROUTER_FORCE_FAIL=1` devuelve fallback sin red.

Idempotencia: cache LRU en memoria, 64 entradas, TTL 5 s, key
`(sha256(text)[:16], autor)`.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import re
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from pathlib import Path

import requests

log = logging.getLogger("voz.intent_router")

API_URL = "https://api.anthropic.com/v1/messages"
DEFAULT_MODEL = "claude-haiku-4-5"
DEFAULT_TIMEOUT_S = 3.0
DEFAULT_THRESHOLD = 0.6
PROMPT_FILE = Path(
    os.getenv(
        "INTENT_ROUTER_PROMPT",
        "/home/nosvers/public_html/knowledge_base/prompts/intent_router.md",
    )
)

# Whitelist de tools que el router puede devolver.
ALLOWED_TOOLS: set[str] = {
    # claudio identidad
    "claudio_recordar", "claudio_contexto",
    # familia
    "recordatorio_crear", "recordatorios_listar", "recordatorio_completar",
    "familia_cumpleanos_listar",
    # finanzas
    "gasto_anotar", "gastos_resumen", "recurrente_alertar",
    # compras
    "lista_compras_añadir", "lista_compras_anadir",
    "lista_compras_ver", "lista_compras_completar", "despensa_estado",
    # menús
    "menu_sugerir", "receta_guardar",
    # coche
    "coche_estado", "coche_evento",
    # documentos
    "documento_anotar", "documentos_buscar",
    # salud
    "medicacion_recordar", "cita_medica_anotar",
    # casa
    "casa_mantenimiento_anotar",
    # fallback / capturas libres
    "dia_capturar", "dia_buscar",
}


@dataclass
class IntentResult:
    tool: str
    args: dict
    confidence: float
    fallback: bool
    razon: str
    modelo: str
    cached: bool = False
    raw: dict | None = field(default=None, repr=False)


# ─── Prompt loading ──────────────────────────────────────────────

_FALLBACK_PROMPT = (
    "Eres el router de intents de Claudio. Devuelve EXCLUSIVAMENTE un JSON "
    '{"tool": "<nombre>", "args": {...}, "confidence": <0..1>, "razon": "..."}. '
    "Si el dictado es ambiguo, usa tool=dia_capturar con confidence<0.6."
)


def _load_prompt() -> str:
    """Carga el prompt del vault, quitando frontmatter. Fallback si no existe."""
    try:
        if not PROMPT_FILE.exists():
            log.warning(f"prompt no existe en {PROMPT_FILE}, uso fallback")
            return _FALLBACK_PROMPT
        text = PROMPT_FILE.read_text(encoding="utf-8")
        text = re.sub(r"^---\n.*?\n---\n+", "", text, count=1, flags=re.DOTALL)
        return text.strip() or _FALLBACK_PROMPT
    except Exception as e:
        log.warning(f"error leyendo prompt: {e}")
        return _FALLBACK_PROMPT


# ─── Idempotency cache ───────────────────────────────────────────

_CACHE_MAX = 64
_CACHE_TTL_S = 5.0
_cache: "OrderedDict[tuple[str, str], tuple[float, IntentResult]]" = OrderedDict()


def _cache_key(text: str, autor: str) -> tuple[str, str]:
    h = hashlib.sha256(text.strip().lower().encode("utf-8")).hexdigest()[:16]
    return (h, autor)


def _cache_get(text: str, autor: str) -> IntentResult | None:
    key = _cache_key(text, autor)
    item = _cache.get(key)
    if item is None:
        return None
    ts, result = item
    if (time.monotonic() - ts) > _CACHE_TTL_S:
        # expired
        _cache.pop(key, None)
        return None
    # mark recent
    _cache.move_to_end(key)
    # devolvemos una copia con cached=True para que el caller sepa
    return IntentResult(
        tool=result.tool,
        args=dict(result.args),
        confidence=result.confidence,
        fallback=result.fallback,
        razon=result.razon,
        modelo=result.modelo,
        cached=True,
        raw=result.raw,
    )


def _cache_set(text: str, autor: str, result: IntentResult) -> None:
    key = _cache_key(text, autor)
    _cache[key] = (time.monotonic(), result)
    _cache.move_to_end(key)
    while len(_cache) > _CACHE_MAX:
        _cache.popitem(last=False)


def clear_cache() -> None:
    """Para tests."""
    _cache.clear()


# ─── Fallback constructor ────────────────────────────────────────

def _fallback(text: str, razon: str, modelo: str = "fallback") -> IntentResult:
    return IntentResult(
        tool="dia_capturar",
        args={"texto": text},
        confidence=0.3,
        fallback=True,
        razon=razon,
        modelo=modelo,
    )


# ─── API Anthropic ───────────────────────────────────────────────

def _post_haiku(
    prompt: str,
    user_text: str,
    autor: str,
    *,
    timeout: float,
    modelo: str,
) -> dict | None:
    """Devuelve dict parseado del modelo, o None si error/timeout."""
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        log.warning("ANTHROPIC_API_KEY no configurada — fallback")
        return None
    payload = {
        "model": modelo,
        "max_tokens": 300,
        "system": prompt,
        "messages": [
            {
                "role": "user",
                "content": f"Autor: {autor}\nDictado: {user_text}",
            }
        ],
    }
    try:
        r = requests.post(
            API_URL,
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=timeout,
        )
    except requests.RequestException as e:
        log.warning(f"red error: {type(e).__name__}")
        return None
    if r.status_code != 200:
        log.warning(f"status {r.status_code}: {r.text[:200]}")
        return None
    try:
        data = r.json()
        content = data["content"][0]["text"].strip()
        # Quita code fences si están presentes (al principio o intercalados)
        content = re.sub(
            r"```(?:json)?\s*", "", content, flags=re.IGNORECASE
        )
        content = content.replace("```", "").strip()
        # Extrae el primer objeto JSON balanceado (tolera texto antes/después)
        obj = _extract_first_json_object(content)
        if obj is None:
            log.warning(f"no JSON balanceado en body={r.text[:200]}")
            return None
        return json.loads(obj)
    except (json.JSONDecodeError, KeyError, ValueError, TypeError) as e:
        log.warning(f"parse error: {e} body={r.text[:200] if 'r' in locals() else '?'}")
        return None


def _extract_first_json_object(s: str) -> str | None:
    """Devuelve la primera substring que es un JSON object balanceado."""
    start = s.find("{")
    if start < 0:
        return None
    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(s)):
        ch = s[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return s[start:i + 1]
    return None


# ─── route_intent (public) ───────────────────────────────────────

async def route_intent(
    text: str,
    autor: str,
    *,
    threshold: float = DEFAULT_THRESHOLD,
    timeout: float = DEFAULT_TIMEOUT_S,
    modelo: str = DEFAULT_MODEL,
) -> IntentResult:
    """Decide qué tool ejecutar para un texto dictado.

    Args:
        text: transcript completo.
        autor: 'angel' | 'africa' (viene del JWT, no del cliente).
        threshold: confidence mínima para no caer al fallback.
        timeout: segundos antes de fallback por red.
        modelo: model id de Anthropic.
    """
    text = (text or "").strip()
    if not text:
        return _fallback("", "texto vacío")

    cached = _cache_get(text, autor)
    if cached is not None:
        return cached

    if os.getenv("INTENT_ROUTER_FORCE_FAIL") == "1":
        result = _fallback(text, "forzado por env")
        _cache_set(text, autor, result)
        return result

    prompt = _load_prompt()
    # _post_haiku es bloqueante (requests) — lo ejecutamos en thread para no
    # bloquear el event loop del endpoint
    parsed = await asyncio.to_thread(
        _post_haiku, prompt, text, autor, timeout=timeout, modelo=modelo
    )
    if parsed is None:
        result = _fallback(text, "red o parse")
        _cache_set(text, autor, result)
        return result

    tool = str(parsed.get("tool") or "").strip()
    args = parsed.get("args") if isinstance(parsed.get("args"), dict) else {}
    try:
        confidence = float(parsed.get("confidence", 0.0))
    except (TypeError, ValueError):
        confidence = 0.0
    confidence = max(0.0, min(1.0, confidence))
    razon = str(parsed.get("razon") or "")[:120]

    # Normalizar alias ASCII
    if tool == "lista_compras_anadir":
        tool = "lista_compras_añadir"

    if tool not in ALLOWED_TOOLS:
        result = _fallback(text, f"tool fuera de whitelist: {tool!r}", modelo)
        result.raw = parsed
        _cache_set(text, autor, result)
        return result

    if confidence < threshold and tool != "dia_capturar":
        # Confidence baja con tool no-capturar → fallback a captura
        result = _fallback(text, f"confidence {confidence:.2f} < {threshold}", modelo)
        result.raw = parsed
        _cache_set(text, autor, result)
        return result

    # Sanitiza args: quita autor si el modelo lo incluyó (lo inyecta el server)
    args.pop("autor", None)

    result = IntentResult(
        tool=tool,
        args=args,
        confidence=confidence,
        fallback=(tool == "dia_capturar"),
        razon=razon,
        modelo=modelo,
        raw=parsed,
    )
    _cache_set(text, autor, result)
    return result
