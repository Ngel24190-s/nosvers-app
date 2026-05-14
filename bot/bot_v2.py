#!/usr/bin/env python3
"""
NosVers HQ Bot v2 — @nosvers_hq_bot
Bot conversacional con tool-use para Angel y África.
Comandos: /statut, /pendiente, /vault, /agentes, /run, /logs
Mensajes libres: conversación natural con Claude + herramientas.
"""

import os, json, logging, subprocess, requests, sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Claudio Jarvis tools (proyecto 005)
sys.path.insert(0, '/home/nosvers')
try:
    from claudio_tools.finanzas import gasto_anotar as _claudio_gasto_anotar
    from claudio_tools.compras import lista_compras_añadir as _claudio_compra_anadir
    from claudio_tools.familia import recordatorio_crear as _claudio_recordatorio_crear
    from claudio_tools.common import parse_date_natural as _claudio_parse_date
    _CLAUDIO_OK = True
except Exception as _claudio_err:
    _CLAUDIO_OK = False
    _claudio_import_err = _claudio_err

# Config
load_dotenv('/home/nosvers/.env')
TOKEN = os.getenv('TELEGRAM_TOKEN')
ANGEL_ID = int(os.getenv('ANGEL_CHAT_ID', '5752097691'))
ANGEL_PROXY_ID = 1087968824
AFRICA_CHAT_ID = int(os.getenv('AFRICA_CHAT_ID', '0'))
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')
WP_URL = os.getenv('WP_URL', 'https://nosvers.com/wp-json/wp/v2/')
WP_USER = os.getenv('WP_USER', '')
WP_PASS = os.getenv('WP_PASS', '')

NOTIF_DIR = Path('/home/nosvers/bot/notifications')
NOTIF_DIR.mkdir(exist_ok=True)
VAULT_DIR = Path('/home/nosvers/public_html/knowledge_base')
AGENTS_DIR = Path('/home/nosvers/agents')
VENV_PY = '/home/nosvers/venv/bin/python3'

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger('nosvers-bot')

chat_histories = {}

SYSTEM_NOSVERS = """Eres el asistente ejecutivo de NosVers, ferme lombricole en Neuvic, Dordogne.
Angel es el CEO, Africa es la experta de campo. Los dos son espanoles — habla siempre en espanol.
Tienes herramientas para: leer/escribir vault, ejecutar agentes, registrar inventario, ver estado del sistema.
Productos: Extrait Vivant 45EUR, Engrais Vert 9.90EUR, Lombricompost 5L 9.90EUR,
Atelier 85EUR, Club Sol Vivant 15EUR/mes, Guide du Sol Vivant 19EUR.
Objetivos: M3=600EUR/mes, M6=2000EUR/mes.
Usa las herramientas cuando sea necesario. No inventes datos."""

AUTHORIZED_USERS = {ANGEL_ID, ANGEL_PROXY_ID, AFRICA_CHAT_ID}

AGENTS_MAP = {
    'orchestrator': 'orchestrator.py',
    'visual': 'agt01_visual.py',
    'instagram': 'agt02_instagram.py',
    'seo': 'agt04_seo.py',
    'africa': 'agt05_africa.py',
    'infoproduct': 'agt06_infoproduct.py',
    'youtube': 'agt07_youtube.py',
    'facebook': 'agt08_facebook.py',
    'community': 'agt10_community.py',
    'analyste': 'agt_analyste.py',
    'berger': 'agt_berger.py',
    'directeur': 'agt_directeur.py',
    'eisenia': 'agt_eisenia.py',
    'infra': 'agt_infra.py',
    'ingham': 'agt_ingham.py',
}

# ── TOOLS PARA CLAUDE ─────────────────────────────────────

CLAUDE_TOOLS = [
    {
        "name": "vault_read",
        "description": "Leer un archivo de la vault NosVers. Categorias: contexto, agentes, operaciones, vers, compost, animaux, club, huerto, estudios, analytics.",
        "input_schema": {
            "type": "object",
            "properties": {
                "categoria": {"type": "string", "description": "Carpeta en la vault"},
                "archivo": {"type": "string", "description": "Nombre del archivo sin .md"}
            },
            "required": ["categoria", "archivo"]
        }
    },
    {
        "name": "vault_write",
        "description": "Escribir o actualizar un archivo en la vault. Usar para registrar datos de produccion, observaciones de campo, inventario, notas.",
        "input_schema": {
            "type": "object",
            "properties": {
                "categoria": {"type": "string"},
                "archivo": {"type": "string"},
                "contenido": {"type": "string"},
                "modo": {"type": "string", "enum": ["overwrite", "append"], "description": "append agrega al final, overwrite reemplaza"}
            },
            "required": ["categoria", "archivo", "contenido"]
        }
    },
    {
        "name": "vault_list",
        "description": "Listar archivos disponibles en una categoria de la vault.",
        "input_schema": {
            "type": "object",
            "properties": {
                "categoria": {"type": "string", "description": "Carpeta a listar (contexto, agentes, operaciones, etc.)"}
            },
            "required": ["categoria"]
        }
    },
    {
        "name": "run_agent",
        "description": "Ejecutar un agente de NosVers. Agentes disponibles: orchestrator, visual, instagram, seo, africa, infoproduct, youtube, facebook, community, analyste, berger, directeur, eisenia, infra, ingham.",
        "input_schema": {
            "type": "object",
            "properties": {
                "agent_name": {"type": "string"},
                "args": {"type": "string", "description": "Argumentos opcionales (ej: 'briefing', 'consult pregunta')"}
            },
            "required": ["agent_name"]
        }
    },
    {
        "name": "system_status",
        "description": "Obtener estado del sistema: RAM, disco, servicios, Docker, agentes activos.",
        "input_schema": {"type": "object", "properties": {}}
    },
    {
        "name": "register_harvest",
        "description": "Registrar una cosecha o produccion. Africa o Angel reportan: bac, cantidad, tipo de producto.",
        "input_schema": {
            "type": "object",
            "properties": {
                "bac": {"type": "string", "description": "Identificador del bac (bac1, bac2, ibc, etc.)"},
                "producto": {"type": "string", "description": "lombricompost, lombrithe, vers, etc."},
                "cantidad_kg": {"type": "number"},
                "notas": {"type": "string"}
            },
            "required": ["bac", "producto", "cantidad_kg"]
        }
    },
    {
        "name": "register_observation",
        "description": "Registrar observacion de campo: estado de bacs, animales, huerto, suelo, clima.",
        "input_schema": {
            "type": "object",
            "properties": {
                "zona": {"type": "string", "description": "bac1, bac2, ibc, huerto, gallinero, etc."},
                "observacion": {"type": "string"},
                "urgencia": {"type": "string", "enum": ["normal", "atencion", "urgente"]}
            },
            "required": ["zona", "observacion"]
        }
    }
]


def execute_tool(tool_name: str, tool_input: dict) -> str:
    """Ejecutar herramienta y devolver resultado."""
    try:
        if tool_name == 'vault_read':
            filepath = VAULT_DIR / tool_input['categoria'] / f"{tool_input['archivo']}.md"
            if filepath.exists():
                return filepath.read_text(encoding='utf-8', errors='replace')[:3000]
            # Buscar en subcarpetas
            base = VAULT_DIR / tool_input['categoria']
            for f in base.rglob(f"{tool_input['archivo']}.md"):
                return f.read_text(encoding='utf-8', errors='replace')[:3000]
            return f"Archivo no encontrado: {tool_input['categoria']}/{tool_input['archivo']}"

        elif tool_name == 'vault_write':
            dirpath = VAULT_DIR / tool_input['categoria']
            dirpath.mkdir(parents=True, exist_ok=True)
            filepath = dirpath / f"{tool_input['archivo']}.md"
            modo = tool_input.get('modo', 'append')
            if modo == 'append' and filepath.exists():
                with open(filepath, 'a', encoding='utf-8') as f:
                    f.write(f"\n\n---\n{datetime.now().strftime('%Y-%m-%d %H:%M')}\n{tool_input['contenido']}")
            else:
                filepath.write_text(tool_input['contenido'], encoding='utf-8')
            return f"OK — escrito en {tool_input['categoria']}/{tool_input['archivo']}.md"

        elif tool_name == 'vault_list':
            dirpath = VAULT_DIR / tool_input['categoria']
            if not dirpath.exists():
                return f"Categoria '{tool_input['categoria']}' no existe"
            files = sorted(f.stem for f in dirpath.rglob('*.md'))
            return '\n'.join(files) if files else "Sin archivos"

        elif tool_name == 'run_agent':
            agent_name = tool_input['agent_name']
            if agent_name not in AGENTS_MAP:
                return f"Agente '{agent_name}' no existe. Disponibles: {', '.join(AGENTS_MAP.keys())}"
            script = AGENTS_DIR / AGENTS_MAP[agent_name]
            args_str = tool_input.get('args', '')
            cmd = f"{VENV_PY} {script} {args_str}".strip()
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=120)
            output = (result.stdout + result.stderr)[:1500]
            return output if output.strip() else "Agente ejecutado sin output."

        elif tool_name == 'system_status':
            cmds = [
                "free -h | head -3",
                "df -h / | tail -1",
                "docker ps --format '{{.Names}}: {{.Status}}' 2>/dev/null",
                "systemctl is-active nosvers-bot nosvers-mcp nosvers-voice syncthing 2>/dev/null | paste - - - -"
            ]
            output = ""
            for cmd in cmds:
                r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
                output += r.stdout
            return output[:2000]

        elif tool_name == 'register_harvest':
            registro = (
                f"## Cosecha {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
                f"- Bac: {tool_input['bac']}\n"
                f"- Producto: {tool_input['producto']}\n"
                f"- Cantidad: {tool_input['cantidad_kg']} kg\n"
            )
            if tool_input.get('notas'):
                registro += f"- Notas: {tool_input['notas']}\n"
            dirpath = VAULT_DIR / 'operaciones'
            dirpath.mkdir(parents=True, exist_ok=True)
            filepath = dirpath / 'registro-produccion.md'
            with open(filepath, 'a', encoding='utf-8') as f:
                f.write(f"\n{registro}")
            return f"Cosecha registrada: {tool_input['cantidad_kg']}kg de {tool_input['producto']} del {tool_input['bac']}"

        elif tool_name == 'register_observation':
            urgencia = tool_input.get('urgencia', 'normal')
            icons = {'normal': '', 'atencion': '⚠️ ', 'urgente': '🚨 '}
            registro = (
                f"## {icons.get(urgencia, '')}{datetime.now().strftime('%Y-%m-%d %H:%M')} — {tool_input['zona']}\n"
                f"{tool_input['observacion']}\n"
            )
            dirpath = VAULT_DIR / 'operaciones'
            dirpath.mkdir(parents=True, exist_ok=True)
            filepath = dirpath / 'observaciones-campo.md'
            with open(filepath, 'a', encoding='utf-8') as f:
                f.write(f"\n{registro}")
            result = f"Observacion registrada: {tool_input['zona']}"
            if urgencia == 'urgente':
                # Notificar a Angel si es urgente y lo reporta África
                try:
                    requests.post(
                        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                        json={"chat_id": ANGEL_ID,
                              "text": f"🚨 URGENTE — {tool_input['zona']}\n{tool_input['observacion']}"}
                    )
                except:
                    pass
                result += " + alerta enviada a Angel"
            return result

        else:
            return f"Herramienta '{tool_name}' no reconocida"

    except Exception as e:
        return f"Error ejecutando {tool_name}: {str(e)[:200]}"


# ── FUNCIONES AUXILIARES ──────────────────────────────────

def is_authorized(user_id: int, update=None) -> bool:
    extra = ""
    if update and update.effective_user:
        u = update.effective_user
        extra = f" name={u.first_name} username={u.username}"
    if update and update.effective_chat:
        extra += f" chat_id={update.effective_chat.id}"
    logger.info(f"[AUTH] user_id={user_id}{extra} authorized={user_id in AUTHORIZED_USERS}")
    return user_id in AUTHORIZED_USERS


def get_pending_notifications():
    notifs = []
    for f in sorted(NOTIF_DIR.glob('*.txt')):
        notifs.append(f.read_text())
        f.unlink()
    return notifs


async def deliver_notifications(update: Update):
    for notif in get_pending_notifications():
        try:
            await update.message.reply_text(notif, parse_mode='Markdown')
        except:
            await update.message.reply_text(notif)


# ── COMANDOS ──────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id, update):
        return
    await deliver_notifications(update)
    await update.message.reply_text(
        "🌿 *NosVers HQ*\n\n"
        "Escribe lo que necesites en lenguaje natural.\n\n"
        "*Ejemplos:*\n"
        "• _como van las ventas_\n"
        "• _he cosechado 5kg del bac 1_\n"
        "• _lanza el agente instagram_\n"
        "• _estado del sistema_\n\n"
        "*Comandos directos:*\n"
        "/statut /pendiente /vault /agentes /run /logs\n",
        parse_mode='Markdown'
    )


async def notificaciones(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id, update):
        return
    notifs = get_pending_notifications()
    if not notifs:
        await update.message.reply_text("Sin notificaciones pendientes.")
        return
    for n in notifs:
        try:
            await update.message.reply_text(n, parse_mode='Markdown')
        except:
            await update.message.reply_text(n)


async def statut(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id, update):
        return
    await deliver_notifications(update)
    await update.message.reply_chat_action("typing")
    parts = ["🌿 *Estado NosVers*\n"]
    try:
        r = subprocess.run("free -h | awk 'NR==2{print $3\"/\"$2}'", shell=True, capture_output=True, text=True, timeout=5)
        parts.append(f"RAM: {r.stdout.strip()}")
    except:
        pass
    try:
        r = subprocess.run("df -h / | awk 'NR==2{print $3\"/\"$2\" (\"$5\")\"}'", shell=True, capture_output=True, text=True, timeout=5)
        parts.append(f"Disco: {r.stdout.strip()}")
    except:
        pass
    try:
        r = subprocess.run("uptime -p", shell=True, capture_output=True, text=True, timeout=5)
        parts.append(f"Uptime: {r.stdout.strip()}")
    except:
        pass
    try:
        r = subprocess.run("docker ps --format '{{.Names}}: {{.Status}}' 2>/dev/null", shell=True, capture_output=True, text=True, timeout=5)
        if r.stdout.strip():
            parts.append(f"\n*Docker:*\n```\n{r.stdout.strip()}\n```")
    except:
        pass
    try:
        services = ['nosvers-bot', 'nosvers-mcp', 'nosvers-voice', 'syncthing']
        svc_status = []
        for s in services:
            r = subprocess.run(f"systemctl is-active {s}", shell=True, capture_output=True, text=True, timeout=3)
            icon = '✅' if r.stdout.strip() == 'active' else '❌'
            svc_status.append(f"{icon} {s}")
        parts.append(f"\n*Servicios:*\n" + '\n'.join(svc_status))
    except:
        pass
    try:
        agent_count = len(list(AGENTS_DIR.glob('agt*.py')))
        vault_count = len(list(VAULT_DIR.rglob('*.md')))
        parts.append(f"\nAgentes: {agent_count} | Vault: {vault_count} archivos")
    except:
        pass
    try:
        await update.message.reply_text('\n'.join(parts), parse_mode='Markdown')
    except:
        await update.message.reply_text('\n'.join(parts))


async def pendiente(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id, update):
        return
    await update.message.reply_chat_action("typing")
    filepath = VAULT_DIR / 'agentes' / 'agt05_africa' / '_taches.md'
    if filepath.exists():
        content = filepath.read_text(encoding='utf-8', errors='replace')[:3000]
        try:
            taches = json.loads(content)
            pending = [t for t in taches if not t.get('done')]
            if pending:
                msg = "📋 *Tareas pendientes:*\n\n"
                for t in pending[:8]:
                    icon = {'rouge':'🔴','orange':'🟠','jaune':'🟡','vert':'🟢'}.get(t.get('priorite',''),'🟡')
                    msg += f"{icon} {t.get('titre','?')} ({t.get('duree_min','?')}min)\n"
                await update.message.reply_text(msg, parse_mode='Markdown')
                return
        except:
            pass
    await update.message.reply_text("Sin tareas pendientes registradas.")


async def vault(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id, update):
        return
    cats = sorted(d.name for d in VAULT_DIR.iterdir() if d.is_dir())
    msg = "📂 *Vault NosVers*\n\n"
    for cat in cats:
        count = len(list((VAULT_DIR / cat).rglob('*.md')))
        msg += f"• `{cat}/` ({count} archivos)\n"
    msg += "\nUsa: `/vault_read categoria archivo`"
    try:
        await update.message.reply_text(msg, parse_mode='Markdown')
    except:
        await update.message.reply_text(msg)


async def vault_read_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id, update):
        return
    if not context.args or len(context.args) < 2:
        await update.message.reply_text("Uso: /vault_read categoria archivo")
        return
    cat, archivo = context.args[0], context.args[1]
    result = execute_tool('vault_read', {'categoria': cat, 'archivo': archivo})
    if len(result) > 4000:
        result = result[:4000] + "\n_(truncado)_"
    await update.message.reply_text(result)


async def agentes_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id, update):
        return
    await update.message.reply_chat_action("typing")
    msg = "🤖 *Agentes NosVers*\n\n"
    for name, script in sorted(AGENTS_MAP.items()):
        log_file = AGENTS_DIR / script.replace('.py', '.log')
        if not log_file.exists():
            log_file = Path(f'/home/nosvers/logs/{script.replace(".py", ".log")}')
        if log_file.exists():
            try:
                last_line = log_file.read_text(errors='replace').strip().split('\n')[-1][:80]
                msg += f"✅ *{name}*: {last_line}\n"
            except:
                msg += f"✅ *{name}*: log existente\n"
        else:
            msg += f"⬚ *{name}*: sin log reciente\n"
    try:
        await update.message.reply_text(msg, parse_mode='Markdown')
    except:
        await update.message.reply_text(msg)


async def run_agent_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id, update):
        return
    if not context.args:
        await update.message.reply_text(f"Uso: /run agente\nDisponibles: {', '.join(AGENTS_MAP.keys())}")
        return
    agent_name = context.args[0].lower()
    args_str = ' '.join(context.args[1:]) if len(context.args) > 1 else ''
    await update.message.reply_text(f"⏳ Ejecutando {agent_name}...")
    result = execute_tool('run_agent', {'agent_name': agent_name, 'args': args_str})
    if len(result) > 4000:
        result = result[:4000] + "\n_(truncado)_"
    await update.message.reply_text(f"✅ *{agent_name}:*\n{result}", parse_mode='Markdown')


async def logs_agent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id, update):
        return
    if not context.args:
        await update.message.reply_text(f"Uso: /logs agente\nDisponibles: {', '.join(AGENTS_MAP.keys())}")
        return
    agent_name = context.args[0].lower()
    if agent_name not in AGENTS_MAP:
        await update.message.reply_text(f"Agente '{agent_name}' no existe.")
        return
    log_name = AGENTS_MAP[agent_name].replace('.py', '.log')
    for log_dir in [AGENTS_DIR, Path('/home/nosvers/logs')]:
        log_file = log_dir / log_name
        if log_file.exists():
            content = log_file.read_text(errors='replace')
            if len(content) > 3000:
                content = "...\n" + content[-3000:]
            try:
                await update.message.reply_text(f"📋 *{agent_name}:*\n```\n{content}\n```", parse_mode='Markdown')
            except:
                await update.message.reply_text(content[:4000])
            return
    await update.message.reply_text(f"Sin logs para {agent_name}")


# ── CONVERSACIÓN PRINCIPAL (con tool-use) ─────────────────

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Conversacion natural con Claude + herramientas."""
    if not is_authorized(update.effective_user.id, update):
        return
    await deliver_notifications(update)

    if not ANTHROPIC_API_KEY:
        await update.message.reply_text("ANTHROPIC_API_KEY no configurada")
        return

    user_id = update.effective_user.id
    chat_id = str(update.message.chat.id)
    msg_text = update.message.text.strip()
    if not msg_text:
        return

    # Historial
    if chat_id not in chat_histories:
        chat_histories[chat_id] = []
    chat_histories[chat_id].append({"role": "user", "content": msg_text})
    chat_histories[chat_id] = chat_histories[chat_id][-10:]

    await update.message.reply_chat_action("typing")

    # Perfil diferenciado
    is_africa = (user_id == AFRICA_CHAT_ID)
    perfil = "\nHablas con Africa, experta de campo. Tono: companera, complice." if is_africa else "\nHablas con Angel, CEO. Tono: directo, estrategico."

    # Contexto vault ligero (siempre)
    vault_snippet = ""
    for cat, arch in [('contexto', 'nosvers-identidad'), ('operaciones', 'semana-actual')]:
        fp = VAULT_DIR / cat / f"{arch}.md"
        if fp.exists():
            try:
                vault_snippet += fp.read_text(encoding='utf-8', errors='replace')[:800] + "\n"
            except:
                pass

    system = SYSTEM_NOSVERS + perfil
    if vault_snippet:
        system += f"\n\nContexto base:\n{vault_snippet[:1500]}"

    headers = {
        'x-api-key': ANTHROPIC_API_KEY,
        'anthropic-version': '2023-06-01',
        'anthropic-beta': 'advisor-tool-2026-03-01',
        'content-type': 'application/json',
    }
    advisor_tool = {
        'type': 'advisor_20260301',
        'name': 'advisor',
        'model': 'claude-opus-4-6',
        'max_uses': 2
    }
    api_payload = {
        'model': 'claude-haiku-4-5',
        'max_tokens': 1200,
        'system': system,
        'messages': list(chat_histories[chat_id]),
        'tools': CLAUDE_TOOLS + [advisor_tool]
    }

    try:
        final_reply = None
        for _turn in range(4):
            r = requests.post('https://api.anthropic.com/v1/messages',
                headers=headers, json=api_payload, timeout=90)

            if r.status_code != 200:
                await update.message.reply_text(f"API error: {r.status_code} — {r.text[:200]}")
                return

            resp = r.json()
            stop_reason = resp.get('stop_reason', '')

            if stop_reason == 'tool_use':
                assistant_content = resp['content']
                api_payload['messages'].append({"role": "assistant", "content": assistant_content})

                tool_results = []
                for block in assistant_content:
                    if block.get('type') == 'tool_use':
                        name = block['name']
                        inp = block['input']
                        logger.info(f"[TOOL] {name}: {json.dumps(inp, ensure_ascii=False)[:120]}")
                        result = execute_tool(name, inp)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block['id'],
                            "content": result[:3000]
                        })

                api_payload['messages'].append({"role": "user", "content": tool_results})
                await update.message.reply_chat_action("typing")
                continue

            # Respuesta final de texto
            text_parts = [b['text'] for b in resp['content'] if b.get('type') == 'text']
            final_reply = '\n'.join(text_parts)
            break

        if not final_reply:
            final_reply = "Accion completada."

        chat_histories[chat_id].append({"role": "assistant", "content": final_reply})
        chat_histories[chat_id] = chat_histories[chat_id][-10:]

        if len(final_reply) > 4000:
            final_reply = final_reply[:4000] + "\n_(truncado)_"

        try:
            await update.message.reply_text(final_reply, parse_mode="Markdown")
        except:
            await update.message.reply_text(final_reply)

    except Exception as e:
        logger.error(f"[BOT] Error: {e}")
        await update.message.reply_text(f"Error: {str(e)[:200]}")


# ── CLAUDIO JARVIS HOOKS (proyecto 005) ───────────────────

_GASTO_CATS = {
    'alimentacion', 'transporte', 'coche', 'hogar', 'ocio', 'salud',
    'nosvers', 'ropa', 'regalos', 'viajes', 'otros',
}


def _autor_from_user(user_id: int) -> str:
    """Mapea Telegram user_id → autor para los tools claudio."""
    if user_id == AFRICA_CHAT_ID:
        return 'africa'
    return 'angel'


async def gasto_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/gasto <monto> <concepto...> [categoria]"""
    if not is_authorized(update.effective_user.id, update):
        return
    if not _CLAUDIO_OK:
        await update.message.reply_text(f"claudio_tools no disponible: {_claudio_import_err}")
        return
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "Uso: /gasto <monto> <concepto> [categoria]\n"
            "Ejemplo: /gasto 45 gasolina coche"
        )
        return
    try:
        monto = float(context.args[0].replace(',', '.'))
    except ValueError:
        await update.message.reply_text(f"Monto inválido: {context.args[0]}")
        return
    resto = list(context.args[1:])
    categoria = 'otros'
    if resto and resto[-1].lower() in _GASTO_CATS:
        categoria = resto.pop().lower()
    concepto = ' '.join(resto).strip()
    if not concepto:
        await update.message.reply_text("Falta el concepto del gasto.")
        return
    autor = _autor_from_user(update.effective_user.id)
    out = _claudio_gasto_anotar(monto, concepto, categoria, autor)
    await update.message.reply_text(out)


async def compra_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/compra <item> [...]  → añade a lista de compra. Prefijo '!' = urgente."""
    if not is_authorized(update.effective_user.id, update):
        return
    if not _CLAUDIO_OK:
        await update.message.reply_text(f"claudio_tools no disponible: {_claudio_import_err}")
        return
    if not context.args:
        await update.message.reply_text(
            "Uso: /compra <item> [cantidad]\n"
            "Ejemplo: /compra leche  ·  /compra ! pilas AA"
        )
        return
    args = list(context.args)
    urgente = False
    if args and args[0] in ('!', '!!'):
        urgente = True
        args = args[1:]
    if not args:
        await update.message.reply_text("Falta el item.")
        return
    # Heurística: si último token es "(cantidad)" o termina en kg/g/L → cantidad
    cantidad = ''
    if len(args) > 1:
        last = args[-1]
        if last.startswith('(') and last.endswith(')'):
            cantidad = last.strip('()')
            args = args[:-1]
    item = ' '.join(args).strip()
    autor = _autor_from_user(update.effective_user.id)
    out = _claudio_compra_anadir(item, autor, cantidad=cantidad, urgente=urgente)
    await update.message.reply_text(out)


async def recordar_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/recordar [fecha] <texto>  — fecha 'hoy', 'mañana', 'YYYY-MM-DD' o día semana."""
    if not is_authorized(update.effective_user.id, update):
        return
    if not _CLAUDIO_OK:
        await update.message.reply_text(f"claudio_tools no disponible: {_claudio_import_err}")
        return
    if not context.args:
        await update.message.reply_text(
            "Uso: /recordar <fecha> <texto>  o  /recordar <texto> (hoy)\n"
            "Ejemplos:\n"
            "  /recordar 2026-06-12 cumpleaños Lucía\n"
            "  /recordar mañana llamar fontanero\n"
            "  /recordar revisar agua de los bacs"
        )
        return
    raw = ' '.join(context.args).strip()
    fecha, resto = _claudio_parse_date(raw)
    if fecha is None:
        # No se pudo extraer fecha → asumir hoy
        from datetime import date as _date
        fecha = _date.today()
        texto = raw
    else:
        texto = resto
    if not texto:
        await update.message.reply_text(
            f"Falta el texto del recordatorio (fecha detectada: {fecha.isoformat()})"
        )
        return
    autor = _autor_from_user(update.effective_user.id)
    out = _claudio_recordatorio_crear(texto, fecha.isoformat(), autor, prioridad=3)
    await update.message.reply_text(out)


# ── MAIN ──────────────────────────────────────────────────

def main():
    if not TOKEN:
        logger.error("TELEGRAM_TOKEN no configurado")
        return

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("statut", statut))
    app.add_handler(CommandHandler("pendiente", pendiente))
    app.add_handler(CommandHandler("vault", vault))
    app.add_handler(CommandHandler("vault_read", vault_read_cmd))
    app.add_handler(CommandHandler("agentes", agentes_status))
    app.add_handler(CommandHandler("notificaciones", notificaciones))
    app.add_handler(CommandHandler("run", run_agent_cmd))
    app.add_handler(CommandHandler("logs", logs_agent))
    # Claudio Jarvis hooks (proyecto 005)
    app.add_handler(CommandHandler("gasto", gasto_cmd))
    app.add_handler(CommandHandler("compra", compra_cmd))
    app.add_handler(CommandHandler("recordar", recordar_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("NosVers HQ Bot v2 arrancado")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
