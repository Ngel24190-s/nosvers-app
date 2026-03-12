#!/usr/bin/env python3
"""
AGT-01 · Preparador de visuels Instagram
Procesa fotos brutas de África → visuels listos para publicar
Estado: ACTIVO — esperando fotos de África
"""

import os
import shutil
from datetime import datetime
from dotenv import load_dotenv

load_dotenv('/home/nosvers/.env')

UPLOADS_DIR = '/home/nosvers/uploads/'
VISUELS_DIR = '/home/nosvers/uploads/visuels/'


def get_current_week():
    return datetime.now().strftime('semana-%W')


def run():
    print(f"[{datetime.now()}] AGT-01: Buscando fotos nuevas...")

    week = get_current_week()
    week_dir = os.path.join(VISUELS_DIR, week)

    # Buscar fotos en uploads/
    photo_exts = {'.jpg', '.jpeg', '.png', '.heic', '.webp'}
    new_photos = [
        f for f in os.listdir(UPLOADS_DIR)
        if os.path.isfile(os.path.join(UPLOADS_DIR, f))
        and os.path.splitext(f)[1].lower() in photo_exts
    ]

    if not new_photos:
        print("  Sin fotos nuevas en uploads/")
        return

    os.makedirs(week_dir, exist_ok=True)

    for photo in new_photos:
        src = os.path.join(UPLOADS_DIR, photo)
        dst = os.path.join(week_dir, photo)
        shutil.move(src, dst)
        print(f"  Movida: {photo} → visuels/{week}/")

    print(f"[{datetime.now()}] AGT-01: {len(new_photos)} fotos organizadas en {week}")


if __name__ == '__main__':
    run()
