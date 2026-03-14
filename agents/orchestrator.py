#!/usr/bin/env python3
"""
NosVers · Orchestrator
Coordinador central — verifica estado de agentes y notifica a Angel
Cron: 0 * * * * (cada hora)
"""

import os
import json
import subprocess
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv('/home/nosvers/.env')

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
ANGEL_CHAT_ID = os.getenv('ANGEL_CHAT_ID', '5752097691')
APP_URL = os.getenv('APP_URL', 'https://nosvers.com/granja/api.php')
APP_TOKEN = os.getenv('APP_TOKEN', '')
AGENT_NAME = __file__.split('/')[-1].replace('.py', '')
AGENTS_DIR = '/home/nosvers/agents'
LOG_FILE = '/home/nosvers/agents/orchestrator.log'


def log(msg):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{timestamp}] {msg}"
    print(line)
    with open(LOG_FILE, 'a') as f:
        f.write(line + '\n')


# ── VAULT HELPERS ─────────────────────────────────────────
def vault_read(category, filename):
    """Leer un archivo de la vault del agente"""
    try:
        r = requests.get(f"{APP_URL}?action=vault_read&category={category}&filename={filename}",
                         headers={'X-App-Token': APP_TOKEN}, timeout=10)
        if r.status_code == 200:
            return r.json().get('content', '')
    except Exception as e:
        log(f"vault_read error: {e}")
    return ''


def vault_write(category, filename, content, mode='append'):
    """Escribir en la vault del agente"""
    try:
        requests.post(f"{APP_URL}?action=vault_write",
                      headers={'Content-Type': 'application/json', 'X-App-Token': APP_TOKEN},
                      json={'category': category, 'filename': filename, 'content': content, 'mode': mode},
                      timeout=10)
    except Exception as e:
        log(f"vault_write error: {e}")


def save_memoria(entry):
    """Guardar entrada en la memoria del agente"""
    ts = datetime.now().strftime('%Y-%m-%d %H:%M')
    vault_write(f'agentes/{AGENT_NAME}', '_memoria', f'\n## {ts}\n{entry}', mode='append')


def save_resultado(content):
    """Guardar ultimo resultado del agente"""
    vault_write(f'agentes/{AGENT_NAME}', '_resultado', content, mode='overwrite')
# ──────────────────────────────────────────────────────────


def notify(msg):
    if not TELEGRAM_TOKEN:
        log("WARN: No TELEGRAM_TOKEN, skip notify")
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": ANGEL_CHAT_ID, "text": msg, "parse_mode": "Markdown"},
            timeout=10
        )
    except Exception as e:
        log(f"ERROR notify: {e}")


def check_services():
    """Verifica servicios del sistema."""
    results = []

    # Bot Telegram
    ret = subprocess.run(['systemctl', 'is-active', 'nosvers-bot'], capture_output=True, text=True)
    bot_status = ret.stdout.strip()
    results.append(('Bot Telegram', bot_status == 'active', bot_status))

    # Vault
    vault_path = '/home/nosvers/public_html/knowledge_base'
    vault_ok = os.path.isdir(vault_path)
    results.append(('Vault', vault_ok, 'OK' if vault_ok else 'no encontrada'))

    # App granja
    try:
        r = requests.get(f"{APP_URL}?action=vault_list",
                         headers={'X-App-Token': APP_TOKEN}, timeout=10)
        results.append(('App granja', r.status_code == 200, f"HTTP {r.status_code}"))
    except Exception as e:
        results.append(('App granja', False, str(e)[:50]))

    return results


def check_agent_memory():
    """Lee el estado de los agentes desde agent_memory.json."""
    memory_path = '/home/nosvers/public_html/agent_memory.json'
    if not os.path.exists(memory_path):
        return {}
    with open(memory_path) as f:
        return json.load(f)


def run():
    log("=== Orchestrator check ===")

    services = check_services()
    memory = check_agent_memory()

    all_ok = all(ok for _, ok, _ in services)

    # Solo notificar si hay problemas o cada 6 horas (0, 6, 12, 18h)
    hour = datetime.now().hour
    should_notify = not all_ok or hour % 6 == 0

    if should_notify:
        msg = f"🤖 *Orchestrator · {datetime.now().strftime('%d/%m %H:%M')}*\n\n"
        for name, ok, detail in services:
            icon = "✅" if ok else "❌"
            msg += f"{icon} {name}: {detail}\n"

        if memory:
            msg += "\n*Agentes:*\n"
            for agent, data in memory.items():
                last = data.get('last_vault_write', 'nunca')
                msg += f"· {agent}: {last}\n"

        notify(msg)

    for name, ok, detail in services:
        status = "OK" if ok else "FAIL"
        log(f"  {name}: {status} ({detail})")

    log("=== Check completado ===")


if __name__ == '__main__':
    run()
