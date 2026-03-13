#!/usr/bin/env python3
"""
AGT-06 · Infoproductos — PDFs + Lemon Squeezy
Estado: FASE 1 — activar en M1
Genera PDFs maquetados del conocimiento de África para el Club Sol Vivant
"""

import os
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv('/home/nosvers/.env')

APP_URL = os.getenv('APP_URL', 'https://nosvers.com/granja/api.php')
APP_TOKEN = os.getenv('APP_TOKEN', '')
ANTHROPIC_KEY = os.getenv('ANTHROPIC_API_KEY', '')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
ANGEL_CHAT_ID = os.getenv('ANGEL_CHAT_ID', '5752097691')

PDF_OUTPUT = '/home/nosvers/uploads/pdfs/'


def vault_read(category, filename):
    try:
        r = requests.get(
            f"{APP_URL}?action=vault_read&category={category}&filename={filename}",
            headers={'X-App-Token': APP_TOKEN}, timeout=10
        )
        if r.status_code == 200:
            return r.json().get('content', '')
    except Exception:
        pass
    return ''


def notify(msg):
    if not TELEGRAM_TOKEN:
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": ANGEL_CHAT_ID, "text": msg, "parse_mode": "Markdown"},
            timeout=10
        )
    except Exception:
        pass


def run():
    """
    FASE 1: Placeholder — se activará cuando haya suficiente contenido de África.
    Flujo futuro:
    1. Leer conocimiento acumulado de vault (contexto/africa-conocimiento)
    2. Generar PDF con reportlab/weasyprint
    3. Subir a Lemon Squeezy via API
    4. Notificar a Angel
    """
    print(f"[{datetime.now()}] AGT-06: FASE 1 — En espera")

    # Verificar si hay contenido suficiente
    conocimiento = vault_read('contexto', 'africa-conocimiento')
    if len(conocimiento) > 3000:
        notify(
            "📄 *AGT-06*: Hay contenido suficiente de África para generar PDF #1 del Club.\n"
            "_Esperando activación — confirma con Angel_"
        )
    else:
        print("  Contenido insuficiente para PDF. Esperando más material de África.")


if __name__ == '__main__':
    run()
