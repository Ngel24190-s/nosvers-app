#!/usr/bin/env python3
"""
AGT-05 · Procesador de conocimiento de África
Procesa contenido de África → estructura en vault → genera PDFs Club
Cron: 0 */6 * * * (cada 6 horas)
"""

import os
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv('/home/nosvers/.env')

# ── VAULT HELPER — leer/escribir contexto del agente ─────
import os, requests as _req
from datetime import datetime

APP_URL  = os.getenv('APP_URL', 'https://nosvers.com/granja/api.php')
APP_TOKEN = os.getenv('APP_TOKEN', '')
AGENT_NAME = __file__.split('/')[-1].replace('.py','')

def vault_read(category, filename):
    """Leer un archivo de la vault del agente"""
    try:
        r = _req.get(f"{APP_URL}?action=vault_read&category={category}&filename={filename}",
                    headers={'X-App-Token': APP_TOKEN}, timeout=10)
        if r.status_code == 200:
            return r.json().get('content', '')
    except Exception as e:
        log(f"vault_read error: {e}")
    return ''

def vault_write(category, filename, content, mode='append'):
    """Escribir en la vault del agente"""
    try:
        _req.post(f"{APP_URL}?action=vault_write",
                 headers={'Content-Type':'application/json','X-App-Token': APP_TOKEN},
                 json={'category': category, 'filename': filename, 'content': content, 'mode': mode},
                 timeout=10)
    except Exception as e:
        log(f"vault_write error: {e}")

def get_contexto():
    """Leer el contexto predeterminado de este agente"""
    return vault_read(f'agentes/{AGENT_NAME}', '_contexto')

def save_memoria(entry):
    """Guardar entrada en la memoria del agente"""
    ts = datetime.now().strftime('%Y-%m-%d %H:%M')
    vault_write(f'agentes/{AGENT_NAME}', '_memoria', f'\n## {ts}\n{entry}', mode='append')

def save_resultado(content):
    """Guardar último resultado del agente"""
    vault_write(f'agentes/{AGENT_NAME}', '_resultado', content, mode='overwrite')
# ─────────────────────────────────────────────────────────


APP_URL = os.getenv('APP_URL', 'https://nosvers.com/granja/api.php')
APP_TOKEN = os.getenv('APP_TOKEN', '')
ANTHROPIC_KEY = os.getenv('ANTHROPIC_API_KEY', '')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
ANGEL_CHAT_ID = os.getenv('ANGEL_CHAT_ID', '5752097691')

# Directorio donde África deja contenido (email procesado, notas, etc.)
AFRICA_INPUT = '/home/nosvers/uploads/africa/'


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


def vault_write(category, filename, content, mode='append'):
    try:
        requests.post(
            f"{APP_URL}?action=vault_write",
            headers={'X-App-Token': APP_TOKEN, 'Content-Type': 'application/json'},
            json={'category': category, 'filename': filename, 'content': content, 'mode': mode},
            timeout=10
        )
    except Exception:
        pass


def process_with_claude(raw_content):
    """Estructura contenido bruto de África en formato vault."""
    prompt = f"""Tienes contenido bruto de África (Directora de Conocimiento de NosVers, experta en lombricompost y sol vivant).

Contenido bruto:
{raw_content}

Estructura este contenido en formato Markdown limpio para la vault de conocimiento:
1. Título claro
2. Categorías/tags
3. Contenido organizado con H2/H3
4. Datos técnicos destacados
5. Citas textuales de África entre comillas
6. Fecha de procesamiento

Si hay suficiente contenido técnico, indica "READY_FOR_PDF" al final.
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
            'system': 'Eres un editor técnico especializado en agricultura regenerativa y lombricompost.',
            'messages': [{'role': 'user', 'content': prompt}]
        },
        timeout=60
    )

    if r.status_code == 200:
        return r.json()['content'][0]['text']
    return None


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
    print(f"[{datetime.now()}] AGT-05: Buscando contenido de África...")

    # Buscar archivos nuevos en directorio de input
    if not os.path.isdir(AFRICA_INPUT):
        os.makedirs(AFRICA_INPUT, exist_ok=True)
        print("  Directorio de input creado, esperando contenido")
        return

    processed_log = os.path.join(AFRICA_INPUT, '.processed')
    processed = set()
    if os.path.exists(processed_log):
        with open(processed_log) as f:
            processed = set(f.read().strip().split('\n'))

    new_files = [f for f in os.listdir(AFRICA_INPUT)
                 if f not in processed and not f.startswith('.') and os.path.isfile(os.path.join(AFRICA_INPUT, f))]

    if not new_files:
        print("  Sin contenido nuevo de África")
        return

    for filename in new_files:
        filepath = os.path.join(AFRICA_INPUT, filename)
        print(f"  Procesando: {filename}")

        with open(filepath) as f:
            raw = f.read()

        structured = process_with_claude(raw)
        if structured:
            # Guardar en vault
            safe_name = filename.rsplit('.', 1)[0].lower().replace(' ', '-')
            vault_write('contexto', f'africa-{safe_name}', structured, mode='overwrite')

            # Append a conocimiento acumulado
            vault_write('contexto', 'africa-conocimiento', f"\n\n## {filename}\n{structured}", mode='append')

            # Marcar como procesado
            with open(processed_log, 'a') as f:
                f.write(filename + '\n')

            # Notificar si hay material para PDF
            if 'READY_FOR_PDF' in structured:
                notify(
                    f"📚 *AGT-05 · Contenido África procesado*\n\n"
                    f"Archivo: {filename}\n"
                    f"*Material suficiente para PDF del Club*\n"
                    f"_¿Genero el PDF? Confirma con /generar\\_pdf_"
                )
            else:
                notify(
                    f"📚 *AGT-05*: Procesado _{filename}_ de África → vault actualizada"
                )

    print(f"[{datetime.now()}] AGT-05: {len(new_files)} archivos procesados")


if __name__ == '__main__':
    run()
