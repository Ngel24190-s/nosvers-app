#!/usr/bin/env python3
"""
AGT-11 · Analytics & Reporting
Misión: Métricas semanales + informe para Angel
Cron: 0 18 * * 5 (viernes 18h)
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
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN','')
ANGEL_CHAT_ID = os.getenv('ANGEL_CHAT_ID','5752097691')
VAULT_PATH = Path('/home/nosvers/public_html/knowledge_base')

def get_wp_stats():
    try:
        posts = requests.get(f"{WP_URL}posts?per_page=5&status=publish",
                            auth=(WP_USER, WP_PASS), timeout=10).json()
        return {'posts_publicados': len(posts), 'ultimo_post': posts[0].get('title',{}).get('rendered','') if posts else ''}
    except: return {}

def generate_report(stats):
    payload = {
        "model": "claude-sonnet-4-6", "max_tokens": 600,
        "system": "Eres AGT-11 Analytics de NosVers. Generas informes semanales concisos para Angel (CEO). KPIs objetivo: M3→600€/mes, M6→2000€/mes, Club M1→20 membres.",
        "messages": [{"role": "user", "content": f"Genera el informe semanal con estos datos:\n{stats}\n\nIncluye: resumen de actividad, métricas clave, recomendaciones para la semana siguiente."}]
    }
    r = requests.post('https://api.anthropic.com/v1/messages',
                      headers={'x-api-key': ANTHROPIC_KEY, 'anthropic-version': '2023-06-01', 'Content-Type': 'application/json'},
                      json=payload, timeout=30)
    return r.json().get('content',[{}])[0].get('text','')

def main():
    print(f"[{datetime.now()}] AGT-11 Analytics iniciando")
    
    stats = get_wp_stats()
    report = generate_report(stats)
    
    fecha = datetime.now().strftime('%Y-%m-%d')
    analytics_path = VAULT_PATH / 'analytics'
    analytics_path.mkdir(exist_ok=True)
    
    with open(analytics_path / 'informe-semanal.md', 'w', encoding='utf-8') as f:
        f.write(f"# Informe Semanal — {fecha}\n\n{report}")
    
    # Notificar a Angel
    if TELEGRAM_TOKEN:
        msg = f"📊 *Informe semanal NosVers — {fecha}*\n\n{report[:400]}..."
        try:
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                         json={"chat_id": ANGEL_CHAT_ID, "text": msg, "parse_mode": "Markdown"},
                         timeout=10)
        except: pass
    
    print(f"[{datetime.now()}] Informe semanal generado y enviado")

if __name__ == '__main__':
    main()
