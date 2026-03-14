#!/usr/bin/env python3
"""
AGT-07 · YouTube Manager
Misión: Guiones sin voz + SEO + publicación
Cron: 0 10 * * 2 (martes 10h)
"""
import os, requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
load_dotenv('/home/nosvers/.env')

ANTHROPIC_KEY = os.getenv('ANTHROPIC_API_KEY','')
WP_URL = os.getenv('WP_URL','https://nosvers.com/wp-json/wp/v2/')
WP_USER = os.getenv('WP_USER','claude_nosvers')
WP_PASS = os.getenv('WP_PASS','')
VAULT_PATH = Path('/home/nosvers/public_html/knowledge_base')

SYSTEM_YT = """Eres AGT-07 YouTube Manager de NosVers, ferme lombricole en Dordogne.
Generas guiones para vídeos SIN VOZ de África (texto superposado + imágenes).
Formatos: timelapse lombricompost, proceso LombriThé, antes/después bancales, un día en la ferme.
Duración objetivo: 60-90 segundos.
Siempre incluir: título SEO, descripción optimizada (500 palabras), 15 tags, thumbnail sugerido."""

def generate_script(tema):
    payload = {
        "model": "claude-sonnet-4-6", "max_tokens": 1200,
        "system": SYSTEM_YT,
        "messages": [{"role": "user", "content": f"Genera un guión completo para: {tema}"}]
    }
    r = requests.post('https://api.anthropic.com/v1/messages',
                      headers={'x-api-key': ANTHROPIC_KEY, 'anthropic-version': '2023-06-01', 'Content-Type': 'application/json'},
                      json=payload, timeout=30)
    return r.json().get('content',[{}])[0].get('text','')

def main():
    print(f"[{datetime.now()}] AGT-07 YouTube iniciando")
    
    # Leer brief semanal
    brief_path = VAULT_PATH / 'operaciones' / 'brief-semanal.md'
    tema = "Le processus du lombricompostage de A à Z"
    if brief_path.exists():
        brief = brief_path.read_text(encoding='utf-8')
        if 'YouTube' in brief:
            lines = [l for l in brief.split('\n') if 'YouTube' in l or 'video' in l.lower()]
            if lines: tema = lines[0].replace('YouTube:', '').strip()
    
    script = generate_script(tema)
    
    # Guardar en vault
    fecha = datetime.now().strftime('%Y-%m-%d')
    yt_path = VAULT_PATH / 'agentes' / 'agt07_youtube'
    yt_path.mkdir(parents=True, exist_ok=True)
    
    with open(yt_path / '_resultado.md', 'w', encoding='utf-8') as f:
        f.write(f"# Guión YouTube — {fecha}\n\n{script}")
    
    print(f"[{datetime.now()}] Guión guardado")

if __name__ == '__main__':
    main()
