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


# Archivos/paths con credenciales — Claudio NUNCA debe leerlos ni siquiera para Angel
SENSITIVE_FILE_PATTERNS = [
    r'\.env(\.|$|\s|\b)',
    r'\.key(\s|\b|$)',
    r'\.pem(\s|\b|$)',
    r'\bid_rsa\b',
    r'\bid_ed25519\b',
    r'\bid_ecdsa\b',
    r'tokens\.sqlite',
    r'sessions\.sqlite',
    r'\.secret(s)?(\s|\b|$)',
    r'\.aws/credentials',
    r'\.ssh/(?!known_hosts|config\b)[^/\s]+',
    r'mcp_credentials',
    r'\bjwt_secret\b',
    r'\bapi_key\b',
    r'\bclient_secret\b',
]

# Variables de entorno con credenciales
SENSITIVE_ENV_VARS = [
    'ANTHROPIC_API_KEY', 'OPENAI_API_KEY', 'STRIPE_SECRET_KEY', 'STRIPE_API_KEY',
    'STRIPE_LIVE_KEY', 'TELEGRAM_TOKEN', 'TELEGRAM_BOT_TOKEN', 'VOZ_JWT_SECRET',
    'WP_PASS', 'WP_PASSWORD', 'HF_TOKEN', 'HUGGINGFACE_TOKEN', 'GITHUB_TOKEN',
    'GITHUB_PAT', 'PAT', 'GOOGLE_API_KEY', 'AWS_SECRET_ACCESS_KEY',
    'AWS_ACCESS_KEY_ID', 'AHREFS_API_KEY', 'GOOGLE_CLIENT_SECRET',
    'OAUTH_CLIENT_SECRET', 'MCP_TOKEN', 'JWT_SECRET',
]


def comando_lee_secretos(comando: str) -> tuple[bool, str]:
    """Detecta intentos de leer archivos o variables sensibles. Capa 2."""
    c = comando.lower()
    # Comandos lectores típicos sobre archivos
    for pattern in SENSITIVE_FILE_PATTERNS:
        if re.search(pattern, comando, re.IGNORECASE):
            # ¿Es comando de lectura? cat/less/more/head/tail/grep/awk/sed/cp/scp/python con read
            if re.search(r'\b(cat|less|more|head|tail|grep|awk|sed|nano|vi|vim|cp|scp|rsync|tar|zip|base64|xxd|od|strings|hexdump)\b', c) or \
               re.search(r'\b(open|read|read_text|read_bytes|loads?)\b\s*\(.{0,100}\.env', c) or \
               re.search(r'\bsource\b', c) or \
               'curl' in c and any(s in comando for s in ['file://', '/home/nosvers/.env', '/.env']):
                return True, f"archivo sensible ({pattern})"
    # Variables sensibles via printenv/env/echo/printf
    for var in SENSITIVE_ENV_VARS:
        if re.search(rf'\$\{{?{var}\b', comando) or \
           re.search(rf'\bprintenv\b.{{0,40}}\b{var}\b', comando, re.IGNORECASE) or \
           re.search(rf'\benv\b.{{0,40}}\b{var}\b', comando, re.IGNORECASE):
            return True, f"variable sensible (${var})"
    # Dump masivo de env
    if re.search(r'\b(printenv|env|set)\b\s*($|\|\s*(grep|less|head|tail|cat))', c):
        return True, "dump de variables de entorno"
    return False, ""


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
    {
        "name": "claude_code_lanzar",
        "description": "Lanza Claude Code (claude-code CLI) en una sesión tmux para que programe un proyecto complejo, escriba código, refactorice o implemente features. SOLO Angel puede invocarla. ÚSALA cuando el usuario pida 'lanza code', 'que code haga X', 'arranca un proyecto', 'programa Y', 'desarrolla Z'. Especifica un brief detallado con qué debe hacer Claude Code (Spec Kit completo: specify, plan, tasks, implement).",
        "input_schema": {
            "type": "object",
            "properties": {
                "brief": {"type": "string", "description": "Brief detallado del proyecto. Incluye objetivo, archivos a tocar, constraints, definition of done. Mínimo 200 caracteres."},
                "nombre_proyecto": {"type": "string", "description": "Slug del proyecto (solo a-z 0-9 guiones, max 40 chars). Ej: 'widget-stripe', 'fix-bot-telegram', 'agente-noticias'"},
            },
            "required": ["brief", "nombre_proyecto"],
        },
    },
]

# Clasificación de tools por nivel de acceso
TOOLS_READ_ONLY = {"sistema_estado", "agentes_estado", "agente_logs",
                   "vault_leer", "vault_listar", "dia_buscar"}
TOOLS_WRITE = {"vault_escribir"}  # acepta África pero registrada
TOOLS_DESTRUCTIVE_ANGEL_ONLY = {"agente_ejecutar", "ejecutar_comando", "git_pull_vps", "claude_code_lanzar"}


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

    # Filter de comandos peligrosos (Capa 1) + lectura de secretos (Capa 2)
    if name == "ejecutar_comando":
        comando = tool_input.get("comando", "")
        peligroso, razon = comando_es_peligroso(comando)
        if peligroso:
            return {"ok": False, "error": f"Comando bloqueado por seguridad: {razon}"}
        lee_secretos, razon2 = comando_lee_secretos(comando)
        if lee_secretos:
            log.warning(f"BLOQUEO Capa 2: {autor} intentó {razon2} con: {comando[:80]}")
            return {"ok": False, "error": f"Lectura de secretos bloqueada (Capa 2): {razon2}. Las credenciales NO se exponen via voz."}

    # vault_leer Capa 2 (por si la categoría/archivo se cuela)
    if name == "vault_leer":
        path_test = f"{tool_input.get('categoria','')}/{tool_input.get('archivo','')}"
        lee_secretos, razon2 = comando_lee_secretos(path_test)
        if lee_secretos:
            log.warning(f"BLOQUEO Capa 2 vault_leer: {autor} intentó {razon2}")
            return {"ok": False, "error": f"Lectura bloqueada (Capa 2): {razon2}"}

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
        elif name == "claude_code_lanzar":
            return _ejecutar_claude_code(tool_input.get("brief", ""),
                                         tool_input.get("nombre_proyecto", ""))
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




# ─── HELPER: Lanzar Claude Code en tmux ────────────────────────────

def _ejecutar_claude_code(brief: str, nombre_proyecto: str) -> dict:
    """Crea spec dir + BRIEF.md + lanza tmux con claude-code en modo remote-control."""
    import subprocess, re
    from pathlib import Path

    if len(brief) < 100:
        return {"ok": False, "error": "brief demasiado corto (min 100 chars)"}

    nombre = re.sub(r"[^a-z0-9-]+", "-", nombre_proyecto.lower()).strip("-")[:40]
    if not nombre:
        return {"ok": False, "error": "nombre_proyecto invalido"}

    spec_dir = Path(f"/home/nosvers/specs/claudio-{nombre}")
    spec_dir.mkdir(parents=True, exist_ok=True)
    (spec_dir / "BRIEF.md").write_text(brief, encoding="utf-8")

    session = f"spec-claudio-{nombre}"
    subprocess.run(["tmux", "kill-session", "-t", session], capture_output=True)
    subprocess.run(["setsid", "tmux", "new-session", "-d",
                    "-s", session, "-c", str(spec_dir)], check=True)

    subprocess.run(["tmux", "send-keys", "-t", session,
                    "unset ANTHROPIC_API_KEY && claude", "Enter"])
    time.sleep(9)
    subprocess.run(["tmux", "send-keys", "-t", session,
                    "/remote-control", "Enter"])
    time.sleep(4)
    subprocess.run(["tmux", "send-keys", "-t", session, "", "Enter"])
    time.sleep(5)

    prompt = ("Lee BRIEF.md entero. Arranca el proyecto sin parar (Spec Kit: "
              "specify, plan, tasks, implement). Bug telegram conocido: NO "
              "uses telegram_enviar intermedio. Commit + push al terminar.")
    subprocess.run(["tmux", "send-keys", "-t", session, prompt])
    time.sleep(2)
    subprocess.run(["tmux", "send-keys", "-t", session, "Enter"])
    time.sleep(8)

    cap = subprocess.run(["tmux", "capture-pane", "-t", session, "-p"],
                          capture_output=True, text=True)
    m = re.search(r"session_[a-zA-Z0-9]+", cap.stdout)
    session_id = m.group(0) if m else "?"

    return {
        "ok": True,
        "result": (f"Claude Code lanzado proyecto {nombre} session {session_id} "
                   f"tmux {session} URL https://claude.ai/code/{session_id}")
    }


# ─── AGENTIC LOOP ─────────────────────────────────────────────────

SYSTEM_AGENTIC = (
    "Eres Claudio, asistente AGÉNTICO de Angel y África. Hablas español castellano "
    "peninsular SIEMPRE, breve y directo. Tienes manos en el VPS NosVers: puedes "
    "ejecutar agentes, comandos bash, leer/escribir vault, hacer git pull, "
    "lanzar Claude Code para proyectos complejos.\n\n"
    "REGLAS IMPORTANTES:\n"
    "- ACTÚA, no expliques teoría. Si el usuario pide algo concreto → USA tools. "
    "Nunca digas 'tendrías que ir a...' o 'puedes hacer...' — HAZLO TÚ.\n"
    "- Si pide programar / desarrollar / refactorizar / crear un agente nuevo / "
    "implementar feature → usa claude_code_lanzar con brief detallado.\n"
    "- Si pide algo simple (ver estado, ejecutar agente, leer archivo) → usa la "
    "tool directa, no Code.\n"
    "- Después de ejecutar, responde BREVE (2-3 frases máx). RESUME el resultado, "
    "NO copies la salida cruda. Si fue un comando bash con muchas líneas, "
    "interpreta y di 'todo OK' o señala lo importante.\n"
    "- Si no necesitas tools (saludo, charla, opinión), responde directo.\n"
    "- Si África pide algo destructive (lanzar agente, ejecutar comando, lanzar "
    "Code), recházalo amablemente y sugiérele pedírselo a Angel.\n"
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
