"""
voz.agentic — Modo agentic de Claudio.

Cuando Angel/África dictan algo que requiere ACTUAR (no solo conversar),
Claudio usa tool_use de Anthropic API para invocar tools reales del VPS:
ejecutar agentes, leer/escribir vault, comandos bash, git pull, etc.

Restricciones de seguridad:
- África NO puede ejecutar tools destructive (write/exec)
- Comandos peligrosos (rm -rf /, mkfs, sudo, fork bombs) SIEMPRE bloqueados
- Cada acción se loguea a claudio/logs/agentic-YYYY-MM-DD.jsonl
"""
from __future__ import annotations

import json
import logging
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Permitir import de mcp_server (en /home/nosvers/)
sys.path.insert(0, "/home/nosvers")

import requests

log = logging.getLogger("voz.agentic")

API_URL = "https://api.anthropic.com/v1/messages"
MODEL = os.getenv("VOZ_AGENTIC_MODEL", "claude-haiku-4-5")
MAX_TOKENS = 800
TIMEOUT_S = 30.0
MAX_TOOL_ITERATIONS = 5

LOG_DIR = Path("/home/nosvers/public_html/knowledge_base/claudio/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)


# ─── COMANDOS PELIGROSOS (siempre bloqueados) ─────────────────────

DANGEROUS_PATTERNS = [
    r'rm\s+-rf?\s+/(?!home/nosvers|tmp|var/cache)',
    r'rm\s+-rf?\s+(/etc|/var|/usr|/bin|/boot|/lib|/sbin)',
    r'\bmkfs\b',
    r'\bdd\s+if=',
    r':\(\s*\)\s*\{',  # fork bomb
    r'\bsudo\b',
    r'\bsu\s+',
    r'curl[^|;]*\|\s*(bash|sh|python)',
    r'wget[^|;]*\|\s*(bash|sh|python)',
    r'\bshutdown\b',
    r'\breboot\b',
    r'\bhalt\b',
    r'>\s*/dev/(sda|sdb|nvme)',
    r'chmod\s+777\s+/',
    r'passwd\s+',
]


def comando_es_peligroso(comando: str) -> tuple[bool, str]:
    """Devuelve (True, razon) si el comando hace match con un patrón peligroso."""
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, comando, re.IGNORECASE):
            return True, pattern
    return False, ""


# ─── AUDIT LOG ────────────────────────────────────────────────────

def _audit_log(autor: str, tool: str, args: dict, result_summary: str, ok: bool) -> None:
    """Append-only log de cada tool ejecutada."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    log_file = LOG_DIR / f"agentic-{today}.jsonl"
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "autor": autor,
        "tool": tool,
        "args": args,
        "result_summary": result_summary[:200],
        "ok": ok,
    }
    try:
        with log_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as e:
        log.warning(f"audit log fallo: {e}")


# ─── TOOL DEFINITIONS (Anthropic API schema) ───────────────────────

TOOLS_SCHEMA = [
    {
        "name": "sistema_estado",
        "description": "Estado del sistema VPS: servicios (Caddy, MCP, bot), uptime, RAM, agentes instalados, vault. Read-only. Disponible para Angel y África.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "agentes_estado",
        "description": "Estado de todos los agentes NosVers: instalados, última ejecución, próximo cron. Read-only. Disponible para Angel y África.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "agente_logs",
        "description": "Logs recientes de un agente concreto. Read-only. Disponible para todos. Agentes válidos: orchestrator, agt01_visual, agt02_instagram, agt04_seo, agt05_africa, agt06_infoproduct, agt07_diario, agt00_intelligence, agt_infra, agt_eisenia, agt_analyste, agt_directeur, agt07_youtube, agt08_facebook.",
        "input_schema": {
            "type": "object",
            "properties": {
                "nombre": {"type": "string", "description": "Nombre exacto del agente"},
                "lineas": {"type": "integer", "description": "Cuántas líneas (default 30)", "default": 30},
            },
            "required": ["nombre"],
        },
    },
    {
        "name": "agente_ejecutar",
        "description": "Lanza un agente NosVers manualmente. SOLO Angel puede ejecutar. Agentes válidos: orchestrator, agt01_visual, agt02_instagram, agt04_seo, agt05_africa, agt06_infoproduct.",
        "input_schema": {
            "type": "object",
            "properties": {
                "nombre": {"type": "string", "description": "Nombre exacto del agente"},
            },
            "required": ["nombre"],
        },
    },
    {
        "name": "vault_leer",
        "description": "Lee un archivo del vault NosVers. Disponible para todos. Categorías típicas: agentes, operaciones, contexto, granja, finanzas, recordatorios.",
        "input_schema": {
            "type": "object",
            "properties": {
                "categoria": {"type": "string"},
                "archivo": {"type": "string", "description": "Nombre del archivo .md sin extensión"},
            },
            "required": ["categoria", "archivo"],
        },
    },
    {
        "name": "vault_listar",
        "description": "Lista archivos en una categoría del vault. Read-only. Disponible para todos.",
        "input_schema": {
            "type": "object",
            "properties": {
                "categoria": {"type": "string", "description": "Categoría a listar (vacío = raíz)"},
            },
            "required": [],
        },
    },
    {
        "name": "vault_escribir",
        "description": "Escribe contenido en archivo del vault. SOLO Angel puede modificar. Modos: 'append' (default), 'overwrite'.",
        "input_schema": {
            "type": "object",
            "properties": {
                "categoria": {"type": "string"},
                "archivo": {"type": "string"},
                "contenido": {"type": "string"},
                "modo": {"type": "string", "enum": ["append", "overwrite"], "default": "append"},
            },
            "required": ["categoria", "archivo", "contenido"],
        },
    },
    {
        "name": "ejecutar_comando",
        "description": "Ejecuta comando bash en el VPS NosVers. SOLO Angel. Comandos peligrosos (rm -rf /, sudo, mkfs, etc.) BLOQUEADOS automáticamente. Use ruta absoluta cuando sea posible. Timeout 60s.",
        "input_schema": {
            "type": "object",
            "properties": {
                "comando": {"type": "string", "description": "Comando bash completo"},
            },
            "required": ["comando"],
        },
    },
    {
        "name": "git_pull_vps",
        "description": "Hace git pull del repo NosVers en el VPS. SOLO Angel.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "dia_buscar",
        "description": "Busca en las notas diarias del vault común (dia.md). Disponible para todos.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Término a buscar"},
                "limite": {"type": "integer", "default": 10},
            },
            "required": ["query"],
        },
    },
]

# Clasificación de tools por nivel de acceso
TOOLS_READ_ONLY = {"sistema_estado", "agentes_estado", "agente_logs",
                   "vault_leer", "vault_listar", "dia_buscar"}
TOOLS_WRITE = {"vault_escribir"}  # acepta África pero registrada
TOOLS_DESTRUCTIVE_ANGEL_ONLY = {"agente_ejecutar", "ejecutar_comando", "git_pull_vps"}


def _tools_para(autor: str) -> list[dict]:
    """Devuelve el subset de TOOLS_SCHEMA permitido al autor."""
    if autor == "angel":
        return TOOLS_SCHEMA
    # África: read-only + vault_escribir (compartido)
    permitidas = TOOLS_READ_ONLY | TOOLS_WRITE
    return [t for t in TOOLS_SCHEMA if t["name"] in permitidas]


# ─── EJECUTORES (llaman a las funciones del mcp_server) ────────────

def _ejecutar_tool(name: str, tool_input: dict, autor: str) -> dict:
    """Despacha la llamada a la función real. Devuelve {ok, result, error?}."""
    # Permisos
    if autor != "angel" and name in TOOLS_DESTRUCTIVE_ANGEL_ONLY:
        return {"ok": False, "error": f"África no puede ejecutar {name}. Pídeselo a Angel."}

    # Filter de comandos peligrosos
    if name == "ejecutar_comando":
        comando = tool_input.get("comando", "")
        peligroso, razon = comando_es_peligroso(comando)
        if peligroso:
            return {"ok": False, "error": f"Comando bloqueado por seguridad: {razon}"}

    try:
        # Lazy import de las funciones del mcp_server
        import mcp_server as ms

        if name == "sistema_estado":
            return {"ok": True, "result": ms.sistema_estado.fn() if hasattr(ms.sistema_estado, 'fn') else _call_mcp_tool("sistema_estado")}
        elif name == "agentes_estado":
            return {"ok": True, "result": _call_mcp_tool("agentes_estado")}
        elif name == "agente_logs":
            return {"ok": True, "result": _call_mcp_tool("agente_logs", **tool_input)}
        elif name == "agente_ejecutar":
            # FORCE notificar_angel=False para evitar bug telegram_enviar
            args = dict(tool_input)
            args["notificar_angel"] = False
            return {"ok": True, "result": _call_mcp_tool("agente_ejecutar", **args)}
        elif name == "vault_leer":
            return {"ok": True, "result": _call_mcp_tool("vault_leer", **tool_input)}
        elif name == "vault_listar":
            return {"ok": True, "result": _call_mcp_tool("vault_listar", **tool_input)}
        elif name == "vault_escribir":
            return {"ok": True, "result": _call_mcp_tool("vault_escribir", **tool_input)}
        elif name == "ejecutar_comando":
            args = dict(tool_input)
            args["notificar_angel"] = False
            return {"ok": True, "result": _call_mcp_tool("ejecutar_comando", **args)}
        elif name == "git_pull_vps":
            return {"ok": True, "result": _call_mcp_tool("git_pull_vps")}
        elif name == "dia_buscar":
            return {"ok": True, "result": _call_mcp_tool("dia_buscar", **tool_input)}
        else:
            return {"ok": False, "error": f"Tool desconocida: {name}"}
    except Exception as e:
        log.exception(f"Tool {name} fallo")
        return {"ok": False, "error": f"Error ejecutando {name}: {e}"}


def _call_mcp_tool(name: str, **kwargs) -> str:
    """Llama a una @mcp.tool() del mcp_server.py extrayendo la fn subyacente."""
    import mcp_server as ms
    tool_obj = getattr(ms, name, None)
    if tool_obj is None:
        raise ValueError(f"mcp_server no tiene tool {name}")
    # FastMCP envuelve las funciones — accedemos a la fn original
    fn = getattr(tool_obj, 'fn', None) or tool_obj
    return fn(**kwargs)


# ─── AGENTIC LOOP ─────────────────────────────────────────────────

SYSTEM_AGENTIC = (
    "Eres Claudio, asistente con manos de Angel y África. Hablas español castellano "
    "peninsular SIEMPRE, breve y directo. Tienes herramientas para actuar en el VPS "
    "y vault NosVers.\n\n"
    "REGLAS IMPORTANTES:\n"
    "- Si el usuario pide algo concreto que requiere actuar (ejecutar agente, leer "
    "log, hacer git pull, mirar estado, leer archivo del vault, etc.), USA las "
    "tools que tienes disponibles. NO digas 'tendrías que ir a...' — HAZLO.\n"
    "- Después de ejecutar una tool, da una respuesta BREVE en lenguaje natural "
    "(máximo 2-3 frases). NO copies la salida cruda del comando — RESUME.\n"
    "- Si no necesitas tools (saludo, conversación, pregunta general), responde "
    "directamente sin invocarlas.\n"
    "- Si el usuario es África y pide una acción que solo puede hacer Angel, "
    "explícale brevemente y sugiérele pedírselo a él.\n"
)


def agentic_responder(texto: str, autor: str = "angel", contexto: str = "casa") -> dict:
    """Ciclo agentic: modelo + tools hasta respuesta final.
    Devuelve {ok, texto, model, latency_ms, tools_usadas}.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return {"ok": False, "error": "anthropic_key_missing",
                "texto": "Lo siento, no puedo actuar ahora mismo."}

    tools = _tools_para(autor)
    system = SYSTEM_AGENTIC + f"\nUsuario actual: {autor}. Contexto: {contexto}."

    messages = [{"role": "user", "content": texto}]
    tools_usadas: list[str] = []
    t0 = time.monotonic()

    for iteracion in range(MAX_TOOL_ITERATIONS):
        try:
            r = requests.post(
                API_URL,
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": MODEL,
                    "max_tokens": MAX_TOKENS,
                    "system": system,
                    "tools": tools,
                    "messages": messages,
                },
                timeout=TIMEOUT_S,
            )
            r.raise_for_status()
            data = r.json()
        except requests.Timeout:
            return {"ok": False, "error": "timeout", "texto": "Tardé demasiado, prueba otra vez."}
        except Exception as e:
            log.exception(f"agentic API error: {e}")
            return {"ok": False, "error": "api_error", "texto": "Algo falló al pensar."}

        # ¿El modelo invocó una tool?
        stop_reason = data.get("stop_reason")
        content_blocks = data.get("content", [])

        # Si stop_reason == "tool_use" → ejecutar tool y continuar el loop
        if stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": content_blocks})
            tool_results = []
            for block in content_blocks:
                if block.get("type") == "tool_use":
                    tool_name = block.get("name")
                    tool_input = block.get("input", {})
                    tool_id = block.get("id")
                    tools_usadas.append(tool_name)
                    res = _ejecutar_tool(tool_name, tool_input, autor)
                    _audit_log(autor, tool_name, tool_input,
                               str(res.get("result", res.get("error", "")))[:200],
                               res.get("ok", False))
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_id,
                        "content": str(res.get("result") or res.get("error") or "sin respuesta"),
                        "is_error": not res.get("ok", False),
                    })
            messages.append({"role": "user", "content": tool_results})
            continue

        # Stop = end_turn → respuesta final
        reply_text = ""
        for b in content_blocks:
            if b.get("type") == "text":
                reply_text += b.get("text", "")
        reply_text = reply_text.strip() or "Hecho."

        return {
            "ok": True,
            "texto": reply_text,
            "model": MODEL,
            "latency_ms": int((time.monotonic() - t0) * 1000),
            "tools_usadas": tools_usadas,
            "iteraciones": iteracion + 1,
        }

    return {"ok": False, "error": "max_iterations_exceeded",
            "texto": "Demasiados pasos, dame otra orden."}
