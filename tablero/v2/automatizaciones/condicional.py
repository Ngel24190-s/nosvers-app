"""Evaluador DSL para nodo Condicional.

Formato: `<lhs> <op> <rhs>` donde:
- lhs: literal o {{var}}  (resuelto con interpolation.resolve)
- op: > < >= <= == != contains matches
- rhs: literal numérico, "string" entre comillas, true/false, o {{var}}

Sin eval/exec/ast. Parsing con regex y matching explícito.
"""
from __future__ import annotations

import re
from typing import Any

from tablero.v2.automatizaciones.interpolation import resolve

_OP_PATTERN = r"(>=|<=|==|!=|>|<|contains|matches)"
_EXPR_RE = re.compile(rf"^\s*(.+?)\s+{_OP_PATTERN}\s+(.+?)\s*$")


def _coerce_literal(s: str) -> Any:
    s = s.strip()
    if s.startswith('"') and s.endswith('"'):
        return s[1:-1]
    if s.startswith("'") and s.endswith("'"):
        return s[1:-1]
    if s.lower() == "true":
        return True
    if s.lower() == "false":
        return False
    if s.lower() in {"null", "none"}:
        return None
    try:
        if "." in s:
            return float(s)
        return int(s)
    except ValueError:
        return s


def evaluar(expresion: str, ctx: dict[str, Any]) -> bool:
    """Evalúa una expresión simple. Devuelve bool.

    Lanza ValueError si la expresión no cuadra con el patrón.
    """
    if not isinstance(expresion, str):
        raise ValueError("expresion debe ser str")
    if len(expresion) > 500:
        raise ValueError("expresion demasiado larga")

    # 1. Resolver {{vars}} primero
    resuelto = resolve(expresion, ctx)

    # 2. Parsear lhs OP rhs
    m = _EXPR_RE.match(resuelto)
    if not m:
        raise ValueError(f"expresion no parseable: {resuelto!r}")
    lhs_s, op, rhs_s = m.group(1), m.group(2), m.group(3)
    lhs = _coerce_literal(lhs_s)
    rhs = _coerce_literal(rhs_s)

    if op == "==":
        return lhs == rhs
    if op == "!=":
        return lhs != rhs
    if op == "contains":
        return str(rhs) in str(lhs)
    if op == "matches":
        try:
            return bool(re.search(str(rhs), str(lhs)))
        except re.error:
            return False
    # comparadores numéricos
    try:
        l = float(lhs)
        r = float(rhs)
    except (TypeError, ValueError):
        # Para strings, comparación lexicográfica
        l, r = str(lhs), str(rhs)
    if op == ">":
        return l > r
    if op == "<":
        return l < r
    if op == ">=":
        return l >= r
    if op == "<=":
        return l <= r
    raise ValueError(f"operador desconocido: {op}")
