"""
voz.contexto — Síntesis sintética del contexto reciente.

Contrato: ver specs/001-voice-assistant/contracts/mcp_tools.md (dia_contexto).
"""
from __future__ import annotations

import logging
import os
import time
from datetime import date, datetime, timedelta
from threading import Lock

import requests

from .vault_io import AUTORES_VALIDOS, ETIQUETAS_VALIDAS, leer_dia, listar_dias

log = logging.getLogger("voz.contexto")

API_URL = "https://api.anthropic.com/v1/messages"
DEFAULT_MODEL = "claude-sonnet-4-6"
CACHE_TTL_S = 300

_CACHE: dict[tuple, tuple[float, dict]] = {}
_CACHE_LOCK = Lock()


def _cache_get(key: tuple) -> dict | None:
    with _CACHE_LOCK:
        item = _CACHE.get(key)
        if not item:
            return None
        ts, res = item
        if time.monotonic() - ts > CACHE_TTL_S:
            del _CACHE[key]
            return None
        return res


def _cache_set(key: tuple, resultado: dict) -> None:
    with _CACHE_LOCK:
        _CACHE[key] = (time.monotonic(), resultado)
        if len(_CACHE) > 50:
            # evict oldest
            oldest = min(_CACHE.items(), key=lambda kv: kv[1][0])
            del _CACHE[oldest[0]]


def _formatear_notas_para_sintesis(
    fechas: list[date],
    etiquetas_filtro: set[str] | None,
    autor_filtro: str | None,
) -> tuple[str, int]:
    bloques: list[str] = []
    total = 0
    for f in fechas:
        notas = leer_dia(f)
        if etiquetas_filtro:
            notas = [n for n in notas if n.etiqueta in etiquetas_filtro]
        if autor_filtro:
            notas = [n for n in notas if n.autor == autor_filtro]
        if not notas:
            continue
        bloques.append(f"## {f.isoformat()}\n")
        for n in notas:
            bloques.append(f"- [{n.autor}/{n.etiqueta}] {n.ts[:19]} — {n.texto.strip()}")
        bloques.append("")
        total += len(notas)
    return "\n".join(bloques), total


def _llamar_sintesis(material: str, modelo: str = DEFAULT_MODEL) -> str:
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        return "_(síntesis no disponible — falta ANTHROPIC_API_KEY)_"
    system = (
        "Eres el segundo cerebro de Angel y África (NosVers). Recibes notas brutas\n"
        "de su diario común. Cada nota lleva prefijo [autor/etiqueta]. Devuelve una\n"
        "síntesis en castellano, máximo 800 palabras, formato markdown con secciones:\n"
        "'Hilos principales (Angel)', 'Hilos principales (África)', 'Cruce / decisiones\n"
        "conjuntas', 'Pendientes detectados', 'Tono general'. Si una sección está\n"
        "vacía, omítela. Sin saludos. Directo. No inventes."
    )
    try:
        r = requests.post(
            API_URL,
            headers={"x-api-key": api_key, "anthropic-version": "2023-06-01",
                     "Content-Type": "application/json"},
            json={"model": modelo, "max_tokens": 1500, "system": system,
                  "messages": [{"role": "user", "content": material}]},
            timeout=30,
        )
        if r.status_code != 200:
            log.warning(f"Síntesis status {r.status_code}: {r.text[:200]}")
            return f"_(error API: {r.status_code})_"
        return r.json()["content"][0]["text"].strip()
    except requests.RequestException as e:
        log.error(f"Síntesis red error: {e}")
        return f"_(error red: {type(e).__name__})_"


def _leer_calendario() -> list[dict] | str:
    """Intenta leer eventos próximos del calendario. Retorna 'no_disponible' si falla."""
    # MVP: stub. La integración real depende del helper del proyecto.
    # TODO: integrar con tool MCP de Google Calendar cuando esté disponible.
    return "no_disponible"


def _leer_estado_agentes() -> str | None:
    """Intenta leer un resumen del estado de los agentes."""
    try:
        # Reusa la lógica que ya tiene mcp_server.agentes_estado(): listar logs recientes.
        from pathlib import Path
        log_dir = Path("/home/nosvers/logs")
        if not log_dir.exists():
            return None
        recientes = sorted(log_dir.glob("agt*.log"), key=lambda p: p.stat().st_mtime, reverse=True)[:8]
        lineas = []
        for fp in recientes:
            try:
                mtime = datetime.fromtimestamp(fp.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
                lineas.append(f"- {fp.stem}: {mtime}")
            except OSError:
                continue
        return "\n".join(lineas) if lineas else None
    except Exception:
        return None


def dia_contexto_impl(
    rango_dias: int = 7,
    incluir_calendario: bool = True,
    incluir_estado_agentes: bool = True,
    etiquetas_filtro: str = "",
    autor: str = "",
) -> dict:
    """Síntesis del contexto reciente.

    `autor` (BRIEF §14): vacío = ambos. "angel" o "africa" para filtrar.
    """
    rango_dias = max(1, min(30, int(rango_dias)))
    etiquetas_set = None
    if etiquetas_filtro:
        items = [s.strip().lower() for s in etiquetas_filtro.split(",") if s.strip()]
        etiquetas_set = {e for e in items if e in ETIQUETAS_VALIDAS}
        if not etiquetas_set:
            etiquetas_set = None
    autor_filtro = autor.strip().lower()
    if autor_filtro and autor_filtro not in AUTORES_VALIDOS:
        autor_filtro = ""

    cache_key = (rango_dias, incluir_calendario, incluir_estado_agentes,
                 tuple(sorted(etiquetas_set)) if etiquetas_set else None,
                 autor_filtro or None)
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached | {"cache": True}

    hasta = date.today()
    desde = hasta - timedelta(days=rango_dias - 1)
    fechas = listar_dias(desde, hasta)

    material, notas_count = _formatear_notas_para_sintesis(fechas, etiquetas_set, autor_filtro or None)
    sintesis = _llamar_sintesis(material) if material else "_(sin actividad en el rango pedido — amplía el rango_dias)_"

    calendario = _leer_calendario() if incluir_calendario else None
    agentes = _leer_estado_agentes() if incluir_estado_agentes else None

    resultado = {
        "ok": True,
        "rango": {"desde": desde.isoformat(), "hasta": hasta.isoformat()},
        "filtro_autor": autor_filtro or None,
        "notas_count": notas_count,
        "sintesis": sintesis,
        "calendario": calendario,
        "agentes": agentes,
    }
    _cache_set(cache_key, resultado)
    return resultado
