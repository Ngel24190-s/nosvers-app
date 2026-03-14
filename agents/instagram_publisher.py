#!/usr/bin/env python3
"""
NosVers · Instagram Publisher
Publica fotos directamente en @nosvers.ferme via instagrapi
"""
import os, json, requests
from pathlib import Path
from dotenv import load_dotenv
load_dotenv('/home/nosvers/.env')

try:
    from instagrapi import Client
except ImportError:
    import subprocess
    subprocess.run(['/home/nosvers/venv/bin/pip','install','instagrapi','-q'])
    from instagrapi import Client

IG_USER = os.getenv('INSTAGRAM_USER', 'nosvers.ferme')
IG_PASS = os.getenv('INSTAGRAM_PASS', '')
SESSION_FILE = Path('/home/nosvers/.instagram_session.json')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN', '')
ANGEL_CHAT_ID = os.getenv('ANGEL_CHAT_ID', '5752097691')

def get_client():
    cl = Client()
    if SESSION_FILE.exists():
        cl.load_settings(SESSION_FILE)
    else:
        if not IG_PASS:
            raise ValueError("INSTAGRAM_PASS not set in .env")
        cl.login(IG_USER, IG_PASS)
        cl.dump_settings(SESSION_FILE)
    return cl

def publish_photo(image_path: str, caption: str) -> dict:
    cl = get_client()
    media = cl.photo_upload(path=image_path, caption=caption, extra_data={"disable_comments": 0})
    return {"ok": True, "media_id": str(media.pk), "shortcode": media.code, "url": f"https://www.instagram.com/p/{media.code}/"}

def notify(msg):
    if TELEGRAM_TOKEN:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": ANGEL_CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=10)

if __name__ == '__main__':
    import sys
    data = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    image_path = data.get('image_path', '')
    caption = data.get('caption', '')
    if not image_path or not caption:
        print(json.dumps({"ok": False, "error": "Faltan image_path y caption"}))
        sys.exit(1)
    result = publish_photo(image_path, caption)
    notify(f"✅ Post publicado en Instagram\n{result['url']}")
    print(json.dumps(result))
