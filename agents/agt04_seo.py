#!/usr/bin/env python3
"""
AGT-04 · SEO + Blog WordPress
Genera artículo semanal para el blog de nosvers.com
Cron: 0 7 * * 1 (lunes 7h)
"""

import os
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv('/home/nosvers/.env')

APP_URL = os.getenv('APP_URL', 'https://nosvers.com/granja/api.php')
APP_TOKEN = os.getenv('APP_TOKEN', '')
ANTHROPIC_KEY = os.getenv('ANTHROPIC_API_KEY', '')
WP_URL = os.getenv('WP_URL', 'https://nosvers.com/wp-json/wp/v2/')
WP_USER = os.getenv('WP_USER', '')
WP_PASS = os.getenv('WP_PASS', '')
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


def generate_article(identidad, filosofia):
    """Genera artículo SEO optimizado."""
    prompt = f"""Genera un artículo para el blog de nosvers.com optimizado para SEO.

SOBRE NOSVERS:
{identidad}

FILOSOFÍA:
{filosofia}

Requisitos:
- Título SEO (60 chars max)
- Meta description (155 chars max)
- Artículo de 800-1200 palabras
- H2 y H3 bien estructurados
- Keywords naturales integradas
- Idioma: Francés
- Tema: elige entre lombricompost, sol vivant, permaculture, autonomie alimentaire
- Incluye un CTA hacia los productos o el Club Sol Vivant
- Formato: HTML compatible con WordPress (wp:paragraph, wp:heading blocks)

Devuelve el artículo en formato JSON:
{{"title": "...", "meta_description": "...", "content": "<!-- wp:paragraph -->...", "keywords": ["...", "..."]}}
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
            'max_tokens': 4000,
            'system': 'Eres un experto SEO y redactor para blogs de agricultura regenerativa en Francia.',
            'messages': [{'role': 'user', 'content': prompt}]
        },
        timeout=90
    )

    if r.status_code == 200:
        return r.json()['content'][0]['text']
    return None


def publish_draft(title, content):
    """Publica como borrador en WordPress."""
    try:
        r = requests.post(
            f"{WP_URL}posts",
            auth=(WP_USER, WP_PASS),
            json={'title': title, 'content': content, 'status': 'draft'},
            timeout=30
        )
        if r.status_code in (200, 201):
            return r.json().get('link', 'publicado')
        return f"Error WP: HTTP {r.status_code}"
    except Exception as e:
        return f"Error: {e}"


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
    print(f"[{datetime.now()}] AGT-04: Generando artículo SEO...")

    identidad = vault_read('contexto', 'nosvers-identidad')
    filosofia = vault_read('contexto', 'angel-filosofia')

    result = generate_article(identidad, filosofia)
    if not result:
        print("ERROR: No se pudo generar el artículo")
        return

    # Guardar en vault
    vault_write('agentes', 'agt04-seo', result)

    # Intentar parsear JSON y publicar draft
    import json
    try:
        article = json.loads(result)
        wp_result = publish_draft(article['title'], article['content'])
        notify(
            f"📝 *AGT-04 · Artículo SEO*\n\n"
            f"*{article['title']}*\n"
            f"Keywords: {', '.join(article.get('keywords', []))}\n\n"
            f"Publicado como draft: {wp_result}\n"
            f"_Revisa y publica cuando quieras_"
        )
    except (json.JSONDecodeError, KeyError):
        vault_write('agentes', 'agt04-seo', result)
        notify("📝 *AGT-04*: Artículo generado pero no en formato JSON. Revisa vault: agentes/agt04-seo.md")

    print(f"[{datetime.now()}] AGT-04: Completado")


if __name__ == '__main__':
    run()
