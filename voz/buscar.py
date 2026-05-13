"""
voz.buscar — Búsqueda full-text MVP sobre los archivos del día.

Contrato: ver specs/001-voice-assistant/contracts/mcp_tools.md (dia_buscar).
"""
from __future__ import annotations

import logging
import re
import unicodedata
from datetime import date

from .vault_io import AUTORES_VALIDOS, ETIQUETAS_VALIDAS, leer_dia, listar_dias

log = logging.getLogger("voz.buscar")


def _normalizar(s: str) -> str:
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower()


def _fragmento(texto: str, query_norm: str, original_query: str, contexto: int = 80) -> str:
    texto_norm = _normalizar(texto)
    idx = texto_norm.find(query_norm)
    if idx < 0:
        return texto[:contexto] + ("…" if len(texto) > contexto else "")
    start = max(0, idx - contexto // 2)
    end = min(len(texto), idx + len(query_norm) + contexto // 2)
    fragmento = texto[start:end]
    if start > 0:
        fragmento = "…" + fragmento
    if end < len(texto):
        fragmento = fragmento + "…"
    # Resalta en el fragmento (usando el original_query case-insensitive)
    pattern = re.compile(re.escape(original_query), re.IGNORECASE)
    fragmento = pattern.sub(lambda m: f"<mark>{m.group(0)}</mark>", fragmento)
    return fragmento


def dia_buscar_impl(
    query: str,
    desde: str = "",
    hasta: str = "",
    limite: int = 20,
    etiqueta: str = "",
    autor: str = "",
) -> dict:
    """Búsqueda en el pool común. `autor` vacío = ambos (BRIEF §14.3)."""
    query = (query or "").strip()
    if not query:
        return {"ok": False, "error": "input_vacio", "detalle": "query vacío"}
    limite = max(1, min(100, int(limite)))
    etiqueta = etiqueta.strip().lower()
    if etiqueta and etiqueta not in ETIQUETAS_VALIDAS:
        etiqueta = ""
    autor_filtro = autor.strip().lower()
    if autor_filtro and autor_filtro not in AUTORES_VALIDOS:
        autor_filtro = ""

    desde_d = None
    hasta_d = None
    try:
        if desde:
            desde_d = date.fromisoformat(desde)
        if hasta:
            hasta_d = date.fromisoformat(hasta)
    except ValueError as e:
        return {"ok": False, "error": "parametro_invalido", "detalle": f"fecha inválida: {e}"}

    query_norm = _normalizar(query)
    fechas = listar_dias(desde_d, hasta_d)
    resultados = []

    for f in fechas:
        notas = leer_dia(f)
        for n in notas:
            if etiqueta and n.etiqueta != etiqueta:
                continue
            if autor_filtro and n.autor != autor_filtro:
                continue
            if query_norm in _normalizar(n.texto):
                resultados.append({
                    "fecha": f.isoformat(),
                    "ts": n.ts,
                    "autor": n.autor,
                    "etiqueta": n.etiqueta,
                    "origen": n.origen,
                    "fragmento": _fragmento(n.texto, query_norm, query),
                })
                if len(resultados) >= limite * 5:
                    break
        if len(resultados) >= limite * 5:
            break

    resultados.sort(key=lambda r: r["ts"], reverse=True)
    return {
        "ok": True,
        "query": query,
        "filtro_autor": autor_filtro or None,
        "rango": {
            "desde": desde_d.isoformat() if desde_d else "",
            "hasta": hasta_d.isoformat() if hasta_d else "",
        },
        "total": len(resultados[:limite]),
        "resultados": resultados[:limite],
    }
