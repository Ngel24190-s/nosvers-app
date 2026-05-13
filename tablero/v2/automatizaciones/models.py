"""Pydantic models para Automation Engine (004).

Discriminated unions sealed para Trigger y Action. Forward-refs resueltas para
CondicionalAction (que se referencia a sí mismo a través de listas de Action).
"""
from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any, Literal, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator

Autor = Literal["angel", "africa", "claude"]


# ── Triggers ────────────────────────────────────────────────────────────────

class CronTrigger(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tipo: Literal["cron"]
    rrule: str

    @field_validator("rrule")
    @classmethod
    def _validar_rrule(cls, v: str) -> str:
        try:
            from croniter import croniter
            if not croniter.is_valid(v):
                raise ValueError(f"rrule cron inválida: {v}")
        except ImportError:
            pass
        return v


class WebhookStripeTrigger(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tipo: Literal["webhook_stripe"]
    evento: str = "payment_intent.succeeded"
    filtros: dict[str, Any] = Field(default_factory=dict)


class NotaCapturadaTrigger(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tipo: Literal["nota_capturada"]
    filtros: dict[str, Any] = Field(default_factory=dict)


class AgenteTerminadoTrigger(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tipo: Literal["agente_terminado"]
    filtros: dict[str, Any] = Field(default_factory=dict)


class AegisAlertaTrigger(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tipo: Literal["aegis_alerta"]
    filtros: dict[str, Any] = Field(default_factory=dict)


class EmailMatchTrigger(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tipo: Literal["email_match"]
    filtros: dict[str, Any] = Field(default_factory=dict)


class VozKeywordTrigger(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tipo: Literal["voz_keyword"]
    keywords: list[str] = Field(min_length=1)


class VpsThresholdTrigger(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tipo: Literal["vps_threshold"]
    metrica: Literal["cpu", "ram", "disk"]
    umbral_pct: float = Field(ge=0, le=100)
    comparador: Literal["gt", "lt"]


Trigger = Annotated[
    Union[
        CronTrigger,
        WebhookStripeTrigger,
        NotaCapturadaTrigger,
        AgenteTerminadoTrigger,
        AegisAlertaTrigger,
        EmailMatchTrigger,
        VozKeywordTrigger,
        VpsThresholdTrigger,
    ],
    Field(discriminator="tipo"),
]


# ── Actions ─────────────────────────────────────────────────────────────────

class DiaCapturarAction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tipo: Literal["dia_capturar"]
    texto: str = Field(min_length=1)
    etiqueta: str = ""
    autor: Autor | None = None


class TelegramAction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tipo: Literal["telegram"]
    mensaje: str = Field(min_length=1)
    chat_id: str | None = None


class EjecutarAgenteAction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tipo: Literal["ejecutar_agente"]
    agente: str = Field(min_length=1)
    params: dict[str, Any] = Field(default_factory=dict)


class ClaudePromptAction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tipo: Literal["claude_prompt"]
    model: str = "claude-haiku-4-5-20251001"
    system: str = ""
    prompt: str = Field(min_length=1)
    max_tokens: int = Field(default=2000, ge=1, le=16000)


class EmailEnviarAction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tipo: Literal["email_enviar"]
    to: str = Field(min_length=3)
    subject: str
    body: str


class WebhookCallAction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tipo: Literal["webhook_call"]
    url: str = Field(pattern=r"^https?://")
    method: Literal["GET", "POST", "PUT", "DELETE"] = "POST"
    headers: dict[str, str] = Field(default_factory=dict)
    body_json: dict[str, Any] | None = None


class CockpitToastAction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tipo: Literal["cockpit_toast"]
    level: Literal["ok", "warn", "error"] = "ok"
    text: str = Field(min_length=1)


class WpPostAction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tipo: Literal["wp_post"]
    titulo: str = Field(min_length=1)
    contenido_html: str
    status: Literal["draft", "publish"] = "draft"


class DelayAction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tipo: Literal["delay"]
    segundos: float = Field(ge=0.1, le=300)


class CondicionalAction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tipo: Literal["condicional"]
    expresion: str = Field(min_length=1)
    acciones_si: list["Action"] = Field(min_length=1)
    acciones_no: list["Action"] = Field(default_factory=list)


Action = Annotated[
    Union[
        DiaCapturarAction,
        TelegramAction,
        EjecutarAgenteAction,
        ClaudePromptAction,
        EmailEnviarAction,
        WebhookCallAction,
        CockpitToastAction,
        WpPostAction,
        DelayAction,
        CondicionalAction,
    ],
    Field(discriminator="tipo"),
]


CondicionalAction.model_rebuild()


# ── Automation root ─────────────────────────────────────────────────────────

ID_PATTERN = r"^(auto|ejemplo)_\d{4}_\d{2}_\d{2}_[a-z0-9_]{1,80}$"


class Automation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(pattern=ID_PATTERN)
    nombre: str = Field(min_length=1, max_length=120)
    autor: Autor
    creado: datetime
    modificado: datetime
    activo: bool = False
    trigger: Trigger
    acciones: list[Action] = Field(min_length=1, max_length=20)
    metadatos: dict[str, Any] = Field(default_factory=dict)


class AutomationCreate(BaseModel):
    """Body para POST /automatizaciones — sin id, creado, modificado, autor."""
    model_config = ConfigDict(extra="forbid")
    nombre: str = Field(min_length=1, max_length=120)
    activo: bool = False
    trigger: Trigger
    acciones: list[Action] = Field(min_length=1, max_length=20)
    metadatos: dict[str, Any] = Field(default_factory=dict)


__all__ = [
    "Autor", "Automation", "AutomationCreate",
    "Trigger", "Action", "ID_PATTERN",
    # Triggers
    "CronTrigger", "WebhookStripeTrigger", "NotaCapturadaTrigger",
    "AgenteTerminadoTrigger", "AegisAlertaTrigger", "EmailMatchTrigger",
    "VozKeywordTrigger", "VpsThresholdTrigger",
    # Actions
    "DiaCapturarAction", "TelegramAction", "EjecutarAgenteAction",
    "ClaudePromptAction", "EmailEnviarAction", "WebhookCallAction",
    "CockpitToastAction", "WpPostAction", "DelayAction", "CondicionalAction",
]
