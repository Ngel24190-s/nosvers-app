"""
voz.capturar — Orquestación de captura de nota: STT → clasificación → vault.

Contrato: ver specs/001-voice-assistant/contracts/mcp_tools.md (dia_capturar).
"""
from __future__ import annotations

import base64
import logging
import time
from collections import OrderedDict
from datetime import datetime, timezone
from threading import Lock

from .vault_io import (
    AUTORES_VALIDOS,
    DIA_DIR,
    Nota,
    ETIQUETAS_VALIDAS,
    ORIGENES_VALIDOS,
    VAULT_BASE,
    _normalize_autor,
    escribir_nota,
    guardar_audio_opus,
    ruta_audio_relativa,
)

log = logging.getLogger("voz.capturar")

# Cache LRU de (device_label, client_uuid) → resultado, TTL 1h, max 1000 por device.
_IDEM_CACHE: OrderedDict[tuple[str, str], tuple[float, dict]] = OrderedDict()
_IDEM_LOCK = Lock()
_IDEM_MAX = 1000
_IDEM_TTL_S = 3600


def _idempotencia_get(device: str, uuid: str) -> dict | None:
    if not uuid:
        return None
    key = (device or "_", uuid)
    with _IDEM_LOCK:
        item = _IDEM_CACHE.get(key)
        if not item:
            return None
        ts, res = item
        if time.monotonic() - ts > _IDEM_TTL_S:
            del _IDEM_CACHE[key]
            return None
        _IDEM_CACHE.move_to_end(key)
        return res


def _idempotencia_set(device: str, uuid: str, resultado: dict) -> None:
    if not uuid:
        return
    key = (device or "_", uuid)
    with _IDEM_LOCK:
        _IDEM_CACHE[key] = (time.monotonic(), resultado)
        _IDEM_CACHE.move_to_end(key)
        while len(_IDEM_CACHE) > _IDEM_MAX:
            _IDEM_CACHE.popitem(last=False)


def _parse_ts(ts_iso: str) -> datetime:
    if not ts_iso:
        return datetime.now().astimezone()
    try:
        dt = datetime.fromisoformat(ts_iso)
        if dt.tzinfo is None:
            dt = dt.astimezone()
        return dt
    except ValueError:
        return datetime.now().astimezone()


def dia_capturar_impl(
    texto: str = "",
    audio_bytes: bytes | None = None,
    audio_b64: str = "",
    ts_iso: str = "",
    etiqueta: str = "auto",
    origen: str = "otro",
    autor: str = "angel",
    device_label: str = "mcp_directo",
    client_uuid: str = "",
) -> dict:
    """Implementación de dia_capturar. Devuelve dict con campos del contrato.

    `autor` (BRIEF §14): "angel" o "africa". Se persiste en el frontmatter
    de la nota y en el sufijo del nombre del audio. En PWA viene del JWT
    `sub`; en voz_linux viene de la identificación por speaker ID.
    """
    t0 = time.monotonic()
    autor_n = _normalize_autor(autor)

    # Idempotencia
    cached = _idempotencia_get(device_label, client_uuid)
    if cached is not None:
        log.info(f"capturar idempotente reusado uuid={client_uuid[:8]}")
        return cached | {"nota": "duplicado_ignorado"}

    # Normalizar enums
    origen = origen if origen in ORIGENES_VALIDOS else "otro"

    # Decodificar audio si viene en base64
    if not audio_bytes and audio_b64:
        try:
            audio_bytes = base64.b64decode(audio_b64, validate=True)
        except (ValueError, TypeError) as e:
            return {"ok": False, "error": "parametro_invalido", "detalle": f"audio_b64: {e}"}

    # Si llega audio sin texto, transcribir
    audio_path_rel: str | None = None
    if audio_bytes:
        ts_dt = _parse_ts(ts_iso)
        fecha = ts_dt.date()
        hms = ts_dt.strftime("%H-%M-%S")
        audio_path = guardar_audio_opus(audio_bytes, fecha, hms, autor_n)
        audio_path_rel = ruta_audio_relativa(audio_path)
        if not texto.strip():
            try:
                from .stt import transcribir  # lazy import (faster-whisper)
                stt_res = transcribir(audio_bytes)
                texto = stt_res["texto"]
                log.info(f"STT idioma={stt_res['idioma_detectado']} dur={stt_res['duracion']:.1f}s")
            except Exception as e:
                log.error(f"STT falló: {e}")
                return {"ok": False, "error": "whisper_error", "detalle": str(e)}

    if not texto.strip():
        return {"ok": False, "error": "input_vacio"}

    # Clasificar
    if etiqueta == "auto":
        from .clasificar import clasificar
        cls = clasificar(texto)
        etiqueta_final = cls["etiqueta"]
        confianza = cls["confianza"]
        modelo = cls["modelo"]
    elif etiqueta in ETIQUETAS_VALIDAS:
        etiqueta_final = etiqueta
        confianza = 1.0
        modelo = "manual"
    else:
        etiqueta_final = "otro"
        confianza = 0.0
        modelo = "fallback"

    # Construir nota y escribir
    ts_dt = _parse_ts(ts_iso)
    nota = Nota(
        ts=ts_dt.isoformat(),
        autor=autor_n,
        etiqueta=etiqueta_final,
        origen=origen,
        audio=audio_path_rel,
        clasificador_confianza=confianza,
        clasificador_modelo=modelo,
        texto=texto.strip(),
    )
    try:
        archivo = escribir_nota(nota)
    except Exception as e:
        log.exception("Error escribiendo nota")
        return {"ok": False, "error": "vault_locked" if "lock" in str(e).lower() else "interno",
                "detalle": str(e)}

    latencia_ms = int((time.monotonic() - t0) * 1000)
    log.info(
        f"ok autor={autor_n} device={device_label} origen={origen} etiqueta={etiqueta_final} "
        f"conf={confianza:.2f} latencia={latencia_ms}ms"
    )

    resultado = {
        "ok": True,
        "archivo": str(archivo.relative_to(VAULT_BASE.parent)),
        "ts": nota.ts,
        "autor": autor_n,
        "texto": texto.strip(),
        "transcripcion": texto.strip(),
        "etiqueta_aplicada": etiqueta_final,
        "confianza": round(confianza, 3),
        "modelo": modelo,
        "audio_persistido": audio_path_rel,
        "latencia_ms": latencia_ms,
    }
    _idempotencia_set(device_label, client_uuid, resultado)
    return resultado
