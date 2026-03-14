#!/usr/bin/env python3
"""
AGT-00 · Intelligence Collector
Misión: Scraping de blogs + Google Trends + foros jardinage France
Genera ideas diarias de contenido para el Content Director
Cron: 0 6 * * *
"""
import os, json, requests, feedparser
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
load_dotenv('/home/nosvers/.env')

ANTHROPIC_KEY = os.getenv('ANTHROPIC_API_KEY','')
VAULT_PATH = Path('/home/nosvers/public_html/knowledge_base')

# Fuentes RSS de jardinage France
RSS_FEEDS = [
    'https://www.rustica.fr/feed',
    'https://www.jardiner-malin.fr/feed',
    'https://permaculturedesign.fr/feed',
    'https://www.bioalaune.com/feed',
]

KEYWORDS = ['lombricompost','sol vivant','permaculture','jardinage bio','compostage','engrais vert']

def fetch_rss_ideas():
    ideas = []
    for url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:3]:
                title = entry.get('title','')
                if any(kw in title.lower() for kw in KEYWORDS):
                    ideas.append({'source': feed.feed.get('title',''), 'title': title, 'url': entry.get('link','')})
        except: pass
    return ideas

def generate_content_ideas(raw_ideas):
    if not ANTHROPIC_KEY or not raw_ideas:
        return "Sin ideas esta semana — verificar fuentes RSS"
    
    ideas_text = '\n'.join([f"- {i['title']} ({i['source']})" for i in raw_ideas[:10]])
    
    payload = {
        "model": "claude-sonnet-4-6",
        "max_tokens": 800,
        "system": "Eres el Intelligence Collector de NosVers, ferme lombricole en Dordogne. Generas ideas de contenido accionables basadas en tendencias de jardinage en Francia.",
        "messages": [{"role": "user", "content": f"Basándote en estas noticias de jardinage France, genera 5 ideas de contenido específicas para NosVers (lombricompost, suelo vivo, jardinage bio):\n\n{ideas_text}\n\nFormato: idea concreta + canal sugerido (Instagram/Blog/YouTube/Facebook)"}]
    }
    
    r = requests.post('https://api.anthropic.com/v1/messages',
                      headers={'x-api-key': ANTHROPIC_KEY, 'anthropic-version': '2023-06-01', 'Content-Type': 'application/json'},
                      json=payload, timeout=30)
    return r.json().get('content',[{}])[0].get('text','Error generando ideas')

def main():
    print(f"[{datetime.now()}] AGT-00 Intelligence iniciando")
    
    ideas_raw = fetch_rss_ideas()
    ideas_content = generate_content_ideas(ideas_raw)
    
    fecha = datetime.now().strftime('%Y-%m-%d')
    content = f"## {fecha} — Ideas semanales\n\n{ideas_content}\n\n### Fuentes detectadas\n"
    for i in ideas_raw[:5]:
        content += f"- [{i['title']}]({i['url']})\n"
    
    # Guardar en vault
    intel_path = VAULT_PATH / 'intelligence'
    intel_path.mkdir(exist_ok=True)
    ideas_file = intel_path / 'ideas-semaine.md'
    
    with open(ideas_file, 'a', encoding='utf-8') as f:
        f.write(f"\n\n---\n{content}")
    
    print(f"[{datetime.now()}] Ideas guardadas en vault/intelligence/ideas-semaine.md")

if __name__ == '__main__':
    main()
