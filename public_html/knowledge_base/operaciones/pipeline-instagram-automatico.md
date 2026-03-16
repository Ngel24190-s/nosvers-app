# pipeline-instagram-automatico
*2026-03-14 14:37*

# Pipeline Instagram Automático — Sin interacción hasta validación
*Aprobado por Angel — 2026-03-14*

## Flujo completo

```
FOTO HECHA EN APP
      ↓
1. AGT-01 edita con Pillow
   (recorte 4:5, exposición, calidez, @nosvers.ferme)
      ↓
2. Claude Vision analiza la foto editada
   → genera caption en francés
   → genera hashtags
      ↓
3. Canva API — sin interacción humana:
   - Sube la foto editada como asset
   - Genera diseño con brand kit kAHB5U-R_6E
   - Exporta JPEG 1080x1350px
      ↓
4. Telegram a Angel:
   - Preview del post final (imagen Canva exportada)
   - Caption completo listo para copiar
   - Dos botones: ✅ Publicar | ❌ Rechazar
      ↓
5. Angel toca ✅ en Telegram
      ↓
6. instagrapi publica en @nosvers.ferme
      ↓
7. Telegram confirma: "✅ Publicado → URL del post"
```

---

## Implementación técnica para Code

### agents/pipeline_instagram.py

```python
#!/usr/bin/env python3
"""
NosVers · Pipeline Instagram Automático
Foto → Edición → Canva → Caption → Telegram validación → Publicar
"""
import os, json, base64, requests, tempfile
from pathlib import Path
from PIL import Image, ImageEnhance, ImageDraw, ImageFont
from dotenv import load_dotenv
load_dotenv('/home/nosvers/.env')

ANTHROPIC_KEY = os.getenv('ANTHROPIC_API_KEY', '')
CANVA_TOKEN = os.getenv('CANVA_API_TOKEN', '')  # Token API de Canva
CANVA_BRAND_KIT = 'kAHB5U-R_6E'
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN', '')
ANGEL_CHAT_ID = os.getenv('ANGEL_CHAT_ID', '5752097691')
IG_USER = os.getenv('INSTAGRAM_USER', 'nosvers.ferme')
IG_PASS = os.getenv('INSTAGRAM_PASS', '')
VAULT = Path('/home/nosvers/public_html/knowledge_base')

# Cola de posts pendientes de validación
PENDING_FILE = Path('/home/nosvers/uploads/pending_posts.json')

# ─── PASO 1: EDITAR FOTO ─────────────────────────────────────────
def editar_foto(input_path: str) -> str:
    img = Image.open(input_path).convert('RGB')
    w, h = img.size
    
    # Recortar a 4:5
    target_ratio = 4 / 5
    if w / h > target_ratio:
        new_w = int(h * target_ratio)
        img = img.crop(((w - new_w) // 2, 0, (w - new_w) // 2 + new_w, h))
    else:
        new_h = int(w / target_ratio)
        img = img.crop((0, (h - new_h) // 2, w, (h - new_h) // 2 + new_h))
    
    img = img.resize((1080, 1350), Image.LANCZOS)
    img = ImageEnhance.Brightness(img).enhance(1.12)
    img = ImageEnhance.Color(img).enhance(1.15)
    img = ImageEnhance.Contrast(img).enhance(1.08)
    
    # Balance cálido
    r, g, b = img.split()
    r = r.point(lambda i: min(255, int(i * 1.04)))
    b = b.point(lambda i: int(i * 0.96))
    img = Image.merge('RGB', (r, g, b))
    
    output = input_path.replace('.jpg', '_edited.jpg').replace('.jpeg', '_edited.jpg').replace('.png', '_edited.jpg')
    img.save(output, 'JPEG', quality=92, optimize=True)
    return output

# ─── PASO 2: GENERAR CAPTION CON CLAUDE VISION ──────────────────
def generar_caption(image_path: str, contexto: str = "") -> dict:
    with open(image_path, 'rb') as f:
        img_b64 = base64.b64encode(f.read()).decode()
    
    payload = {
        "model": "claude-sonnet-4-6",
        "max_tokens": 600,
        "system": """Eres AGT-02 Instagram Manager de NosVers, ferme lombricole en Dordogne.
Generas captions perfectos para @nosvers.ferme. IDIOMA: francés siempre.
Voz: educativa, auténtica, cercana. Sin "Découvrez" ni "Profitez". Un solo CTA suave.
Responde ÚNICAMENTE con JSON válido, sin texto extra:
{"caption": "texto completo con emojis", "hashtags": "#tag1 #tag2 ...", "horario": "lunes 18h"}""",
        "messages": [{"role": "user", "content": [
            {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": img_b64}},
            {"type": "text", "text": f"Genera el caption Instagram para esta foto de la ferme NosVers.{' Contexto: ' + contexto if contexto else ''}"}
        ]}]
    }
    
    r = requests.post('https://api.anthropic.com/v1/messages',
        headers={'x-api-key': ANTHROPIC_KEY, 'anthropic-version': '2023-06-01', 'Content-Type': 'application/json'},
        json=payload, timeout=30)
    
    text = r.json().get('content', [{}])[0].get('text', '{}')
    import re
    match = re.search(r'\{.*\}', text, re.DOTALL)
    return json.loads(match.group()) if match else {
        "caption": text, 
        "hashtags": "#nosvers #solVivant #dordogne #lombricompost",
        "horario": "lunes 18h"
    }

# ─── PASO 3: CANVA API — SUBIR FOTO Y EXPORTAR ──────────────────
def crear_post_canva(image_path: str, caption_data: dict) -> str:
    """
    1. Sube la imagen editada como asset a Canva
    2. Genera un diseño con la foto + brand kit NosVers
    3. Exporta el diseño como JPEG
    Retorna: ruta del JPEG exportado
    """
    headers = {
        'Authorization': f'Bearer {CANVA_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    # Subir asset a Canva
    with open(image_path, 'rb') as f:
        img_data = f.read()
    
    # API Canva: crear upload job
    upload_r = requests.post('https://api.canva.com/rest/v1/asset-uploads',
        headers={'Authorization': f'Bearer {CANVA_TOKEN}', 
                 'Content-Type': 'image/jpeg',
                 'Asset-Upload-Metadata': json.dumps({"name_base64": base64.b64encode(b"foto_nosvers.jpg").decode()})},
        data=img_data, timeout=30)
    
    asset_id = None
    if upload_r.status_code in [200, 201]:
        asset_id = upload_r.json().get('asset', {}).get('id')
    
    # Generar diseño via generate-design con el asset
    if asset_id:
        gen_r = requests.post('https://api.canva.com/rest/v1/designs/generate',
            headers=headers,
            json={
                "design_type": "instagram_post",
                "brand_kit_id": CANVA_BRAND_KIT,
                "asset_ids": [asset_id],
                "query": "Post Instagram NosVers ferme Dordogne. Photo pleine page de la ferme. Texte blanc en bas: @nosvers.ferme · Dordogne. Style editorial organique minimal."
            }, timeout=60)
        
        if gen_r.status_code == 200:
            candidates = gen_r.json().get('result', {}).get('generated_designs', [])
            if candidates:
                # Tomar el primer candidato y exportarlo
                candidate_id = candidates[0].get('candidate_id')
                job_id = gen_r.json().get('job', {}).get('id', '')
                
                # Crear diseño desde candidato
                create_r = requests.post('https://api.canva.com/rest/v1/designs',
                    headers=headers,
                    json={"candidate_id": candidate_id, "job_id": job_id},
                    timeout=30)
                
                if create_r.status_code == 200:
                    design_id = create_r.json().get('design', {}).get('id')
                    
                    # Exportar el diseño como JPEG
                    export_r = requests.post(f'https://api.canva.com/rest/v1/exports',
                        headers=headers,
                        json={"design_id": design_id, "format": "jpg", "export_quality": "pro"},
                        timeout=60)
                    
                    if export_r.status_code == 200:
                        export_url = export_r.json().get('job', {}).get('urls', [None])[0]
                        if export_url:
                            # Descargar el JPEG exportado
                            output = image_path.replace('_edited.jpg', '_canva.jpg')
                            dl = requests.get(export_url, timeout=30)
                            with open(output, 'wb') as f:
                                f.write(dl.content)
                            return output
    
    # Fallback: usar la foto editada directamente (sin Canva)
    return image_path

# ─── PASO 4: ENVIAR A TELEGRAM PARA VALIDACIÓN ─────────────────
def enviar_preview_telegram(image_path: str, caption_data: dict, post_id: str):
    """
    Envía la imagen + caption a Angel por Telegram.
    Guarda el post en cola pendiente para cuando Angel valide.
    """
    # Guardar en cola pendiente
    pending = {}
    if PENDING_FILE.exists():
        pending = json.loads(PENDING_FILE.read_text())
    
    pending[post_id] = {
        "image_path": image_path,
        "caption": caption_data.get('caption', ''),
        "hashtags": caption_data.get('hashtags', ''),
        "status": "pending"
    }
    PENDING_FILE.write_text(json.dumps(pending, ensure_ascii=False, indent=2))
    
    caption_text = caption_data.get('caption', '')
    hashtags = caption_data.get('hashtags', '')
    horario = caption_data.get('horario', 'lunes 18h')
    
    # Enviar foto a Telegram
    with open(image_path, 'rb') as img:
        msg = (f"🌿 *Post listo para Instagram*\n\n"
               f"📋 *Caption:*\n{caption_text}\n\n"
               f"{hashtags}\n\n"
               f"⏰ Horario sugerido: {horario}\n\n"
               f"Responde:\n✅ /publicar_{post_id}\n❌ /rechazar_{post_id}")
        
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto",
            data={"chat_id": ANGEL_CHAT_ID, "caption": msg, "parse_mode": "Markdown"},
            files={"photo": img}, timeout=30)

# ─── PASO 5: PUBLICAR EN INSTAGRAM (llamado desde bot.py) ───────
def publicar_instagram(post_id: str) -> dict:
    if not PENDING_FILE.exists():
        return {"ok": False, "error": "No hay posts pendientes"}
    
    pending = json.loads(PENDING_FILE.read_text())
    post = pending.get(post_id)
    if not post:
        return {"ok": False, "error": f"Post {post_id} no encontrado"}
    
    try:
        from instagrapi import Client
        from pathlib import Path as P
        
        cl = Client()
        session_file = P('/home/nosvers/.instagram_session.json')
        if session_file.exists():
            cl.load_settings(session_file)
        else:
            cl.login(IG_USER, IG_PASS)
            cl.dump_settings(session_file)
        
        full_caption = post['caption'] + '\n\n' + post['hashtags']
        media = cl.photo_upload(path=post['image_path'], caption=full_caption)
        
        # Actualizar estado
        pending[post_id]['status'] = 'published'
        pending[post_id]['url'] = f"https://www.instagram.com/p/{media.code}/"
        PENDING_FILE.write_text(json.dumps(pending, ensure_ascii=False, indent=2))
        
        # Confirmar a Angel
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": ANGEL_CHAT_ID, 
                  "text": f"✅ *Publicado en Instagram*\n{pending[post_id]['url']}",
                  "parse_mode": "Markdown"}, timeout=10)
        
        return {"ok": True, "url": pending[post_id]['url']}
    
    except Exception as e:
        return {"ok": False, "error": str(e)}

# ─── PIPELINE PRINCIPAL ──────────────────────────────────────────
def run_pipeline(input_image_path: str, contexto: str = ""):
    import uuid
    post_id = str(uuid.uuid4())[:8]
    
    print(f"[Pipeline] Iniciando post {post_id}")
    
    # 1. Editar
    edited = editar_foto(input_image_path)
    print(f"[Pipeline] Foto editada: {edited}")
    
    # 2. Caption
    caption_data = generar_caption(edited, contexto)
    print(f"[Pipeline] Caption generado")
    
    # 3. Canva
    final_image = crear_post_canva(edited, caption_data)
    print(f"[Pipeline] Post Canva: {final_image}")
    
    # 4. Telegram
    enviar_preview_telegram(final_image, caption_data, post_id)
    print(f"[Pipeline] Preview enviado a Telegram. Post ID: {post_id}")
    
    return {"post_id": post_id, "status": "pending_validation"}

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        data = json.loads(sys.argv[1])
        if data.get('action') == 'publish':
            result = publicar_instagram(data['post_id'])
        else:
            result = run_pipeline(data.get('image_path', ''), data.get('contexto', ''))
        print(json.dumps(result))
```

### Añadir al bot.py — comandos /publicar y /rechazar

```python
# En bot.py, añadir estos handlers:

@dp.message(Command(re.compile(r'publicar_(\w+)')))
async def cmd_publicar(message: Message, command: CommandObject):
    post_id = command.args or message.text.split('_', 1)[1]
    await message.reply("⏳ Publicando en Instagram...")
    
    import subprocess
    result = subprocess.run(
        ['/home/nosvers/venv/bin/python3', 
         '/home/nosvers/agents/pipeline_instagram.py',
         json.dumps({'action': 'publish', 'post_id': post_id})],
        capture_output=True, text=True, timeout=60
    )
    
    data = json.loads(result.stdout) if result.stdout else {'ok': False, 'error': result.stderr}
    if data.get('ok'):
        await message.reply(f"✅ Publicado!\n{data['url']}")
    else:
        await message.reply(f"❌ Error: {data.get('error')}")

@dp.message(Command(re.compile(r'rechazar_(\w+)')))
async def cmd_rechazar(message: Message, command: CommandObject):
    post_id = message.text.split('_', 1)[1]
    await message.reply(f"❌ Post {post_id} rechazado. Eliminado de la cola.")
    # Marcar como rechazado en el JSON
```

### Endpoint en api.php

```php
case 'run_instagram_pipeline':
    $data = json_decode(file_get_contents('php://input'), true);
    $image_b64 = $data['image'] ?? '';
    $contexto = $data['contexto'] ?? '';
    
    // Guardar imagen
    $tmp = '/home/nosvers/uploads/' . time() . '_pipeline.jpg';
    file_put_contents($tmp, base64_decode($image_b64));
    
    // Lanzar pipeline en background
    $payload = json_encode(['image_path' => $tmp, 'contexto' => $contexto]);
    $cmd = "/home/nosvers/venv/bin/python3 /home/nosvers/agents/pipeline_instagram.py " 
           . escapeshellarg($payload) . " > /home/nosvers/logs/pipeline.log 2>&1 &";
    exec($cmd);
    
    echo json_encode(['ok' => true, 'message' => 'Pipeline iniciado — recibirás preview en Telegram']);
    break;
```

### Canva API Token
Angel necesita generar un token de API de Canva:
1. canva.com/developers → Create integration
2. Scopes: asset:write, design:content:write, design:meta:read
3. Guardar token en /home/nosvers/.env como CANVA_API_TOKEN=...

### Instalar dependencias

```bash
/home/nosvers/venv/bin/pip install instagrapi Pillow --break-system-packages -q
```

---

## Resumen del flujo que verá Angel

```
📱 Hace foto en la app
⚙️ 30-60 segundos de procesamiento automático
📲 Telegram: preview del post con foto Canva + caption
   ✅ /publicar_abc123  |  ❌ /rechazar_abc123
👆 Angel toca /publicar_abc123
🚀 Publicado en @nosvers.ferme
✅ Telegram: "Publicado → URL del post"
```

Zero Canva manual. Zero Instagram manual. Solo la validación.
