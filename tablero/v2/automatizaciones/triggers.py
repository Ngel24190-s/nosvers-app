"""Adaptadores de triggers: matching de filtros sobre eventos WS / cron.

Cada función `matches_<tipo>` devuelve `(matched: bool, payload_normalizado: dict)`.
"""
from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Any

log = logging.getLogger("tablero.v2.automatizaciones.triggers")


def _regex_ok(pattern: str | None, value: Any) -> bool:
    if not pattern:
        return True
    try:
        return bool(re.search(pattern, str(value or "")))
    except re.error:
        return False


def matches_nota_capturada(filtros: dict, event: dict) -> tuple[bool, dict]:
    """event esperado: payload del canal `activity` con un item de nota.

    El worker `activity` publica items con shape variable; aceptamos:
    {autor, etiqueta, texto/cuerpo, fecha, slug}.
    """
    if filtros.get("autor") and event.get("autor") != filtros["autor"]:
        return False, event
    if filtros.get("etiqueta") and event.get("etiqueta") != filtros["etiqueta"]:
        return False, event
    if not _regex_ok(filtros.get("contenido_regex"), event.get("texto") or event.get("cuerpo")):
        return False, event
    return True, event


def matches_agente_terminado(filtros: dict, event: dict) -> tuple[bool, dict]:
    if filtros.get("nombre_agente") and event.get("nombre") != filtros["nombre_agente"]:
        return False, event
    estado = filtros.get("estado")
    if estado and estado != "*" and event.get("estado") != estado:
        return False, event
    return True, event


def matches_aegis_alerta(filtros: dict, event: dict) -> tuple[bool, dict]:
    severidad = filtros.get("severidad")
    if severidad and event.get("severidad") != severidad:
        return False, event
    return True, event


def matches_voz_keyword(keywords: list[str], event: dict) -> tuple[bool, dict]:
    if event.get("origen") and event.get("origen") != "voz":
        return False, event
    texto = (event.get("texto") or event.get("cuerpo") or "").lower()
    for kw in keywords:
        if kw.lower() in texto:
            return True, event
    return False, event


def matches_vps_threshold(
    metrica: str, umbral_pct: float, comparador: str, event: dict
) -> tuple[bool, dict]:
    val = None
    if metrica == "cpu":
        val = event.get("cpu_pct")
    elif metrica == "ram":
        val = event.get("ram_pct") or event.get("memory_pct")
    elif metrica == "disk":
        val = event.get("disk_pct")
    if val is None:
        return False, event
    try:
        v = float(val)
    except (TypeError, ValueError):
        return False, event
    if comparador == "gt":
        return v > umbral_pct, event
    return v < umbral_pct, event


def matches_webhook_stripe(evento_esperado: str, filtros: dict, payload: dict) -> tuple[bool, dict]:
    if payload.get("type") and payload["type"] != evento_esperado:
        return False, payload
    # extraer amount de Stripe (en céntimos)
    obj = payload.get("data", {}).get("object", {}) if isinstance(payload.get("data"), dict) else {}
    amount_cents = obj.get("amount") or obj.get("amount_received") or 0
    amount_eur = float(amount_cents) / 100.0
    customer = obj.get("customer_email") or obj.get("receipt_email") or obj.get("customer") or ""
    flat = {"amount": amount_eur, "customer": customer, "raw": payload}
    if filtros.get("amount_gte_eur") is not None:
        if amount_eur < float(filtros["amount_gte_eur"]):
            return False, flat
    if not _regex_ok(filtros.get("customer_email_regex"), customer):
        return False, flat
    return True, flat


def matches_email(filtros: dict, event: dict) -> tuple[bool, dict]:
    if not _regex_ok(filtros.get("from_regex"), event.get("from")):
        return False, event
    if not _regex_ok(filtros.get("subject_regex"), event.get("subject")):
        return False, event
    return True, event


def cron_should_fire(rrule: str, now: datetime, ventana_s: float = 30.0) -> bool:
    """¿La rrule cron tiene que dispararse en [now - ventana_s, now]?

    Usa croniter para encontrar la siguiente fecha desde `now - ventana_s` y
    comprueba si cae dentro de la ventana.
    """
    try:
        from croniter import croniter
    except ImportError:
        log.warning("croniter no instalado; cron_should_fire desactivado")
        return False
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    start = now.timestamp() - ventana_s
    it = croniter(rrule, start)
    nxt_ts = it.get_next()
    return start <= nxt_ts <= now.timestamp()
