#!/usr/bin/env python3
"""
NosVers · Drive to WordPress Sync
Descarga fotos nuevas de Google Drive (carpetas públicas) y las sube a WordPress Media Library.
Cron: 0 */2 * * * (cada 2 horas)
"""
import os, requests, json, hashlib
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
load_dotenv('/home/nosvers/.env')

WP_URL  = os.getenv('WP_URL', 'https://nosvers.com/wp-json/wp/v2/')
WP_USER = os.getenv('WP_USER', 'claude_nosvers')
WP_PASS = os.getenv('WP_PASS', '')

DRIVE_FOLDERS = {
    'instagram': os.getenv('DRIVE_FOLDER_INSTAGRAM', ''),
    'vers-compost': os.getenv('DRIVE_FOLDER_VERS', ''),
    'huerto': os.getenv('DRIVE_FOLDER_HUERTO', ''),
    'general': os.getenv('DRIVE_FOLDER_GENERAL', ''),
}

UPLOADS_DIR = Path('/home/nosvers/uploads')
SYNCED_LOG  = Path('/home/nosvers/logs/drive_synced.txt')
VAULT_PATH  = Path('/home/nosvers/public_html/knowledge_base')

def list_drive_files(folder_id):
    """Lista archivos de una carpeta pública de Drive via API sin auth."""
    if not folder_id:
        return []
    # Usar la API pública de Drive (carpeta compartida con link)
    url = f"https://www.googleapis.com/drive/v3/files"
    params = {
        'q': f"'{folder_id}' in parents and mimeType contains 'image/'",
        'fields': 'files(id,name,mimeType,createdTime,size)',
        'orderBy': 'createdTime desc',
        'pageSize': 20,
        'key': '',  # No API key needed for public folders
    }
    try:
        r = requests.get(url, params=params, timeout=15)
        if r.status_code == 200:
            return r.json().get('files', [])
        else:
            print(f"  Drive API error {r.status_code} for folder {folder_id}")
            return []
    except Exception as e:
        print(f"  Drive error: {e}")
        return []

def download_drive_file(file_id, filename, category):
    """Descarga un archivo de Drive público."""
    dest_dir = UPLOADS_DIR / category
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / filename
    
    if dest.exists():
        return dest
    
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    try:
        r = requests.get(url, timeout=30, stream=True)
        if r.status_code == 200:
            with open(dest, 'wb') as f:
                for chunk in r.iter_content(8192):
                    f.write(chunk)
            print(f"  ✅ Descargado: {filename} → {category}/")
            return dest
        else:
            print(f"  ❌ Error descargando {filename}: HTTP {r.status_code}")
            return None
    except Exception as e:
        print(f"  ❌ Error descargando {filename}: {e}")
        return None

def upload_to_wordpress(filepath):
    """Sube imagen a WordPress Media Library."""
    if not WP_USER or not WP_PASS:
        print(f"  ⚠️ WP credentials not set, skipping upload")
        return None
    
    filename = filepath.name
    mime = 'image/jpeg' if filename.lower().endswith(('.jpg','.jpeg')) else 'image/png'
    
    try:
        with open(filepath, 'rb') as f:
            r = requests.post(
                f"{WP_URL}media",
                auth=(WP_USER, WP_PASS),
                headers={'Content-Disposition': f'attachment; filename="{filename}"',
                         'Content-Type': mime},
                data=f.read(),
                timeout=30
            )
        if r.status_code in (200, 201):
            data = r.json()
            wp_url = data.get('source_url', '')
            wp_id = data.get('id', '')
            print(f"  ✅ WordPress: {filename} → ID {wp_id}")
            return {'id': wp_id, 'url': wp_url, 'filename': filename}
        else:
            print(f"  ❌ WP upload failed: {r.status_code} — {r.text[:100]}")
            return None
    except Exception as e:
        print(f"  ❌ WP upload error: {e}")
        return None

def get_synced():
    """Leer archivos ya sincronizados."""
    if SYNCED_LOG.exists():
        return set(SYNCED_LOG.read_text().strip().splitlines())
    return set()

def mark_synced(file_id):
    """Marcar archivo como sincronizado."""
    SYNCED_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(SYNCED_LOG, 'a') as f:
        f.write(file_id + '\n')

def log_to_vault(category, filename, wp_url=''):
    """Registrar en el log de fotos."""
    log_path = VAULT_PATH / 'operaciones' / 'fotos-log.md'
    log_path.parent.mkdir(parents=True, exist_ok=True)
    entry = f"\n{datetime.now().strftime('%Y-%m-%d %H:%M')} | drive | {category} | auto-sync | {filename}"
    if wp_url:
        entry += f" | wp:{wp_url}"
    with open(log_path, 'a') as f:
        f.write(entry)

def main():
    print(f"[{datetime.now()}] Drive→WordPress sync iniciando")
    
    synced = get_synced()
    total_new = 0
    
    for category, folder_id in DRIVE_FOLDERS.items():
        if not folder_id:
            continue
        
        print(f"\n📁 {category} (folder: {folder_id[:8]}...)")
        files = list_drive_files(folder_id)
        
        if not files:
            print(f"  Sin archivos nuevos")
            continue
        
        for file_info in files:
            fid = file_info['id']
            fname = file_info['name']
            
            if fid in synced:
                continue
            
            # Descargar
            local_path = download_drive_file(fid, fname, category)
            if not local_path:
                continue
            
            # Subir a WordPress
            wp_result = upload_to_wordpress(local_path)
            wp_url = wp_result['url'] if wp_result else ''
            
            # Registrar
            log_to_vault(category, fname, wp_url)
            mark_synced(fid)
            total_new += 1
    
    print(f"\n{'='*40}")
    print(f"Sync completado: {total_new} archivos nuevos procesados")

if __name__ == '__main__':
    main()
