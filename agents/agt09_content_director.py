#!/usr/bin/env python3
"""
AGT-09 · Content Director
Misión: Brief semanal para todos los canales — un tema, cuatro formatos
Cron: 0 9 * * 0 (domingos 9h, antes que AGT-02)
"""
import os, requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
load_dotenv('/home/nosvers/.env')

ANTHROPIC_KEY = os.getenv('ANTHROPIC_API_KEY','')
VAULT_PATH = Path('/home/nosvers/public_html/knowledge_base')

SYSTEM_CD = """Eres AGT-09 Content Director de NosVers, ferme lombricole en Dordogne.
Generas el brief semanal de contenido para todos los canales.
Principio fundamental: UN TEMA → CUATRO FORMATOS (Instagram + Blog/SEO + YouTube + Facebook).
Lees las ideas de Intelligence (vault/intelligence/) y el conocimiento de África (vault/contexto/africa-conocimiento.md).
El tema debe ser estacional, relevante, y basado en el conocimiento real de África.
Output: brief completo con instrucciones específicas para cada agente."""

def generate_brief():
    # Leer intelligence y conocimiento de África
    intel_path = VAULT_PATH / 'intelligence' / 'ideas-semaine.md'
    africa_path = VAULT_PATH / 'contexto' / 'africa-conocimiento.md'
    
    intel = intel_path.read_text(encoding='utf-8')[-800:] if intel_path.exists() else ""
    africa = africa_path.read_text(encoding='utf-8')[-800:] if africa_path.exists() else ""
    
    semana = datetime.now().strftime('%Y semaine %W')
    
    payload = {
        "model": "claude-sonnet-4-6", "max_tokens": 1500,
        "system": SYSTEM_CD,
        "messages": [{"role": "user", "content": f"Genera el brief semanal para {semana}.\n\nInteligence esta semana:\n{intel}\n\nConocimiento de África:\n{africa}\n\nIncluye: tema principal, instrucciones para Instagram (5 posts), Blog (1 artículo), YouTube (1 guión), Facebook (1 post + 2 participaciones en grupos)."}]
    }
    
    r = requests.post('https://api.anthropic.com/v1/messages',
                      headers={'x-api-key': ANTHROPIC_KEY, 'anthropic-version': '2023-06-01', 'Content-Type': 'application/json'},
                      json=payload, timeout=45)
    return r.json().get('content',[{}])[0].get('text','')

def main():
    print(f"[{datetime.now()}] AGT-09 Content Director iniciando")
    
    brief = generate_brief()
    fecha = datetime.now().strftime('%Y-%m-%d')
    
    brief_path = VAULT_PATH / 'operaciones' / 'brief-semanal.md'
    brief_path.write_text(f"# Brief Semanal — {fecha}\n\n{brief}", encoding='utf-8')
    
    print(f"[{datetime.now()}] Brief semanal guardado")

if __name__ == '__main__':
    main()
