#!/usr/bin/env python3
"""
NosVers · Image Service
Servicio unificado de acceso a imágenes desde múltiples fuentes:
1. Google Drive (carpetas NosVers Media + carpetas antiguas)
2. WordPress Media Library (via REST API)
3. Uploads locales del VPS (/home/nosvers/uploads/)
4. Uploads Hostinger (via URL directa)

Los agentes usan este servicio en vez de acceder directamente.
"""
import os
import json
import requests
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv('/home/nosvers/.env')

# ── CONFIG ────────────────────────────────────────────────
WP_URL = os.getenv('WP_URL', 'https://nosvers.com/wp-json/wp/v2/')
WP_USER = os.getenv('WP_USER', 'claude_nosvers')
WP_PASS = os.getenv('WP_PASS', 'fkLzcfDHAE8i6WZQEUCVCvY3')
VPS_UPLOADS = Path('/home/nosvers/uploads')

# Drive folders — nuevas + antiguas
DRIVE_FOLDERS = {
    'root': os.getenv('DRIVE_FOLDER_ID', ''),
    'instagram': os.getenv('DRIVE_FOLDER_INSTAGRAM', ''),
    'vers': os.getenv('DRIVE_FOLDER_VERS', ''),
    'huerto': os.getenv('DRIVE_FOLDER_HUERTO', ''),
    'general': os.getenv('DRIVE_FOLDER_GENERAL', ''),
}

# Carpetas antiguas — Angel las añade aquí o via .env
DRIVE_LEGACY_FOLDERS = {}
for key, val in os.environ.items():
    if key.startswith('DRIVE_LEGACY_'):
        name = key.replace('DRIVE_LEGACY_', '').lower()
        DRIVE_LEGACY_FOLDERS[name] = val

# Merge all Drive folders
ALL_DRIVE_FOLDERS = {**DRIVE_FOLDERS, **DRIVE_LEGACY_FOLDERS}

CACHE_FILE = Path('/home/nosvers/agents/.image_cache.json')


def list_drive_folder(folder_id: str) -> list:
    """List images in a public Google Drive folder (no auth needed if shared)."""
    if not folder_id:
        return []
    try:
        # Use Google Drive API v3 with API key or public access
        api_key = os.getenv('GOOGLE_API_KEY', '')
        if api_key:
            url = f"https://www.googleapis.com/drive/v3/files?q='{folder_id}'+in+parents+and+mimeType+contains+'image'&key={api_key}&fields=files(id,name,mimeType,thumbnailLink,webContentLink,createdTime)&pageSize=100"
        else:
            # Fallback: scrape the public folder page
            url = f"https://drive.google.com/drive/folders/{folder_id}"
        
        r = requests.get(url, timeout=15)
        if r.status_code == 200 and 'files' in r.text:
            data = r.json()
            return [{
                'id': f['id'],
                'name': f['name'],
                'type': f.get('mimeType', 'image/jpeg'),
                'url': f"https://drive.google.com/uc?id={f['id']}&export=download",
                'thumbnail': f.get('thumbnailLink', ''),
                'date': f.get('createdTime', ''),
                'source': 'drive'
            } for f in data.get('files', [])]
    except Exception as e:
        print(f"Drive error for {folder_id}: {e}")
    return []


def list_wp_media(search: str = '', per_page: int = 20) -> list:
    """List images from WordPress media library."""
    try:
        params = {'per_page': per_page, 'media_type': 'image', 'orderby': 'date', 'order': 'desc'}
        if search:
            params['search'] = search
        r = requests.get(f"{WP_URL}media", params=params, auth=(WP_USER, WP_PASS), timeout=15)
        if r.status_code == 200:
            return [{
                'id': m['id'],
                'name': m['title']['rendered'],
                'url': m['source_url'],
                'thumbnail': m.get('media_details', {}).get('sizes', {}).get('medium', {}).get('source_url', m['source_url']),
                'alt': m.get('alt_text', ''),
                'date': m['date'],
                'source': 'wordpress'
            } for m in r.json()]
    except Exception as e:
        print(f"WP Media error: {e}")
    return []


def list_local_uploads(user: str = None) -> list:
    """List images from VPS local uploads."""
    images = []
    search_path = VPS_UPLOADS / user if user else VPS_UPLOADS
    if not search_path.exists():
        return []
    for f in sorted(search_path.rglob('*.{jpg,jpeg,png,webp}'), key=lambda x: x.stat().st_mtime, reverse=True):
        images.append({
            'name': f.name,
            'path': str(f),
            'url': f"https://nosvers.com/granja/uploads/{f.relative_to(VPS_UPLOADS)}",
            'date': datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
            'source': 'local'
        })
    # Also check with glob for case-insensitive
    for ext in ['jpg', 'jpeg', 'png', 'webp', 'JPG', 'JPEG', 'PNG']:
        for f in search_path.glob(f'**/*.{ext}'):
            entry = {
                'name': f.name,
                'path': str(f),
                'url': f"https://nosvers.com/granja/uploads/{f.relative_to(VPS_UPLOADS)}",
                'date': datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
                'source': 'local'
            }
            if entry not in images:
                images.append(entry)
    return images[:50]


def get_all_images(category: str = None, search: str = None, limit: int = 30) -> dict:
    """
    Get images from ALL sources.
    category: 'instagram', 'vers', 'huerto', 'general', or a legacy folder name
    search: text to search in WP media
    """
    result = {
        'drive': [],
        'drive_legacy': [],
        'wordpress': [],
        'local': [],
        'total': 0
    }
    
    # Drive — new folders
    if category and category in DRIVE_FOLDERS:
        result['drive'] = list_drive_folder(DRIVE_FOLDERS[category])
    elif not category:
        for name, fid in DRIVE_FOLDERS.items():
            if name != 'root' and fid:
                result['drive'].extend(list_drive_folder(fid))
    
    # Drive — legacy folders
    if category and category in DRIVE_LEGACY_FOLDERS:
        result['drive_legacy'] = list_drive_folder(DRIVE_LEGACY_FOLDERS[category])
    elif not category:
        for name, fid in DRIVE_LEGACY_FOLDERS.items():
            result['drive_legacy'].extend(list_drive_folder(fid))
    
    # WordPress media
    result['wordpress'] = list_wp_media(search=search or category or '', per_page=limit)
    
    # Local uploads
    result['local'] = list_local_uploads(user=category)
    
    result['total'] = len(result['drive']) + len(result['drive_legacy']) + len(result['wordpress']) + len(result['local'])
    
    return result


def download_image(url: str, dest_path: str) -> str:
    """Download an image from any URL to local path."""
    r = requests.get(url, timeout=30, stream=True)
    r.raise_for_status()
    with open(dest_path, 'wb') as f:
        for chunk in r.iter_content(8192):
            f.write(chunk)
    return dest_path


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Usage: image_service.py [list|search|download] [args]")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == 'list':
        category = sys.argv[2] if len(sys.argv) > 2 else None
        result = get_all_images(category=category)
        print(json.dumps(result, indent=2, default=str))
    
    elif cmd == 'search':
        query = sys.argv[2] if len(sys.argv) > 2 else ''
        result = get_all_images(search=query)
        print(json.dumps(result, indent=2, default=str))
    
    elif cmd == 'download':
        url = sys.argv[2]
        dest = sys.argv[3] if len(sys.argv) > 3 else f'/tmp/nosvers_img_{int(datetime.now().timestamp())}.jpg'
        path = download_image(url, dest)
        print(json.dumps({'ok': True, 'path': path}))
    
    elif cmd == 'folders':
        print("=== Drive NosVers Media ===")
        for name, fid in DRIVE_FOLDERS.items():
            print(f"  {name}: {fid}")
        print("\n=== Drive Legacy (antiguas) ===")
        for name, fid in DRIVE_LEGACY_FOLDERS.items():
            print(f"  {name}: {fid}")
        print(f"\n=== Local uploads: {VPS_UPLOADS} ===")
        if VPS_UPLOADS.exists():
            for d in VPS_UPLOADS.iterdir():
                if d.is_dir():
                    count = len(list(d.glob('*')))
                    print(f"  {d.name}: {count} files")
