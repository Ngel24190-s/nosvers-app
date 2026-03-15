# pendiente-para-code
*2026-03-14 13:32*

# Pendiente para Code — Ejecutar y hacer push
*Guardado: 2026-03-14 · Angel está fuera sin acceso*

---

## FIX URGENTE 1 — Guardar fotos al hacer foto en la app

**Problema:** Cuando Angel o África hacen una foto en la app, se manda al agente pero no se guarda en ningún sitio. Si se cierra la sesión, la foto se pierde.

**Fix en index.html (Hostinger public_html/granja/):**

En TODAS las funciones que envían fotos (hqChatGo, africaChatSend, agentPanelSend), ANTES de llamar a `api.php?action=agente`, añadir esta llamada:

```javascript
// GUARDAR FOTO ANTES DE PROCESAR
async function savePhoto(base64, type, category, caption) {
  try {
    await fetch(API_URL + '?action=upload_photo', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        image: base64,
        image_type: type,
        category: category,   // instagram | vers | huerto | general
        caption: caption || '',
        user: localStorage.getItem('nosvers_user') || 'unknown'
      })
    });
  } catch(e) { console.log('Photo save error:', e); }
}
```

Llamar a savePhoto() en cada sitio donde hay foto antes del fetch agente:
- Panel AGT-01, AGT-02, AGT-04, AGT-05 → category: 'instagram'
- Panel AGT-05 África → category: 'vers' o 'huerto' según contexto
- Vista África → category: 'general'

---

## FIX URGENTE 2 — AGT-02 Instagram responde a fotos en tiempo real

**Problema:** AGT-02 solo corre domingos. No genera el post cuando le das una foto ahora.

**Fix en index.html — en el panel del agente AGT-02:**

Cuando se envía una foto al panel de AGT-02, después de guardarla, llamar directamente a Claude con el system prompt de AGT-02 y la imagen. El resultado (caption + hashtags) se muestra en el panel Y se guarda en vault.

Añadir al final de agentPanelSend() cuando el agente es agt02_instagram:

```javascript
// Si es AGT-02 y hay foto → guardar resultado en vault
if (currentAgent.id === 'agt02_instagram' && reply && reply.length > 50) {
  const fecha = new Date().toISOString().split('T')[0];
  await fetch(API_URL + '?action=vault_write', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      category: 'agentes',
      filename: 'agt02-posts-pendientes',
      content: `\n\n## ${fecha} — Post generado desde foto\n\n${reply}`,
      mode: 'append'
    })
  });
}
```

---

## TAREA 3 — Menú de navegación WordPress

Actualizar el menú principal de nosvers.com con estas páginas nuevas.

Usar WP REST API con auth claude_nosvers / fkLzcfDHAE8i6WZQEUCVCvY3:

```python
import requests
auth = ('claude_nosvers', 'fkLzcfDHAE8i6WZQEUCVCvY3')

# Ver menús existentes
menus = requests.get('https://nosvers.com/wp-json/wp/v2/menus', auth=auth)
# O via wp-json/__experimentalMenus

# Páginas a incluir en el menú principal:
# - Accueil → / (homepage)
# - Extrait Vivant → /extrait-vivant-de-lombric/ (ID 462)
# - Engrais Vert → /pack-engrais-vert/ (ID 463)  
# - Atelier → /atelier-sol-vivant/ (ID 464)
# - La Ferme → /la-ferme-nosvers/ (ID 465)
# - Club Sol Vivant → /club-du-sol-vivant/ (ID 399)
# - Contact → /contact-nosvers/ (ID 466)
# - Blog → /blog/
```

Si la API de menús no está disponible → usar WP Admin directamente.

---

## TAREA 4 — Drive sync agent (drive_to_wordpress.py)

Ver instrucciones completas en: operaciones/instrucciones-code.md

IDs carpetas Drive (ya en operaciones/drive-config.md):
- Root: 1U3gQVGIH8j-_ARJv0Fqs8IQPlMrG0VDv
- instagram: 1SVQk3yGYhQztjISmSBK2wKNSl-crsLHk
- Vers de compost: 1_ZkuC6NLAx9iLMQFomShXr-vACBpzD-F
- Huerto: 1jHAay7I5rA267DUHAhwxZNPQw6-SYtGz
- General: 1-coq2zW5-KyMD5GHfV_Ys2M_1spcDkr5

Las carpetas deben estar compartidas como "cualquier persona con el enlace puede ver".
Angel tiene que hacer esto en Drive antes de que el agente pueda descargar.

---

## TAREA 5 — 6 nuevos agentes del MASTER_TASKS

Ver MASTER_TASKS.md en el repo — BLOQUE 2 y BLOQUE 3.
Solo hay 5 agentes en el array AGENTS de index.html.
Faltan: AGT-00, AGT-07, AGT-08, AGT-09, AGT-10, AGT-11.

---

## POST ESPÁRRAGO — Listo para publicar

Caption completo ya guardado en: agentes/agt02-posts-pendientes.md

Cuando Angel tenga la foto:
1. La sube desde nosvers.com/granja/ botón 📷
2. O la manda aquí a Claude directamente
3. El post está listo — solo falta adjuntar la foto y publicar en Instagram

---

## CUANDO HAGAS TODO — push

```bash
cd /home/nosvers  # o donde esté el repo clonado
git add -A
git commit -m "fix: guardar fotos + AGT-02 tiempo real + menú nav"
git push origin main
```

El autodeploy de Hostinger despliega automáticamente.

*NosVers · 2026-03-14 · Angel fuera, Code ejecuta mañana*


---
*2026-03-14 13:33*


## CONTEXTO FOTO ESPÁRRAGO (importante)

Angel y África hicieron una foto del espárrago directamente en la app de la granja.
La enviaron al panel del agente AGT-02 Instagram.
El agente la recibió pero NO guardó la foto NI generó el post.

La foto está perdida — la tienen en la galería del móvil.
El post del espárrago SÍ está escrito en: agentes/agt02-posts-pendientes.md

**Por qué falló:**
El panel del agente llama a api.php?action=agente con la imagen en base64.
El agente responde en el chat pero no guarda nada.
No hay flujo que conecte "foto → guardar → generar post → mostrar resultado".

**Lo que hay que construir:**
Cuando se envía una foto al panel de AGT-02:
1. Guardar la foto via upload_photo (para no perderla)
2. Llamar a Claude con system prompt de AGT-02 + la imagen
3. Mostrar el caption generado en el panel
4. Guardar el resultado en vault/agentes/agt02-posts-pendientes.md
5. Mostrar botón "✓ Aprobar para publicar" en el panel


---
*2026-03-14 14:30*


## TAREA — Publicación directa en Instagram via instagrapi

### Librería a usar
github.com/subzeroid/instagrapi — activa en 2026, más de 15k stars

### Instalar en VPS
```bash
/home/nosvers/venv/bin/pip install instagrapi --break-system-packages -q
```

### Añadir al .env del VPS
```
INSTAGRAM_USER=nosvers.ferme
INSTAGRAM_PASS=[contraseña Instagram — Angel la proporciona]
```

### Crear agents/instagram_publisher.py

```python
#!/usr/bin/env python3
"""
NosVers · Instagram Publisher
Publica fotos directamente en @nosvers.ferme via instagrapi
Sin pasar por Canva ni Meta Business Suite.
Se activa cuando Angel aprueba un post en la app.
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
    # Reusar sesión si existe (evita login repetido)
    if SESSION_FILE.exists():
        cl.load_settings(SESSION_FILE)
    else:
        cl.login(IG_USER, IG_PASS)
        cl.dump_settings(SESSION_FILE)
    return cl

def publish_photo(image_path: str, caption: str) -> dict:
    """
    Publicar una foto en Instagram.
    image_path: ruta local a la imagen JPEG/PNG
    caption: texto del post con hashtags
    """
    cl = get_client()
    media = cl.photo_upload(
        path=image_path,
        caption=caption,
        extra_data={"disable_comments": 0}
    )
    return {
        "ok": True,
        "media_id": str(media.pk),
        "shortcode": media.code,
        "url": f"https://www.instagram.com/p/{media.code}/"
    }

def notify(msg):
    if TELEGRAM_TOKEN:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": ANGEL_CHAT_ID, "text": msg, "parse_mode": "Markdown"},
            timeout=10
        )

# Llamada directa desde la app via api.php?action=publish_instagram
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
```

### Añadir endpoint en api.php

```php
case 'publish_instagram':
    // Solo Angel puede publicar
    $data = json_decode(file_get_contents('php://input'), true);
    $image_path = $data['image_path'] ?? '';
    $caption = $data['caption'] ?? '';
    
    if (!$image_path || !$caption) {
        echo json_encode(['error' => 'Faltan image_path y caption']);
        break;
    }
    
    // Ejecutar el publisher en el VPS
    $payload = json_encode(['image_path' => $image_path, 'caption' => $caption]);
    $py = '/home/nosvers/venv/bin/python3';
    $script = '/home/nosvers/agents/instagram_publisher.py';
    $output = shell_exec("$py $script " . escapeshellarg($payload) . " 2>&1");
    
    $result = json_decode($output, true);
    echo json_encode($result ?: ['error' => 'Error ejecutando publisher', 'output' => $output]);
    break;
```

### Flujo completo en la app (index.html)

En el panel del agente AGT-02, después de que Claude genere el caption:

```javascript
// Botón "✅ Aprobar y publicar" en el panel de AGT-02
async function publishToInstagram(imagePath, caption) {
  const res = await fetch(API_URL + '?action=publish_instagram', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ image_path: imagePath, caption: caption })
  });
  const d = await res.json();
  if (d.ok) {
    hqAddMsg('ai', `✅ **Publicado en Instagram**\n${d.url}`, 'ap-msgs');
  } else {
    hqAddMsg('ai', `❌ Error: ${d.error}`, 'ap-msgs');
  }
}
```

### Flujo completo de uso

1. África o Angel hacen foto en la app
2. Se envía al panel de AGT-02
3. Claude genera caption + hashtags
4. Aparece botón "✅ Publicar en Instagram"
5. Angel toca el botón
6. La foto se publica directamente en @nosvers.ferme
7. Telegram confirma con la URL del post

### Notas importantes
- La primera vez pedirá verificación 2FA de Instagram — hacerlo en casa
- Después guarda la sesión y no vuelve a pedir login
- Si Instagram bloquea → usar proxy residencial (instagrapi lo soporta)
- Angel debe dar la contraseña de Instagram para el .env

### Alternativa sin contraseña (oficial)
Meta Graph API con cuenta Business verificada.
Requiere: App de Meta aprobada + token de larga duración.
Más seguro pero tarda 1-2 semanas en conseguir los permisos.
Recomendación: empezar con instagrapi ahora, migrar a oficial cuando crezca la cuenta.


---
*2026-03-14 14:34*


## TAREA — AGT-01 edición automática de imágenes con Pillow

### Instalar
```bash
/home/nosvers/venv/bin/pip install Pillow --break-system-packages -q
```

### Actualizar agents/agt01_visual.py con esta función de edición:

```python
from PIL import Image, ImageEnhance, ImageDraw, ImageFont, ImageFilter
import os

def editar_para_instagram(input_path: str, output_path: str = None, 
                           texto: str = "@nosvers.ferme · Dordogne") -> str:
    """
    Edita una foto siguiendo el protocolo visual NosVers:
    1. Recortar a 4:5 (1080x1350px) — formato Instagram óptimo
    2. Exposición +0.15 (ligeramente sobreexpuesto, luz natural)
    3. Balance blancos cálido
    4. Saturación selectiva (verdes +20%, tierra +15%)
    5. Contraste suave +10%
    6. Viñeta sutil
    7. Texto @nosvers.ferme en parte inferior
    8. Export JPEG 90%
    """
    img = Image.open(input_path).convert('RGB')
    w, h = img.size
    
    # 1. Recortar a 4:5 centrado
    target_ratio = 4 / 5
    current_ratio = w / h
    if current_ratio > target_ratio:
        # más ancho de lo necesario — recortar lados
        new_w = int(h * target_ratio)
        left = (w - new_w) // 2
        img = img.crop((left, 0, left + new_w, h))
    else:
        # más alto de lo necesario — recortar arriba/abajo
        new_h = int(w / target_ratio)
        top = (h - new_h) // 2
        img = img.crop((0, top, w, top + new_h))
    
    # Redimensionar a 1080x1350
    img = img.resize((1080, 1350), Image.LANCZOS)
    
    # 2. Exposición +15%
    img = ImageEnhance.Brightness(img).enhance(1.15)
    
    # 3. Calidez (balance blancos cálido)
    r, g, b = img.split()
    r = r.point(lambda i: min(255, int(i * 1.05)))  # más rojo
    b = b.point(lambda i: int(i * 0.95))             # menos azul
    img = Image.merge('RGB', (r, g, b))
    
    # 4. Saturación +15%
    img = ImageEnhance.Color(img).enhance(1.15)
    
    # 5. Contraste suave +10%
    img = ImageEnhance.Contrast(img).enhance(1.10)
    
    # 6. Viñeta sutil
    vignette = Image.new('L', (1080, 1350), 255)
    draw = ImageDraw.Draw(vignette)
    for i in range(60):
        opacity = int(255 - (i * 3.5))
        draw.ellipse([i*2, i*2, 1080-i*2, 1350-i*2], outline=opacity)
    img = Image.composite(img, Image.new('RGB', (1080, 1350), (0,0,0)), vignette)
    
    # 7. Texto @nosvers.ferme
    draw = ImageDraw.Draw(img)
    # Fondo semitransparente en la parte inferior
    overlay = Image.new('RGBA', (1080, 1350), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.rectangle([(0, 1230), (1080, 1350)], fill=(0, 0, 0, 100))
    img = img.convert('RGBA')
    img = Image.alpha_composite(img, overlay).convert('RGB')
    
    # Texto
    draw = ImageDraw.Draw(img)
    try:
        # Intentar usar una fuente del sistema
        from PIL import ImageFont
        font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf', 28)
        font_small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf', 22)
    except:
        font = ImageFont.load_default()
        font_small = font
    
    draw.text((40, 1260), texto, fill=(253, 250, 244, 220), font=font)
    draw.text((40, 1295), "🌿 Ferme lombricole · Neuvic, Dordogne", fill=(180, 170, 150, 180), font=font_small)
    
    # 8. Guardar JPEG 90%
    if not output_path:
        base = os.path.splitext(input_path)[0]
        output_path = base + '_nosvers_edited.jpg'
    
    img.save(output_path, 'JPEG', quality=90, optimize=True)
    return output_path


def procesar_foto_instagram(input_path: str, caption_hint: str = "") -> dict:
    """
    Pipeline completo: editar foto + analizar con Claude Vision + generar caption
    Retorna: { edited_path, caption, hashtags, instagram_ready: True }
    """
    import requests, os
    from dotenv import load_dotenv
    load_dotenv('/home/nosvers/.env')
    
    ANTHROPIC_KEY = os.getenv('ANTHROPIC_API_KEY', '')
    
    # 1. Editar la foto
    edited_path = editar_para_instagram(input_path)
    
    # 2. Analizar con Claude Vision y generar caption
    import base64
    with open(edited_path, 'rb') as f:
        img_b64 = base64.b64encode(f.read()).decode()
    
    payload = {
        "model": "claude-sonnet-4-6",
        "max_tokens": 600,
        "system": """Eres AGT-02 Instagram Manager de NosVers, ferme lombricole en Dordogne.
Analizas la foto y generas el caption perfecto para @nosvers.ferme.
Voz: educativa, auténtica, cercana. Idioma: FRANCÉS.
Formato de respuesta JSON:
{
  "caption": "texto del caption con emojis",
  "hashtags": "#tag1 #tag2 ...",
  "suggestion": "tip de publicación (horario, formato, story)"
}""",
        "messages": [{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": img_b64}},
                {"type": "text", "text": f"Genera el caption para Instagram de esta foto de la ferme NosVers. Contexto adicional: {caption_hint or 'foto de la ferme'}"}
            ]
        }]
    }
    
    r = requests.post('https://api.anthropic.com/v1/messages',
                      headers={'x-api-key': ANTHROPIC_KEY, 'anthropic-version': '2023-06-01', 'Content-Type': 'application/json'},
                      json=payload, timeout=30)
    
    import json, re
    text = r.json().get('content', [{}])[0].get('text', '{}')
    # Extraer JSON de la respuesta
    match = re.search(r'\{.*\}', text, re.DOTALL)
    data = json.loads(match.group()) if match else {"caption": text, "hashtags": "#nosvers #solVivant #dordogne", "suggestion": "Publicar lunes 18h"}
    
    return {
        "edited_path": edited_path,
        "caption": data.get("caption", ""),
        "hashtags": data.get("hashtags", ""),
        "suggestion": data.get("suggestion", ""),
        "instagram_ready": True
    }
```

### Nuevo endpoint en api.php: process_photo_instagram

```php
case 'process_photo_instagram':
    $data = json_decode(file_get_contents('php://input'), true);
    $image_b64 = $data['image'] ?? '';
    $caption_hint = $data['caption_hint'] ?? '';
    
    if (!$image_b64) {
        echo json_encode(['error' => 'No image']);
        break;
    }
    
    // Guardar imagen temporalmente
    $tmp = '/tmp/nosvers_' . time() . '.jpg';
    file_put_contents($tmp, base64_decode($image_b64));
    
    // Procesar con AGT-01
    $py = '/home/nosvers/venv/bin/python3';
    $script = '/home/nosvers/agents/agt01_visual.py';
    $payload = json_encode(['input_path' => $tmp, 'caption_hint' => $caption_hint]);
    $output = shell_exec("$py $script process " . escapeshellarg($payload) . " 2>&1");
    
    $result = json_decode($output, true);
    
    if ($result && $result['instagram_ready']) {
        // Devolver imagen editada en base64
        $edited_b64 = base64_encode(file_get_contents($result['edited_path']));
        $result['edited_image_b64'] = $edited_b64;
        unlink($tmp);
        unlink($result['edited_path']);
    }
    
    echo json_encode($result ?: ['error' => $output]);
    break;
```

### En index.html — flujo completo al subir foto a AGT-02:

```javascript
// Cuando África o Angel suben foto al panel AGT-02:
async function processPhotoForInstagram(base64, type, captionHint) {
  // 1. Mostrar "Procesando..."
  hqAddMsg('ai', '⚙️ Editando la foto y generando el caption...', 'ap-msgs');
  
  // 2. Llamar al pipeline completo
  const res = await fetch(API_URL + '?action=process_photo_instagram', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ image: base64, image_type: type, caption_hint: captionHint })
  });
  const data = await res.json();
  
  if (data.instagram_ready) {
    // 3. Mostrar preview de la imagen editada
    if (data.edited_image_b64) {
      const img = document.createElement('img');
      img.src = `data:image/jpeg;base64,${data.edited_image_b64}`;
      img.style = 'max-width:200px;border-radius:8px;margin-bottom:8px';
      document.getElementById('ap-msgs').appendChild(img);
    }
    
    // 4. Mostrar caption generado
    hqAddMsg('ai', `**Caption generado:**\n\n${data.caption}\n\n${data.hashtags}\n\n_${data.suggestion}_`, 'ap-msgs');
    
    // 5. Botones de acción
    const btns = document.createElement('div');
    btns.style = 'display:flex;gap:8px;margin-top:8px';
    btns.innerHTML = `
      <button onclick="publishToInstagram('${data.edited_path}','${encodeURIComponent(data.caption+' '+data.hashtags)}')"
        style="padding:8px 14px;background:#3D6B20;color:white;border:none;border-radius:8px;cursor:pointer;font-family:inherit">
        ✅ Publicar en Instagram
      </button>
      <button onclick="savePostForLater('${data.caption}','${data.hashtags}')"
        style="padding:8px 14px;background:transparent;color:#7AB648;border:1px solid #7AB648;border-radius:8px;cursor:pointer;font-family:inherit">
        💾 Guardar para luego
      </button>`;
    document.getElementById('ap-msgs').appendChild(btns);
  }
}
```

### Resultado final
Flujo completo sin Canva:
1. Foto hecha en la app
2. AGT-01 edita automáticamente (4:5, exposición, texto)
3. Claude Vision genera el caption en francés
4. Preview en la app + botones Publicar / Guardar
5. ✅ → instagrapi publica directamente


---
*2026-03-15 08:08*


---
## TAREA REPOS — Instalar en Claude Code (terminal del VPS)

Ejecutar en la sesión tmux de Claude Code:

### 1. Superpowers (metodología TDD + planning)
```
/plugin marketplace add obra/superpowers-marketplace
/plugin install superpowers@superpowers-marketplace
```

### 2. WordPress skills (para arreglar nosvers.com)
```
/plugin marketplace add elvismdev/claude-wordpress-skills
/plugin install claude-wordpress-skills@claude-wordpress-skills
```

### 3. Frontend design (para que la web se parezca al Studio V2)
```
/plugin install frontend-design@superpowers-marketplace
```

### 4. Web testing con Playwright
```
/plugin install webapp-testing@superpowers-marketplace
```

### 5. Subagentes especializados
```
curl -sO https://raw.githubusercontent.com/VoltAgent/awesome-claude-code-subagents/main/install-agents.sh
chmod +x install-agents.sh
./install-agents.sh
# Seleccionar: workflow-orchestrator, python-expert, web-developer
```

### 6. Marketing skills de Ayrshare
```
/plugin install marketingskills@ayrshare
```

### 7. Ayrshare MCP para RRSS (cuando Angel decida opción B gratis o pago)
```bash
# Opción B gratis — Facebook:
git clone https://github.com/HagaiHen/facebook-mcp-server /home/nosvers/facebook-mcp
cd /home/nosvers/facebook-mcp && npm install

# Registrar en mcp_server.py de NosVers como herramienta adicional
```

---

## TAREA TELEGRAM — Fix chat_id Angel

El bot está corriendo con `ANGEL_CHAT_ID=5752097691` pero ese ID puede ser incorrecto.

**Pasos:**
1. El bot ya fue modificado temporalmente para aceptar cualquier usuario y loguear IDs
2. Cuando Angel escriba al bot, ver el log: `journalctl -u nosvers-bot -f | grep AUTH`
3. Capturar el user_id real
4. Actualizar en /home/nosvers/.env: `ANGEL_CHAT_ID=ID_REAL`
5. Restaurar is_authorized() para que solo acepte el ID correcto
6. Reiniciar bot: `systemctl restart nosvers-bot`

---

## TAREA PENDIENTE — Push todo lo de ayer

Hacer push de TODOS los cambios pendientes:
```bash
cd /home/nosvers  # o donde esté el repo
git add -A
git commit -m "feat: HQ UI completa + 6 agentes marketing + pipeline instagram + repos skills"
git push origin main
```

Incluye: index.html con HQ Angel + vista África + 6 agentes python + pipeline instagram.

---
*Angel fuera — 2026-03-15*
