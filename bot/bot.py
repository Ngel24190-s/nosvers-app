#!/usr/bin/env python3
"""
NosVers HQ Bot — @nosvers_hq_bot
Bot Telegram para comunicación con Angel (CEO)
Comandos: /statut, /pendiente, /vault, /agentes, /run, /ask
"""

import os
import json
import logging
import subprocess
import requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Config
load_dotenv('/home/nosvers/.env')
TOKEN = os.getenv('TELEGRAM_TOKEN')
ANGEL_ID = int(os.getenv('ANGEL_CHAT_ID', '5752097691'))
ANGEL_PROXY_ID = 1087968824  # Claude Code móvil proxy
APP_URL = os.getenv('APP_URL', 'https://nosvers.com/granja/api.php')
APP_TOKEN = os.getenv('APP_TOKEN', '')
WP_URL = os.getenv('WP_URL', 'https://nosvers.com/wp-json/wp/v2/')
WP_USER = os.getenv('WP_USER', '')
WP_PASS = os.getenv('WP_PASS', '')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')

NOTIF_DIR = Path('/home/nosvers/bot/notifications')
NOTIF_DIR.mkdir(exist_ok=True)

VAULT_DIR = Path('/home/nosvers/public_html/knowledge_base')
AGENTS_DIR = Path('/home/nosvers/agents')
VENV_PY = '/home/nosvers/venv/bin/python3'

# Claude bidireccional — historial por chat
chat_histories = {}

SYSTEM_NOSVERS = """Eres el Director Ejecutivo de NosVers, ferme lombricole en Neuvic, Dordogne.
Angel es el CEO. Responde SIEMPRE en español, directo y concreto.
Tienes acceso via MCP al VPS, vault, agentes y WordPress.
Estado: 7 agentes activos, vault operativa, MCP conectado.
Productos: Extrait Vivant 45€, Engrais Vert 9.90€, Atelier 85€, Club Sol Vivant 15€/mes.
Cuando Angel pregunte algo técnico del VPS → responde que lo ejecutarás via MCP en la próxima sesión Claude.ai.
Para consultas, contenido, estrategia → responde directamente."""

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('nosvers_bot')

AUTHORIZED_USERS = {ANGEL_ID, ANGEL_PROXY_ID}

AGENTS_MAP = {
    'orchestrator': 'orchestrator.py',
    'visual': 'agt01_visual.py',
    'instagram': 'agt02_instagram.py',
    'youtube': 'agt03_youtube.py',
    'seo': 'agt04_seo.py',
    'africa': 'agt05_africa.py',
    'infoproduct': 'agt06_infoproduct.py',
}


def is_authorized(user_id: int) -> bool:
    return user_id in AUTHORIZED_USERS


def get_pending_notifications():
    messages = []
    for f in sorted(NOTIF_DIR.glob('*.txt')):
        try:
            messages.append(f.read_text())
            f.unlink()
        except Exception:
            pass
    return messages


async def deliver_notifications(update: Update):
    notifications = get_pending_notifications()
    for msg in notifications:
        try:
            await update.message.reply_text(msg, parse_mode='Markdown')
        except Exception:
            await update.message.reply_text(msg)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        return
    await deliver_notifications(update)
    await update.message.reply_text(
        "🌿 *NosVers HQ Bot*\n\n"
        "*Consultas:*\n"
        "/statut — Estado del sistema\n"
        "/pendiente — Tareas pendientes\n"
        "/vault — Ver contenido vault\n"
        "/vault\\_read _cat archivo_ — Leer archivo\n"
        "/agentes — Estado de los agentes\n"
        "/web — Estado WordPress\n"
        "/notificaciones — Reportes pendientes\n\n"
        "*Acciones:*\n"
        "/run _agente_ — Ejecutar agente\n"
        "  (orchestrator, instagram, seo, africa, visual, infoproduct)\n"
        "/ask _pregunta_ — Preguntar a Claude con contexto NosVers\n"
        "/logs _agente_ — Ver últimos logs de un agente\n",
        parse_mode='Markdown'
    )


async def notificaciones(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        return
    notifications = get_pending_notifications()
    if not notifications:
        await update.message.reply_text("No hay notificaciones pendientes.")
        return
    for msg in notifications:
        try:
            await update.message.reply_text(msg, parse_mode='Markdown')
        except Exception:
            await update.message.reply_text(msg)


async def statut(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        return
    await deliver_notifications(update)

    checks = []

    # Check App Granja
    try:
        r = requests.get(f"{APP_URL}?action=vault_list", headers={'X-App-Token': APP_TOKEN}, timeout=10)
        if r.status_code == 200:
            data = r.json()
            checks.append(f"✅ App granja: {data.get('total', 0)} archivos en vault")
        else:
            checks.append(f"❌ App granja: HTTP {r.status_code}")
    except Exception as e:
        checks.append(f"❌ App granja: {str(e)[:50]}")

    # Check WordPress
    try:
        r = requests.get(f"{WP_URL}posts?per_page=1", auth=(WP_USER, WP_PASS), timeout=10)
        if r.status_code == 200:
            checks.append("✅ WordPress: conectado")
        else:
            checks.append(f"❌ WordPress: HTTP {r.status_code}")
    except Exception as e:
        checks.append(f"❌ WordPress: {str(e)[:50]}")

    # Check agents
    if AGENTS_DIR.is_dir():
        agent_files = list(AGENTS_DIR.glob('*.py'))
        checks.append(f"✅ Agentes: {len(agent_files)} scripts")
    else:
        checks.append("❌ Agentes: directorio no encontrado")

    # Check vault
    if VAULT_DIR.is_dir():
        cats = [d for d in VAULT_DIR.iterdir() if d.is_dir()]
        total_files = sum(len(list(d.glob('*.md'))) for d in cats)
        checks.append(f"✅ Vault: {len(cats)} categorías, {total_files} archivos")
    else:
        checks.append("❌ Vault: no encontrada")

    # Check Syncthing
    try:
        r = requests.get('http://localhost:8384/rest/system/status', timeout=5,
                         headers={'X-API-Key': ''})
        if r.status_code in (200, 403):
            checks.append("✅ Syncthing: corriendo")
        else:
            checks.append(f"⚠️ Syncthing: HTTP {r.status_code}")
    except Exception:
        checks.append("❌ Syncthing: no responde")

    # Check Claude API
    if ANTHROPIC_API_KEY:
        checks.append("✅ Claude API: configurada")
    else:
        checks.append("⚠️ Claude API: falta ANTHROPIC_API_KEY")

    msg = f"🌿 *NosVers · Estado del sistema*\n_{datetime.now().strftime('%d/%m/%Y %H:%M')}_\n\n"
    msg += "\n".join(checks)

    await update.message.reply_text(msg, parse_mode='Markdown')


async def pendiente(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        return

    vault_file = VAULT_DIR / 'operaciones' / 'semana-actual.md'
    try:
        content = vault_file.read_text()
        if len(content) > 3500:
            content = content[:3500] + "\n\n_(truncado)_"
        await update.message.reply_text(f"📋 *Semana actual*\n\n{content}", parse_mode='Markdown')
    except FileNotFoundError:
        await update.message.reply_text("❌ semana-actual.md no encontrado")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)[:100]}")


async def vault(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        return

    try:
        msg = "📚 *Vault*\n\n"
        total = 0
        for cat_dir in sorted(VAULT_DIR.iterdir()):
            if cat_dir.is_dir():
                files = list(cat_dir.glob('*.md'))
                if files:
                    msg += f"*{cat_dir.name}/*\n"
                    for f in files:
                        msg += f"  · {f.name}\n"
                        total += 1
                    msg += "\n"
        msg = msg.replace("*Vault*", f"*Vault* — {total} archivos")
        await update.message.reply_text(msg, parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)[:100]}")


async def vault_read(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        return

    if not context.args or len(context.args) < 2:
        await update.message.reply_text("Uso: /vault_read categoria archivo\nEjemplo: /vault_read contexto nosvers-identidad")
        return

    category = context.args[0]
    filename = context.args[1]
    if not filename.endswith('.md'):
        filename += '.md'

    filepath = VAULT_DIR / category / filename
    try:
        content = filepath.read_text()
        if len(content) > 3500:
            content = content[:3500] + "\n\n_(truncado)_"
        await update.message.reply_text(content)
    except FileNotFoundError:
        await update.message.reply_text(f"❌ No encontrado: {category}/{filename}")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)[:100]}")


async def agentes_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        return

    memory_path = Path('/home/nosvers/public_html/agent_memory.json')
    msg = "🤖 *Estado agentes*\n\n"

    # Info de agent_memory.json
    try:
        memory = json.loads(memory_path.read_text())
        for agent, data in memory.items():
            last = data.get('last_vault_write', 'nunca')
            msg += f"*{agent}*: última actividad {last}\n"
        msg += "\n"
    except Exception:
        pass

    # Info de logs
    for name, script in AGENTS_MAP.items():
        log_file = AGENTS_DIR / script.replace('.py', '.log')
        if log_file.exists():
            try:
                lines = log_file.read_text().strip().split('\n')
                last_line = lines[-1] if lines else 'vacío'
                if len(last_line) > 80:
                    last_line = last_line[:80] + '...'
                msg += f"📋 {name}: {last_line}\n"
            except Exception:
                pass

    await update.message.reply_text(msg, parse_mode='Markdown')


async def run_agent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        return

    if not context.args:
        agents_list = ", ".join(AGENTS_MAP.keys())
        await update.message.reply_text(f"Uso: /run agente\nAgentes: {agents_list}")
        return

    agent_name = context.args[0].lower()
    if agent_name not in AGENTS_MAP:
        await update.message.reply_text(f"❌ Agente '{agent_name}' no existe.\nDisponibles: {', '.join(AGENTS_MAP.keys())}")
        return

    script = AGENTS_DIR / AGENTS_MAP[agent_name]
    await update.message.reply_text(f"⏳ Ejecutando {agent_name}...")

    try:
        result = subprocess.run(
            [VENV_PY, str(script)],
            capture_output=True, text=True, timeout=120,
            cwd=str(AGENTS_DIR)
        )
        output = result.stdout[-2000:] if result.stdout else ''
        errors = result.stderr[-500:] if result.stderr else ''

        if result.returncode == 0:
            msg = f"✅ *{agent_name}* ejecutado\n\n"
            if output:
                msg += f"```\n{output}\n```"
            else:
                msg += "Sin output"
        else:
            msg = f"❌ *{agent_name}* falló (código {result.returncode})\n\n"
            if errors:
                msg += f"```\n{errors}\n```"
            elif output:
                msg += f"```\n{output}\n```"

        try:
            await update.message.reply_text(msg, parse_mode='Markdown')
        except Exception:
            await update.message.reply_text(msg[:4000])

    except subprocess.TimeoutExpired:
        await update.message.reply_text(f"⏰ {agent_name} tardó más de 2 minutos — cancelado")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)[:200]}")


async def logs_agent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        return

    if not context.args:
        await update.message.reply_text(f"Uso: /logs agente\nAgentes: {', '.join(AGENTS_MAP.keys())}")
        return

    agent_name = context.args[0].lower()
    if agent_name not in AGENTS_MAP:
        await update.message.reply_text(f"❌ Agente '{agent_name}' no existe.")
        return

    log_name = AGENTS_MAP[agent_name].replace('.py', '.log')
    log_file = AGENTS_DIR / log_name
    if not log_file.exists():
        await update.message.reply_text(f"📋 No hay logs para {agent_name}")
        return

    try:
        content = log_file.read_text()
        # Últimas 3000 chars
        if len(content) > 3000:
            content = "...\n" + content[-3000:]
        await update.message.reply_text(f"📋 *Logs {agent_name}*\n\n```\n{content}\n```", parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)[:100]}")


async def ask_claude(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        return

    if not ANTHROPIC_API_KEY:
        await update.message.reply_text("⚠️ ANTHROPIC_API_KEY no configurada. Pide a Angel que la añada al .env")
        return

    if not context.args:
        await update.message.reply_text("Uso: /ask tu pregunta aquí")
        return

    question = ' '.join(context.args)
    await update.message.reply_text("🤔 Pensando...")

    # Cargar contexto de la vault
    vault_context = ""
    for md_file in ['contexto/nosvers-identidad.md', 'contexto/angel-filosofia.md', 'operaciones/semana-actual.md']:
        filepath = VAULT_DIR / md_file
        if filepath.exists():
            vault_context += f"\n--- {md_file} ---\n{filepath.read_text()}\n"

    try:
        r = requests.post(
            'https://api.anthropic.com/v1/messages',
            headers={
                'x-api-key': ANTHROPIC_API_KEY,
                'anthropic-version': '2023-06-01',
                'content-type': 'application/json',
            },
            json={
                'model': 'claude-sonnet-4-6',
                'max_tokens': 1500,
                'system': f"Eres el asistente de NosVers, una granja de lombricompost en Neuvic, Dordogne. "
                          f"Responde en español, directo, sin rodeos. Contexto:\n{vault_context}",
                'messages': [{'role': 'user', 'content': question}]
            },
            timeout=60
        )

        if r.status_code == 200:
            answer = r.json()['content'][0]['text']
            if len(answer) > 3500:
                answer = answer[:3500] + "\n\n_(truncado)_"
            await update.message.reply_text(answer)
        else:
            await update.message.reply_text(f"❌ Claude API error: {r.status_code} — {r.text[:200]}")

    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)[:200]}")


async def web_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        return

    try:
        r = requests.get(f"{WP_URL}posts?per_page=5&status=draft,publish",
                         auth=(WP_USER, WP_PASS), timeout=10)
        if r.status_code == 200:
            posts = r.json()
            msg = "🌐 *WordPress · Últimos posts*\n\n"
            for p in posts:
                status = "📝" if p['status'] == 'draft' else "✅"
                title = p['title']['rendered']
                msg += f"{status} {title}\n"
            await update.message.reply_text(msg, parse_mode='Markdown')
        else:
            await update.message.reply_text(f"❌ WordPress: HTTP {r.status_code}")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)[:100]}")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Telegram bidireccional: Angel escribe lo que sea → Claude responde con contexto NosVers."""
    if not is_authorized(update.effective_user.id):
        return
    await deliver_notifications(update)

    if not ANTHROPIC_API_KEY:
        await update.message.reply_text("⚠️ ANTHROPIC_API_KEY no configurada en .env")
        return

    chat_id = str(update.message.chat.id)
    if chat_id not in chat_histories:
        chat_histories[chat_id] = []

    # Añadir mensaje de Angel al historial
    chat_histories[chat_id].append({"role": "user", "content": update.message.text})

    # Mantener solo últimos 10 mensajes (5 intercambios)
    chat_histories[chat_id] = chat_histories[chat_id][-10:]

    # Indicador de escritura
    await update.message.reply_chat_action("typing")

    # Cargar contexto vault
    vault_context = ""
    for md_file in ['contexto/nosvers-identidad.md', 'contexto/angel-filosofia.md', 'operaciones/semana-actual.md']:
        filepath = VAULT_DIR / md_file
        if filepath.exists():
            try:
                vault_context += f"\n--- {md_file} ---\n{filepath.read_text()[:2000]}\n"
            except Exception:
                pass

    system_prompt = SYSTEM_NOSVERS
    if vault_context:
        system_prompt += f"\n\nContexto actual:\n{vault_context}"

    try:
        r = requests.post(
            'https://api.anthropic.com/v1/messages',
            headers={
                'x-api-key': ANTHROPIC_API_KEY,
                'anthropic-version': '2023-06-01',
                'content-type': 'application/json',
            },
            json={
                'model': 'claude-sonnet-4-6',
                'max_tokens': 1000,
                'system': system_prompt,
                'messages': chat_histories[chat_id]
            },
            timeout=60
        )

        if r.status_code == 200:
            reply = r.json()['content'][0]['text']

            # Guardar respuesta en historial
            chat_histories[chat_id].append({"role": "assistant", "content": reply})
            chat_histories[chat_id] = chat_histories[chat_id][-10:]

            # Telegram tiene límite de 4096 caracteres
            if len(reply) > 4000:
                reply = reply[:4000] + "\n\n_(truncado — continúa en Claude.ai)_"

            try:
                await update.message.reply_text(reply, parse_mode="Markdown")
            except Exception:
                # Si falla Markdown, enviar sin formato
                await update.message.reply_text(reply)
        else:
            await update.message.reply_text(f"⚠️ Claude API: {r.status_code} — {r.text[:200]}")

    except Exception as e:
        await update.message.reply_text(f"⚠️ Error: {str(e)[:200]}")


def main():
    if not TOKEN:
        logger.error("TELEGRAM_TOKEN no configurado en .env")
        return

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("statut", statut))
    app.add_handler(CommandHandler("pendiente", pendiente))
    app.add_handler(CommandHandler("vault", vault))
    app.add_handler(CommandHandler("vault_read", vault_read))
    app.add_handler(CommandHandler("agentes", agentes_status))
    app.add_handler(CommandHandler("web", web_status))
    app.add_handler(CommandHandler("notificaciones", notificaciones))
    app.add_handler(CommandHandler("run", run_agent))
    app.add_handler(CommandHandler("logs", logs_agent))
    app.add_handler(CommandHandler("ask", ask_claude))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("NosVers HQ Bot arrancado")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
