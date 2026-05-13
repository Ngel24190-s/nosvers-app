"""Parser de comandos por voz. Aislado de las deps pesadas (sounddevice,
faster-whisper, kokoro) para poder testearse en cualquier entorno.
"""

from __future__ import annotations

import re

_RE_RAPIDO    = re.compile(r"\b(habla|m[áa]s)\s+(m[áa]s\s+)?r[aá]pid", re.I)
_RE_DESPACIO  = re.compile(r"\b(habla|m[áa]s)\s+(m[áa]s\s+)?(despacio|lent)", re.I)
_RE_FRANCES   = re.compile(r"\b(cambia|pasa)?\s*a\s*franc[eé]s\b", re.I)
_RE_CASTELLANO = re.compile(r"\b(cambia|pasa)?\s*a\s*(castellano|espa[ñn]ol)\b", re.I)
_RE_CIERRA    = re.compile(r"\b(cierra|cierra\s+la|termina)\s+(la\s+)?sesi[oó]n\b", re.I)
_RE_CAPTURA   = re.compile(r"^\s*(captura|anota|toma\s+nota)\s*[:,]?\s*(.+)$", re.I)


def parse_comando(texto: str) -> tuple[str, str | None]:
    """Clasifica el texto en uno de los comandos o 'chat'.

    Devuelve (tipo, payload). Tipos: rapido | despacio | fr | es | cierra |
    captura | chat. Payload sólo aplica a 'captura'.
    """
    if _RE_CIERRA.search(texto):
        return ("cierra", None)
    if _RE_RAPIDO.search(texto):
        return ("rapido", None)
    if _RE_DESPACIO.search(texto):
        return ("despacio", None)
    if _RE_FRANCES.search(texto):
        return ("fr", None)
    if _RE_CASTELLANO.search(texto):
        return ("es", None)
    m = _RE_CAPTURA.match(texto)
    if m:
        return ("captura", m.group(2).strip())
    return ("chat", texto.strip())
