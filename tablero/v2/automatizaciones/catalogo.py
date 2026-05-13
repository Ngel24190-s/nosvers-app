"""Catálogo de triggers + actions con JSON Schema + flags de disponibilidad."""
from __future__ import annotations

import os
from typing import Any

from tablero.v2.automatizaciones.models import (
    AegisAlertaTrigger,
    AgenteTerminadoTrigger,
    ClaudePromptAction,
    CockpitToastAction,
    CondicionalAction,
    CronTrigger,
    DelayAction,
    DiaCapturarAction,
    EjecutarAgenteAction,
    EmailEnviarAction,
    EmailMatchTrigger,
    NotaCapturadaTrigger,
    TelegramAction,
    VozKeywordTrigger,
    VpsThresholdTrigger,
    WebhookCallAction,
    WebhookStripeTrigger,
    WpPostAction,
)

_TRIGGER_META: list[tuple[type, str, str]] = [
    (CronTrigger, "Cron (rrule)", "clock"),
    (WebhookStripeTrigger, "Webhook Stripe", "credit-card"),
    (NotaCapturadaTrigger, "Nota capturada", "edit"),
    (AgenteTerminadoTrigger, "Agente terminado", "cpu"),
    (AegisAlertaTrigger, "AEGIS alerta", "shield"),
    (EmailMatchTrigger, "Email match", "mail"),
    (VozKeywordTrigger, "Voz keyword", "mic"),
    (VpsThresholdTrigger, "VPS threshold", "activity"),
]

_ACTION_META: list[tuple[type, str, str]] = [
    (DiaCapturarAction, "Capturar nota", "edit"),
    (TelegramAction, "Telegram", "send"),
    (EjecutarAgenteAction, "Ejecutar agente", "play"),
    (ClaudePromptAction, "Claude prompt", "sparkles"),
    (EmailEnviarAction, "Enviar email", "mail"),
    (WebhookCallAction, "Webhook call", "globe"),
    (CockpitToastAction, "Cockpit toast", "bell"),
    (WpPostAction, "WordPress post", "file-text"),
    (DelayAction, "Delay", "pause"),
    (CondicionalAction, "Condicional", "git-branch"),
]


def _disponibilidad_trigger(cls: type) -> tuple[bool, str | None]:
    name = cls.__name__
    if name == "WebhookStripeTrigger":
        if not os.environ.get("STRIPE_WEBHOOK_SECRET"):
            return False, "STRIPE_WEBHOOK_SECRET no configurado"
    if name == "EmailMatchTrigger":
        if not os.environ.get("IMAP_HOST"):
            return False, "IMAP no configurado"
    return True, None


def _disponibilidad_action(cls: type) -> tuple[bool, str | None]:
    name = cls.__name__
    if name == "EmailEnviarAction":
        if not os.environ.get("SMTP_HOST"):
            return False, "SMTP no configurado"
    if name == "WpPostAction":
        if not os.environ.get("WP_API"):
            return False, "WP_API no configurado"
    return True, None


def _schema(cls: type) -> dict[str, Any]:
    schema = cls.model_json_schema()
    # Pydantic incluye `title` y a veces refs; lo dejamos tal cual para que el
    # frontend lo use directamente.
    return schema


def _tipo_from_class(cls: type) -> str:
    """Extrae el Literal del campo `tipo`."""
    fields = cls.model_fields
    f = fields.get("tipo")
    if f is None:
        return cls.__name__.lower()
    # f.annotation = Literal["..."]
    args = getattr(f.annotation, "__args__", None)
    if args:
        return str(args[0])
    return cls.__name__.lower()


def build_catalog() -> dict[str, Any]:
    triggers: dict[str, Any] = {}
    for cls, label, icon in _TRIGGER_META:
        tipo = _tipo_from_class(cls)
        avail, reason = _disponibilidad_trigger(cls)
        triggers[tipo] = {
            "schema": _schema(cls),
            "available": avail,
            "label": label,
            "icon": icon,
        }
        if reason:
            triggers[tipo]["reason"] = reason
    actions: dict[str, Any] = {}
    for cls, label, icon in _ACTION_META:
        tipo = _tipo_from_class(cls)
        avail, reason = _disponibilidad_action(cls)
        actions[tipo] = {
            "schema": _schema(cls),
            "available": avail,
            "label": label,
            "icon": icon,
        }
        if reason:
            actions[tipo]["reason"] = reason
    return {"triggers": triggers, "actions": actions}
