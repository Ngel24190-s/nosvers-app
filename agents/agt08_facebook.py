#!/usr/bin/env python3
"""
AGT-08 · Facebook Manager  
Misión: Adaptar contenido Instagram para Facebook + grupos
Cron: 0 11 * * * (diario 11h)
"""
import os, requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
load_dotenv('/home/nosvers/.env')

ANTHROPIC_KEY = os.getenv('ANTHROPIC_API_KEY','')
VAULT_PATH = Path('/home/nosvers/public_html/knowledge_base')

GRUPOS_OBJETIVO = [
    "Jardinage biologique France",
    "Permaculture Dordogne / Périgord", 
    "Compostage et lombricompostage",
    "Maraîchage paysan France"
]

SYSTEM_FB = """Eres AGT-08 Facebook Manager de NosVers.
Adaptas el contenido de Instagram para Facebook (audiencia 40-65 años, jardineros Francia).
Facebook requiere: más texto, más contexto, tono educativo pero accesible.
También generas participaciones orgánicas en grupos de jardinage (como NosVers, experto en suelo vivo).
Idioma: francés siempre."""

def adapt_for_facebook(instagram_post):
    payload = {
        "model": "claude-sonnet-4-6", "max_tokens": 600,
        "system": SYSTEM_FB,
        "messages": [{"role": "user", "content": f"Adapta este post de Instagram para Facebook, haciéndolo más informativo y añadiendo contexto para una audiencia de 40-65 años:\n\n{instagram_post}"}]
    }
    r = requests.post('https://api.anthropic.com/v1/messages',
                      headers={'x-api-key': ANTHROPIC_KEY, 'anthropic-version': '2023-06-01', 'Content-Type': 'application/json'},
                      json=payload, timeout=30)
    return r.json().get('content',[{}])[0].get('text','')

def main():
    print(f"[{datetime.now()}] AGT-08 Facebook iniciando")
    
    # Leer último post de Instagram
    ig_path = VAULT_PATH / 'agentes' / 'agt02-posts-pendientes.md'
    if not ig_path.exists():
        print("Sin posts Instagram para adaptar")
        return
    
    ig_content = ig_path.read_text(encoding='utf-8')
    fb_post = adapt_for_facebook(ig_content[:800])
    
    fecha = datetime.now().strftime('%Y-%m-%d')
    fb_path = VAULT_PATH / 'agentes' / 'agt08_facebook'
    fb_path.mkdir(parents=True, exist_ok=True)
    
    with open(fb_path / '_resultado.md', 'w', encoding='utf-8') as f:
        f.write(f"# Post Facebook — {fecha}\n\n{fb_post}\n\n## Grupos para compartir\n")
        for g in GRUPOS_OBJETIVO:
            f.write(f"- {g}\n")
    
    print(f"[{datetime.now()}] Post Facebook generado")

if __name__ == '__main__':
    main()
