"""
voz.rest — Endpoints REST sobre el binario MCP para servir a la PWA.

Comparte el proceso del MCP server. Se monta sobre FastMCP usando su
servidor HTTP subyacente (Starlette). Auth Bearer vía voz.auth.
"""
from __future__ import annotations

import json
import logging
import os
import time
from datetime import date
from pathlib import Path
from typing import Any

from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

from .tts import sintetizar
from .conversar import conversar
from .auth import validar_token, check_context, CONTEXTS_VALIDOS
from .capturar import dia_capturar_impl
from .contexto import dia_contexto_impl
from .buscar import dia_buscar_impl
from .intent_router import IntentResult, route_intent, TOOLS_POR_CONTEXTO
from .compose_voice_response import compose_voice_response

log = logging.getLogger("voz.rest")

ALLOWED_ORIGIN = "https://voz.nosvers.com"
MAX_AUDIO_BYTES = 5 * 1024 * 1024  # 5 MB

_DICTADO_LOGS_DIR = Path(
    os.getenv(
        "CLAUDIO_DICTADO_LOGS_DIR",
        "/home/nosvers/public_html/knowledge_base/claudio/logs",
    )
)


def _cors_headers() -> dict:
    return {
        "Access-Control-Allow-Origin": ALLOWED_ORIGIN,
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Authorization, Content-Type, X-Request-Id, X-Claudio-Context",
        "Access-Control-Max-Age": "86400",
    }


def _json(data: dict, status: int = 200) -> JSONResponse:
    return JSONResponse(data, status_code=status, headers=_cors_headers())


async def _autenticar(request: Request) -> dict | None:
    auth = request.headers.get("authorization", "")
    if not auth.lower().startswith("bearer "):
        return None
    token = auth[7:].strip()
    return validar_token(token)


async def options_handler(request: Request) -> Response:
    return Response(status_code=204, headers=_cors_headers())


async def capturar_handler(request: Request) -> JSONResponse:
    payload = await _autenticar(request)
    if not payload:
        return _json({"ok": False, "error": "auth_invalido"}, 401)
    device = payload.get("device", "desconocido")
    # autor (BRIEF §14) viene del JWT `sub`; fallback a "angel" si no presente
    autor_jwt = payload.get("sub") or payload.get("autor") or "angel"

    ctype = request.headers.get("content-type", "").lower()
    kwargs: dict[str, Any] = {"device_label": device, "autor": autor_jwt}

    if "multipart/form-data" in ctype:
        form = await request.form()
        meta_raw = form.get("meta", "")
        if hasattr(meta_raw, "read"):  # FileLike
            meta_raw = (await meta_raw.read()).decode("utf-8")
        try:
            meta = json.loads(meta_raw) if meta_raw else {}
        except json.JSONDecodeError:
            return _json({"ok": False, "error": "parametro_invalido", "detalle": "meta no es JSON"}, 400)
        audio_field = form.get("audio")
        if audio_field is None:
            return _json({"ok": False, "error": "input_vacio"}, 400)
        audio_bytes = await audio_field.read()
        if len(audio_bytes) > MAX_AUDIO_BYTES:
            return _json({"ok": False, "error": "payload_too_large"}, 413)
        kwargs.update({
            "audio_bytes": audio_bytes,
            "texto": meta.get("texto", ""),
            "ts_iso": meta.get("ts_iso", ""),
            "etiqueta": meta.get("etiqueta", "auto"),
            "origen": meta.get("origen", "voz_movil"),
            "client_uuid": meta.get("client_uuid", ""),
        })
        # autor del meta sólo si el JWT lo permite (mismo autor o override autorizado)
        if meta.get("autor") and meta.get("autor") == autor_jwt:
            kwargs["autor"] = meta["autor"]
    elif "application/json" in ctype:
        try:
            data = await request.json()
        except json.JSONDecodeError:
            return _json({"ok": False, "error": "parametro_invalido", "detalle": "body no JSON"}, 400)
        kwargs.update({
            "texto": data.get("texto", ""),
            "audio_b64": data.get("audio_b64", ""),
            "ts_iso": data.get("ts_iso", ""),
            "etiqueta": data.get("etiqueta", "auto"),
            "origen": data.get("origen", "otro"),
            "client_uuid": data.get("client_uuid", ""),
        })
        if data.get("autor") and data.get("autor") == autor_jwt:
            kwargs["autor"] = data["autor"]
    else:
        return _json({"ok": False, "error": "unsupported_media_type"}, 415)

    result = dia_capturar_impl(**kwargs)
    status = 200 if result.get("ok") else 400
    return _json(result, status)


async def contexto_handler(request: Request) -> JSONResponse:
    payload = await _autenticar(request)
    if not payload:
        return _json({"ok": False, "error": "auth_invalido"}, 401)
    qp = request.query_params
    result = dia_contexto_impl(
        rango_dias=int(qp.get("dias", 7)),
        incluir_calendario=qp.get("calendario", "1") in ("1", "true", "yes"),
        incluir_estado_agentes=qp.get("agentes", "1") in ("1", "true", "yes"),
        etiquetas_filtro=qp.get("etiquetas", ""),
        autor=qp.get("autor", ""),
    )
    return _json(result)


async def buscar_handler(request: Request) -> JSONResponse:
    payload = await _autenticar(request)
    if not payload:
        return _json({"ok": False, "error": "auth_invalido"}, 401)
    qp = request.query_params
    result = dia_buscar_impl(
        query=qp.get("q", ""),
        desde=qp.get("desde", ""),
        hasta=qp.get("hasta", ""),
        limite=int(qp.get("limite", 20)),
        etiqueta=qp.get("etiqueta", ""),
        autor=qp.get("autor", ""),
    )
    status = 200 if result.get("ok") else 400
    return _json(result, status)


async def health_handler(request: Request) -> JSONResponse:
    return _json({"ok": True, "service": "voz", "version": "1.0.0"})


# ─── /voz/api/dictado-procesar (Fase 2) ───────────────────────────

def _execute_intent(intent: IntentResult, transcript: str, autor: str,
                    device: str, contexto: str = "casa") -> str:
    """Ejecuta el tool decidido por el router. Devuelve string humano.

    `contexto` (007 §FR-G-3): Si == "trabajo" y tool == dia_capturar, la
    nota cae en el vault trabajo/. Para tools del dominio trabajo, el
    autor se inyecta server-side igual que en otros dominios.
    """
    tool = intent.tool
    args = dict(intent.args or {})
    args.pop("autor", None)
    args.pop("quien", None) if tool == "claudio_recordar" else None

    # Mapa tool → callable
    try:
        if tool == "claudio_conversar":
            res = conversar(
                texto=str(args.get("texto") or transcript),
                autor=autor,
                contexto=contexto,
            )
            if not res.get("ok"):
                return f"❌ {res.get('error', 'error_conversar')}"
            return f"💬 {res['texto']}"

        if tool == "dia_capturar":
            res = dia_capturar_impl(
                texto=args.get("texto") or transcript,
                etiqueta=("trabajo" if contexto == "trabajo" else "auto"),
                origen=f"dictado:{contexto}",
                autor=autor,
                device_label=device or "dictado",
            )
            if not res.get("ok"):
                return f"❌ {res.get('error', 'error')}"
            etiq = res.get("etiqueta_aplicada", "otro")
            return f"✅ Apuntado en notas ({etiq})."

        if tool == "dia_buscar":
            res = dia_buscar_impl(
                query=str(args.get("query", "")),
                desde=str(args.get("desde", "")),
                hasta=str(args.get("hasta", "")),
                limite=int(args.get("limite", 10)),
            )
            if not res.get("ok"):
                return f"❌ {res.get('error', 'error')}"
            n = res.get("total", 0)
            return f"Encontré {n} resultados."

        # claudio_tools: importamos lazy para no romper si claudio_tools cae
        from claudio_tools import (
            identidad as _id,
            familia as _fam,
            finanzas as _fin,
            compras as _com,
            menus as _men,
            coche as _coc,
            casa as _cas,
            documentos as _doc,
            salud as _sal,
        )
        # tools que reciben autor explícito
        if tool == "claudio_recordar":
            return _id.claudio_recordar(autor, args.get("hecho", ""),
                                        int(args.get("importancia", 5)))
        if tool == "claudio_contexto":
            return _id.claudio_contexto(autor, args.get("query", ""),
                                        int(args.get("limite", 10)))
        if tool == "recordatorio_crear":
            return _fam.recordatorio_crear(args.get("texto", ""),
                                           args.get("fecha", "hoy"),
                                           autor,
                                           int(args.get("prioridad", 3)))
        if tool == "recordatorios_listar":
            return _fam.recordatorios_listar(
                args.get("periodo", "proximos_7_dias"),
                args.get("autor_filtro", ""))
        if tool == "recordatorio_completar":
            return _fam.recordatorio_completar(args.get("id_o_slug", ""))
        if tool == "familia_cumpleanos_listar":
            return _fam.familia_cumpleanos_listar(int(args.get("meses", 12)))
        if tool == "gasto_anotar":
            return _fin.gasto_anotar(
                float(args.get("monto_eur", 0)),
                args.get("concepto", ""),
                args.get("categoria", "otros"),
                autor)
        if tool == "gastos_resumen":
            return _fin.gastos_resumen(
                args.get("periodo", "mes_actual"),
                args.get("categoria", ""))
        if tool == "recurrente_alertar":
            return _fin.recurrente_alertar(int(args.get("dias", 7)))
        if tool in ("lista_compras_añadir", "lista_compras_anadir"):
            return _com.lista_compras_añadir(
                args.get("item", ""), autor,
                args.get("cantidad", ""),
                bool(args.get("urgente", False)))
        if tool == "lista_compras_ver":
            return _com.lista_compras_ver()
        if tool == "lista_compras_completar":
            return _com.lista_compras_completar(args.get("item", ""))
        if tool == "despensa_estado":
            return _com.despensa_estado()
        if tool == "menu_sugerir":
            return _men.menu_sugerir(args.get("dia", ""),
                                     args.get("ingredientes_disponibles", ""))
        if tool == "receta_guardar":
            return _men.receta_guardar(
                args.get("nombre", ""),
                args.get("ingredientes", ""),
                args.get("pasos", ""),
                args.get("fuente", ""))
        if tool == "coche_estado":
            return _coc.coche_estado()
        if tool == "coche_evento":
            return _coc.coche_evento(
                args.get("tipo", "otros"),
                args.get("fecha", "hoy"),
                float(args.get("monto_eur", 0)),
                args.get("notas", ""),
                autor)
        if tool == "documento_anotar":
            return _doc.documento_anotar(
                args.get("tipo", "otros"),
                args.get("contenido_texto", "") or transcript,
                args.get("fecha", "hoy"),
                args.get("fuente", ""),
                autor)
        if tool == "documentos_buscar":
            return _doc.documentos_buscar(args.get("query", ""),
                                          int(args.get("limite", 20)))
        if tool == "medicacion_recordar":
            return _sal.medicacion_recordar()
        if tool == "cita_medica_anotar":
            return _sal.cita_medica_anotar(
                args.get("quien", autor),
                args.get("especialista", ""),
                args.get("fecha", ""),
                args.get("notas", ""),
                autor)
        if tool == "casa_mantenimiento_anotar":
            return _cas.casa_mantenimiento_anotar(
                args.get("tarea", ""),
                args.get("fecha", ""),
                args.get("proximo", ""),
                autor)

        # ─── Trabajo (007) ─────────────────────────────────────────
        if tool.startswith("chantier_") or tool.startswith("equipe_") \
           or tool in {"devis_anotar", "ppsps_crear",
                       "documento_trabajo_archivar"}:
            from claudio_tools import trabajo as _tra
            if tool == "chantier_listar":
                return _tra.chantier_listar(args.get("estado", "activos"))
            if tool == "chantier_crear":
                return _tra.chantier_crear(
                    args.get("nombre", ""),
                    args.get("direccion", ""),
                    args.get("cliente", ""),
                    float(args.get("devis_eur", 0)),
                    args.get("equipe_ids", ""),
                    args.get("fecha_inicio", "hoy"),
                    args.get("fecha_fin_prev", ""),
                    autor)
            if tool == "chantier_evento":
                return _tra.chantier_evento(
                    args.get("chantier_id", ""),
                    args.get("tipo", "journal"),
                    args.get("descripcion", "") or transcript,
                    autor)
            if tool == "chantier_estado":
                return _tra.chantier_estado(args.get("chantier_id", ""))
            if tool == "chantier_documento_listar":
                return _tra.chantier_documento_listar(
                    args.get("chantier_id", ""),
                    args.get("tipo", "todos"))
            if tool == "equipe_listar":
                return _tra.equipe_listar()
            if tool == "equipe_anotar":
                return _tra.equipe_anotar(
                    args.get("operario", ""),
                    args.get("evento", ""),
                    args.get("fecha", "hoy"))
            if tool == "devis_anotar":
                return _tra.devis_anotar(
                    args.get("cliente", ""),
                    float(args.get("monto_eur", 0)),
                    args.get("chantier_ref", ""))
            if tool == "ppsps_crear":
                return _tra.ppsps_crear(
                    args.get("chantier_id", ""),
                    args.get("version", "v1"),
                    args.get("observaciones", ""))
            if tool == "documento_trabajo_archivar":
                return _tra.documento_trabajo_archivar(
                    args.get("tipo", "otro"),
                    args.get("contenido", "") or transcript,
                    args.get("chantier_ref", ""))
    except Exception as e:  # noqa: BLE001
        log.warning(f"_execute_intent fallo en {tool}: {e}")
        return f"❌ {e}"
    return f"❌ tool desconocido: {tool}"


def _log_dictado(*, autor: str, transcript: str, intent: IntentResult,
                 tool_result: str, latency_ms: int, device: str,
                 ok: bool) -> None:
    try:
        _DICTADO_LOGS_DIR.mkdir(parents=True, exist_ok=True)
        log_full = os.getenv("CLAUDIO_DICTADO_LOG_FULL") == "1"
        line: dict[str, Any] = {
            "ts": __import__("datetime").datetime.now().astimezone()
                  .isoformat(timespec="seconds"),
            "autor": autor,
            "transcript_len": len(transcript),
            "intent": {
                "tool": intent.tool,
                "confidence": round(intent.confidence, 3),
                "fallback": intent.fallback,
                "cached": intent.cached,
                "modelo": intent.modelo,
            },
            "args": intent.args,
            "ok": ok,
            "latency_ms": latency_ms,
            "device": device,
        }
        if log_full:
            line["transcript"] = transcript
            line["tool_result"] = tool_result
        path = _DICTADO_LOGS_DIR / f"dictado-{date.today().isoformat()}.jsonl"
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(line, ensure_ascii=False) + "\n")
    except Exception as e:  # noqa: BLE001
        log.debug(f"log_dictado fallo: {e}")


async def dictado_procesar_handler(request: Request) -> JSONResponse:
    payload = await _autenticar(request)
    if not payload:
        return _json({"ok": False, "error": "auth_invalido"}, 401)
    autor_jwt = payload.get("sub") or payload.get("autor") or "angel"
    device = payload.get("device", "desconocido")

    # Contexto activo (007 §FR-G-1): viene del header `X-Claudio-Context`,
    # NUNCA del body. Default "casa" si ausente (retro-compat con clientes
    # pre-007 que solo veían el contexto familiar).
    ctx_raw = (request.headers.get("x-claudio-context")
               or "casa").strip().lower()
    if ctx_raw not in CONTEXTS_VALIDOS:
        return _json({"ok": False, "error": "context_invalido",
                      "detalle": f"contexto desconocido: {ctx_raw}"}, 400)
    if not check_context(payload, ctx_raw):
        return _json({"ok": False, "error": "context_no_autorizado",
                      "detalle": f"sin acceso a {ctx_raw}"}, 403)
    contexts_permitidos = TOOLS_POR_CONTEXTO.get(ctx_raw, set()) | {"dia_capturar"}

    try:
        data = await request.json()
    except json.JSONDecodeError:
        return _json({"ok": False, "error": "parametro_invalido",
                      "detalle": "body no JSON"}, 400)

    transcript = (data.get("transcript") or "").strip()
    if not transcript:
        return _json({"ok": False, "error": "input_vacio"}, 400)
    if len(transcript) > 4000:
        return _json({"ok": False, "error": "payload_too_large"}, 413)

    t0 = time.monotonic()
    intent = await route_intent(
        transcript, autor_jwt, contexts_permitidos=contexts_permitidos,
    )
    tool_result = _execute_intent(intent, transcript, autor_jwt, device,
                                  contexto=ctx_raw)
    voice_text = compose_voice_response(
        intent.tool, intent.args, tool_result, autor_jwt
    )
    # 008 fix-mobile: sintetizar audio Piper para que Claudio CONTESTE POR VOZ
    audio_url = sintetizar(voice_text) if voice_text else None
    voice = {"text": voice_text, "audio_url": audio_url}
    latency_ms = int((time.monotonic() - t0) * 1000)
    ok = not (tool_result or "").lstrip().startswith("❌")
    _log_dictado(
        autor=autor_jwt, transcript=transcript, intent=intent,
        tool_result=tool_result, latency_ms=latency_ms, device=device,
        ok=ok,
    )

    return _json({
        "ok": True,
        "intent": {
            "tool": intent.tool,
            "args": intent.args,
            "confidence": round(intent.confidence, 3),
            "fallback": intent.fallback,
            "cached": intent.cached,
        },
        "tool_result": tool_result,
        "voice_response": voice,
        "latency_ms": latency_ms,
    })


ROUTES = [
    Route("/voz/api/capturar", capturar_handler, methods=["POST"]),
    Route("/voz/api/capturar", options_handler, methods=["OPTIONS"]),
    Route("/voz/api/contexto", contexto_handler, methods=["GET"]),
    Route("/voz/api/contexto", options_handler, methods=["OPTIONS"]),
    Route("/voz/api/buscar", buscar_handler, methods=["GET"]),
    Route("/voz/api/buscar", options_handler, methods=["OPTIONS"]),
    Route("/voz/api/dictado-procesar", dictado_procesar_handler, methods=["POST"]),
    Route("/voz/api/dictado-procesar", options_handler, methods=["OPTIONS"]),
    Route("/voz/api/health", health_handler, methods=["GET"]),
]


def montar_en_fastmcp(mcp_app) -> None:
    """Monta las rutas REST en el HTTP app de FastMCP.

    FastMCP 3.x expone su Starlette app vía .http_app() o atributo similar.
    Esta función es defensiva: si la API cambia entre versiones, loguea
    un warning pero no rompe el arranque.
    """
    try:
        # FastMCP 3.x — http_app es una propiedad/método
        candidates = [
            getattr(mcp_app, "http_app", None),
            getattr(mcp_app, "_http_app", None),
            getattr(mcp_app, "app", None),
        ]
        app = None
        for c in candidates:
            if c is None:
                continue
            app = c() if callable(c) else c
            if app and hasattr(app, "router"):
                break
        if app is None or not hasattr(app, "router"):
            log.warning("No pude localizar app HTTP de FastMCP — REST no montado")
            return
        for r in ROUTES:
            app.router.routes.append(r)
        log.info(f"REST montado: {len(ROUTES)} rutas bajo /voz/api/")
    except Exception as e:
        log.exception(f"Error montando REST: {e}")
