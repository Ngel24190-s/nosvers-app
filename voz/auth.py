"""
voz.auth — Tokens JWT Bearer revocables para la PWA.

Contrato: ver specs/001-voice-assistant/data-model.md §7.
"""
from __future__ import annotations

import os
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import jwt

DATA_DIR = Path("/home/nosvers/voz/data")
DB_PATH = DATA_DIR / "tokens.sqlite"
SECRET_ENV = "VOZ_JWT_SECRET"
DEFAULT_TTL_DAYS = 365
ALGORITHM = "HS256"


def _secret() -> str:
    s = os.getenv(SECRET_ENV, "")
    if not s:
        # En desarrollo, usa MCP_TOKEN como salt si no hay secret específico.
        s = os.getenv("MCP_TOKEN", "")
    if not s:
        raise RuntimeError(
            f"Falta {SECRET_ENV} en el entorno (o MCP_TOKEN como fallback)"
        )
    return s


def _conn() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(DB_PATH)
    c.execute("""
        CREATE TABLE IF NOT EXISTS tokens (
            jti          TEXT PRIMARY KEY,
            device_label TEXT NOT NULL,
            issued_at    TEXT NOT NULL,
            expires_at   TEXT NOT NULL,
            revoked_at   TEXT
        )
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_tokens_revoked ON tokens(revoked_at)")
    return c


AUTORES_VALIDOS = {"angel", "africa"}
CONTEXTS_VALIDOS = {"casa", "nosvers", "trabajo"}
CONTEXTS_DEFAULT = ["casa", "nosvers"]
CONTEXTS_ANGEL = ["casa", "nosvers", "trabajo"]


def emitir_token(
    device_label: str,
    ttl_days: int = DEFAULT_TTL_DAYS,
    autor: str = "angel",
    contexts: list[str] | None = None,
) -> dict:
    """Emite un nuevo token JWT y lo registra. Devuelve dict con jwt + metadatos.

    `autor` (BRIEF §14): "angel" o "africa". Persiste en JWT como `sub` y se
    usa en /voz/api/capturar como identidad del usuario asociado al device.

    `contexts` (007 §FR-B): lista de contextos disponibles para el portador.
    Si se omite: ["casa","nosvers","trabajo"] para angel, ["casa","nosvers"]
    para africa. El contexto "trabajo" SOLO se concede a angel; intento con
    africa lanza ValueError (defense-in-depth contra mis-issuance).
    """
    if not device_label:
        raise ValueError("device_label requerido")
    autor = autor.strip().lower()
    if autor not in AUTORES_VALIDOS:
        raise ValueError(f"autor inválido: {autor!r}. Esperado: {sorted(AUTORES_VALIDOS)}")
    if contexts is None:
        contexts = CONTEXTS_ANGEL if autor == "angel" else CONTEXTS_DEFAULT
    contexts = [str(c).strip().lower() for c in contexts]
    for c in contexts:
        if c not in CONTEXTS_VALIDOS:
            raise ValueError(f"contexto inválido: {c!r}. Esperado: {sorted(CONTEXTS_VALIDOS)}")
    if "trabajo" in contexts and autor != "angel":
        raise ValueError("contexto 'trabajo' solo permitido para autor=angel")
    # dedupe preservando orden
    seen: set[str] = set()
    contexts = [c for c in contexts if not (c in seen or seen.add(c))]
    jti = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    exp = now + timedelta(days=ttl_days)
    payload = {
        "jti": jti,
        "device": device_label,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
        "sub": autor,
        "available_contexts": contexts,
    }
    token = jwt.encode(payload, _secret(), algorithm=ALGORITHM)
    with _conn() as c:
        c.execute(
            "INSERT INTO tokens(jti, device_label, issued_at, expires_at) VALUES(?,?,?,?)",
            (jti, device_label, now.isoformat(), exp.isoformat()),
        )
    return {
        "jwt": token, "jti": jti, "device": device_label,
        "autor": autor, "expires_at": exp.isoformat(),
        "available_contexts": contexts,
    }


def check_context(payload: dict | None, requested: str | None) -> bool:
    """True si el JWT autoriza el contexto solicitado (007 §FR-B-5).

    Reglas:
    - payload None → False.
    - requested fuera de {casa,nosvers,trabajo} → False.
    - requested == "trabajo" pero sub != "angel" → False (defensa adicional
      aunque available_contexts lo incluya por error).
    - Si payload no trae available_contexts (token viejo), default
      CONTEXTS_DEFAULT (NUNCA trabajo).
    - True si requested ∈ available_contexts.
    """
    if not payload:
        return False
    requested = (requested or "").strip().lower()
    if requested not in CONTEXTS_VALIDOS:
        return False
    if requested == "trabajo" and (payload.get("sub") or "").strip().lower() != "angel":
        return False
    available = payload.get("available_contexts") or CONTEXTS_DEFAULT
    return requested in available


def validar_token(token: str) -> dict | None:
    """Devuelve el payload si el token es válido y no está revocado, None si no."""
    if not token:
        return None
    try:
        payload = jwt.decode(token, _secret(), algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        return None
    jti = payload.get("jti")
    if not jti:
        return None
    with _conn() as c:
        row = c.execute(
            "SELECT revoked_at FROM tokens WHERE jti=?", (jti,)
        ).fetchone()
    if row is None:
        # Token con firma válida pero sin registro (no fue emitido por nosotros).
        return None
    if row[0]:  # revoked_at no nulo
        return None
    return payload


def revocar_token(jti: str) -> bool:
    """Marca un token como revocado. Devuelve True si afectó a 1 fila."""
    if not jti:
        return False
    with _conn() as c:
        cur = c.execute(
            "UPDATE tokens SET revoked_at=? WHERE jti=? AND revoked_at IS NULL",
            (datetime.now(timezone.utc).isoformat(), jti),
        )
        return cur.rowcount == 1


def listar_tokens(incluir_revocados: bool = False) -> list[dict]:
    with _conn() as c:
        if incluir_revocados:
            rows = c.execute(
                "SELECT jti, device_label, issued_at, expires_at, revoked_at FROM tokens ORDER BY issued_at DESC"
            ).fetchall()
        else:
            rows = c.execute(
                "SELECT jti, device_label, issued_at, expires_at, revoked_at FROM tokens WHERE revoked_at IS NULL ORDER BY issued_at DESC"
            ).fetchall()
    return [
        {"jti": r[0], "device_label": r[1], "issued_at": r[2], "expires_at": r[3], "revoked_at": r[4]}
        for r in rows
    ]
