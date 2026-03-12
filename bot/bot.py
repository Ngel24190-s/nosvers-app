#!/usr/bin/env python3
"""
NosVers HQ Bot — @nosvers_hq_bot
Bot Telegram para comunicación con Angel (CEO)
Comandos: /statut, /pendiente, /vault, /agentes
"""

import os
import json
import logging
import requests
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Config
load_dotenv('/home/nosvers/.env')
TOKEN = os.getenv('TELEGRAM_TOKEN')
ANGEL_ID = int(os.getenv('ANGEL_CHAT_ID', '5752097691'))
APP_URL = os.getenv('APP_URL', 'https://nosvers.com/granja/api.php')
APP_TOKEN = os.getenv('APP_TOKEN', '')
WP_URL = os.getenv('WP_URL', 'https://nosvers.com/wp-json/wp/v2/')
WP_USER = os.getenv('WP_USER', '')
WP_PASS = os.getenv('WP_PASS', '')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('nosvers_bot')

AUTHORIZED_USERS = {ANGEL_ID}


def is_authorized(user_id: int) -> bool:
    return user_id in AUTHORIZED_USERS


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        return
    await update.message.reply_text(
        "🌿 *NosVers HQ Bot*\n\n"
        "Comandos disponibles:\n"
        "/statut — Estado del sistema\n"
        "/pendiente — Tareas pendientes\n"
        "/vault — Ver contenido vault\n"
        "/agentes — Estado de los agentes\n"
        "/web — Estado WordPress\n",
        parse_mode='Markdown'
    )


async def statut(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        return

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
    agents_dir = '/home/nosvers/agents/'
    if os.path.isdir(agents_dir):
        agent_files = [f for f in os.listdir(agents_dir) if f.endswith('.py')]
        checks.append(f"✅ Agentes: {len(agent_files)} scripts en /agents/")
    else:
        checks.append("❌ Agentes: directorio no encontrado")

    # Check vault
    vault_dir = '/home/nosvers/public_html/knowledge_base/'
    if os.path.isdir(vault_dir):
        cats = [d for d in os.listdir(vault_dir) if os.path.isdir(os.path.join(vault_dir, d))]
        checks.append(f"✅ Vault: {len(cats)} categorías")
    else:
        checks.append("❌ Vault: no encontrada")

    msg = f"🌿 *NosVers · Estado del sistema*\n_{datetime.now().strftime('%d/%m/%Y %H:%M')}_\n\n"
    msg += "\n".join(checks)

    await update.message.reply_text(msg, parse_mode='Markdown')


async def pendiente(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        return

    try:
        r = requests.get(
            f"{APP_URL}?action=vault_read&category=operaciones&filename=semana-actual",
            headers={'X-App-Token': APP_TOKEN}, timeout=10
        )
        if r.status_code == 200:
            content = r.json().get('content', 'Sin contenido')
            # Truncar si es muy largo para Telegram
            if len(content) > 3500:
                content = content[:3500] + "\n\n_(truncado)_"
            await update.message.reply_text(f"📋 *Semana actual*\n\n{content}", parse_mode='Markdown')
        else:
            await update.message.reply_text("❌ No pude leer semana-actual de la vault")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)[:100]}")


async def vault(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        return

    try:
        r = requests.get(f"{APP_URL}?action=vault_list", headers={'X-App-Token': APP_TOKEN}, timeout=10)
        if r.status_code == 200:
            data = r.json()
            files = data.get('files', [])
            msg = f"📚 *Vault* — {data.get('total', 0)} archivos\n\n"
            by_cat = {}
            for f in files:
                cat = f['category']
                if cat not in by_cat:
                    by_cat[cat] = []
                by_cat[cat].append(f['file'])
            for cat, flist in sorted(by_cat.items()):
                msg += f"*{cat}/*\n"
                for fname in flist:
                    msg += f"  · {fname}\n"
                msg += "\n"
            await update.message.reply_text(msg, parse_mode='Markdown')
        else:
            await update.message.reply_text("❌ No pude listar la vault")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)[:100]}")


async def agentes_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        return

    memory_path = '/home/nosvers/public_html/agent_memory.json'
    try:
        with open(memory_path) as f:
            memory = json.load(f)
        msg = "🤖 *Estado agentes*\n\n"
        for agent, data in memory.items():
            last = data.get('last_vault_write', 'nunca')
            msg += f"*{agent}*: última actividad {last}\n"
        await update.message.reply_text(msg, parse_mode='Markdown')
    except FileNotFoundError:
        await update.message.reply_text("❌ agent_memory.json no encontrado")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)[:100]}")


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
    """Responde a mensajes de texto de Angel."""
    if not is_authorized(update.effective_user.id):
        return
    await update.message.reply_text(
        "Recibido. Usa /statut, /pendiente, /vault, /agentes o /web para interactuar."
    )


def main():
    if not TOKEN:
        logger.error("TELEGRAM_TOKEN no configurado en .env")
        return

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("statut", statut))
    app.add_handler(CommandHandler("pendiente", pendiente))
    app.add_handler(CommandHandler("vault", vault))
    app.add_handler(CommandHandler("agentes", agentes_status))
    app.add_handler(CommandHandler("web", web_status))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("NosVers HQ Bot arrancado")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
