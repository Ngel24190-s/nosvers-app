#!/usr/bin/env python3
"""
AGT-02 · Generador de posts Instagram
Genera 5 posts/semana con copy + hashtags basados en la identidad NosVers
Cron: 0 10 * * 0 (domingos 10h)
"""

import os
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv('/home/nosvers/.env')

APP_URL = os.getenv('APP_URL', 'https://nosvers.com/granja/api.php')
APP_TOKEN = os.getenv('APP_TOKEN', '')
ANTHROPIC_KEY = os.getenv('ANTHROPIC_API_KEY', '')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
ANGEL_CHAT_ID = os.getenv('ANGEL_CHAT_ID', '5752097691')


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


def vault_write(category, filename, content, mode='overwrite'):
    try:
        requests.post(
            f"{APP_URL}?action=vault_write",
            headers={'X-App-Token': APP_TOKEN, 'Content-Type': 'application/json'},
            json={'category': category, 'filename': filename, 'content': content, 'mode': mode},
            timeout=10
        )
    except Exception:
        pass


def generate_posts(identidad, filosofia, semana):
    """Usa Claude para generar 5 posts Instagram."""
    prompt = f"""Genera 5 posts para Instagram de @nosvers.ferme para esta semana.

IDENTIDAD DE MARCA:
{identidad}

FILOSOFÍA:
{filosofia}

CONTEXTO SEMANA:
{semana}

Para cada post genera:
1. Copy principal (máx 150 palabras, tono directo, sin positivismo vacío)
2. Call to action
3. 15-20 hashtags relevantes (mezcla FR/ES)
4. Sugerencia visual (qué foto/video usar)

Formato: POST 1, POST 2... etc.
Idioma principal: Francés con toques de español para autenticidad.
"""

    r = requests.post(
        'https://api.anthropic.com/v1/messages',
        headers={
            'Content-Type': 'application/json',
            'x-api-key': ANTHROPIC_KEY,
            'anthropic-version': '2023-06-01'
        },
        json={
            'model': 'claude-sonnet-4-6',
            'max_tokens': 3000,
            'system': 'Eres el community manager de NosVers, una ferme en Dordogne. Generas contenido auténtico, directo, sin florituras.',
            'messages': [{'role': 'user', 'content': prompt}]
        },
        timeout=60
    )

    if r.status_code == 200:
        return r.json()['content'][0]['text']
    return f"Error generando posts: HTTP {r.status_code}"


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
    print(f"[{datetime.now()}] AGT-02: Generando posts Instagram...")

    identidad = vault_read('contexto', 'nosvers-identidad')
    filosofia = vault_read('contexto', 'angel-filosofia')
    semana = vault_read('operaciones', 'semana-actual')

    if not identidad:
        print("ERROR: No se pudo leer nosvers-identidad de la vault")
        return

    posts = generate_posts(identidad, filosofia, semana)

    # Guardar en vault
    vault_write('agentes', 'agt02-posts-pendientes', posts)

    # Notificar a Angel para aprobación
    preview = posts[:500] + "..." if len(posts) > 500 else posts
    notify(
        f"📸 *AGT-02 · Posts Instagram generados*\n\n"
        f"{preview}\n\n"
        f"_5 posts listos para revisión en vault: agentes/agt02-posts-pendientes.md_"
    )

    print(f"[{datetime.now()}] AGT-02: Posts generados y guardados")


if __name__ == '__main__':
    run()
