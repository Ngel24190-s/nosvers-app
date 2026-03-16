#!/usr/bin/env python3
"""
AGT-10 · Community Manager
Misión: Monitorizar y responder comentarios en todos los canales
Cron: 0 */4 * * * (cada 4 horas)
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

SYSTEM_COMMUNITY = """Eres AGT-10 Community Manager de NosVers con la VOZ DE ÁFRICA.
Respondes comentarios en francés, tono cálido, experto pero cercano.
Para preguntas sobre lombricompost, suelo vivo, jardinage → responde con el conocimiento de África.
Para consultas de compra → dirige al producto correcto de NosVers.
Para preguntas muy técnicas o personales → "Je vais en parler avec África et je reviens vers vous".
NUNCA menciones que eres una IA. Eres el equipo NosVers."""

def check_wp_comments():
    try:
        r = requests.get(f"{WP_URL}comments?status=hold&per_page=5",
                        auth=(WP_USER, WP_PASS), timeout=10)
        return r.json() if r.status_code == 200 else []
    except: return []

def generate_reply(comment_text, context=""):
    payload = {
        "model": "claude-sonnet-4-6", "max_tokens": 300,
        "system": SYSTEM_COMMUNITY,
        "messages": [{"role": "user", "content": f"Responde este comentario del blog NosVers:\n\n{comment_text}\n\nContexto NosVers:\n{context}"}]
    }
    r = requests.post('https://api.anthropic.com/v1/messages',
                      headers={'x-api-key': ANTHROPIC_KEY, 'anthropic-version': '2023-06-01', 'Content-Type': 'application/json'},
                      json=payload, timeout=20)
    return r.json().get('content',[{}])[0].get('text','')

def main():
    print(f"[{datetime.now()}] AGT-10 Community iniciando")
    
    # Leer conocimiento de África para contexto
    africa_path = VAULT_PATH / 'contexto' / 'africa-conocimiento.md'
    context = africa_path.read_text(encoding='utf-8')[:600] if africa_path.exists() else ""
    
    # Revisar comentarios WordPress pendientes
    comments = check_wp_comments()
    
    log_path = VAULT_PATH / 'agentes' / 'agt10_community'
    log_path.mkdir(parents=True, exist_ok=True)
    
    with open(log_path / '_memoria.md', 'a', encoding='utf-8') as f:
        f.write(f"\n## {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"Comentarios pendientes WP: {len(comments)}\n")
        if comments:
            for c in comments[:3]:
                text = c.get('content',{}).get('rendered','')[:200]
                f.write(f"- {text[:100]}...\n")
    
    print(f"[{datetime.now()}] Community check completado. Pendientes: {len(comments)}")

if __name__ == '__main__':
    main()
