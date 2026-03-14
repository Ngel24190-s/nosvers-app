# instrucciones-code
*2026-03-14 12:29*

# INSTRUCCIONES CODE — Drive + AGT-01 Visual
*2026-03-14*

## TAREA URGENTE — Conectar AGT-01 a Google Drive

### 1. Añadir IDs Drive al .env del VPS

```bash
cat >> /home/nosvers/.env << 'EOF'
DRIVE_FOLDER_ROOT=1U3gQVGIH8j-_ARJv0Fqs8IQPlMrG0VDv
DRIVE_FOLDER_INSTAGRAM=1SVQk3yGYhQztjISmSBK2wKNSl-crsLHk
DRIVE_FOLDER_VERS=1_ZkuC6NLAx9iLMQFomShXr-vACBpzD-F
DRIVE_FOLDER_HUERTO=1jHAay7I5rA267DUHAhwxZNPQw6-SYtGz
DRIVE_FOLDER_GENERAL=1-coq2zW5-KyMD5GHfV_Ys2M_1spcDkr5
EOF
```

### 2. Instalar google-api-python-client en venv

```bash
/home/nosvers/venv/bin/pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib --break-system-packages -q
```

### 3. Actualizar agt01_visual.py para leer Drive

El agente debe:
- Listar archivos nuevos en las carpetas Drive via Google Drive API
- Descargar las imágenes nuevas a /home/nosvers/uploads/
- Analizarlas con Claude Vision (ya tiene la API key)
- Las candidatas para Instagram → copiar a /home/nosvers/uploads/instagram/
- Las candidatas para la web → subirlas a WordPress Media Library via WP REST API
- Guardar log en vault/agentes/agt01_visual/_memoria.md

### 4. Configurar Google Drive API (service account)

Alternativa más simple sin OAuth — usar URLs de descarga directa:
Los archivos públicos de Drive se pueden descargar con:
`https://drive.google.com/uc?export=download&id=FILE_ID`

Para que funcione sin OAuth:
- Las carpetas NosVers Media deben estar compartidas como "cualquier persona con el enlace puede ver"
- Angel debe hacer esto en Drive: click derecho en "NosVers Media" → Compartir → cambiar acceso

### 5. Script drive_to_wordpress.py (nuevo)

Crear /home/nosvers/agents/drive_to_wordpress.py:
- Lee los archivos de cada carpeta Drive
- Descarga las imágenes nuevas (no descargadas antes)
- Las sube a WordPress Media Library
- Devuelve las URLs de WordPress
- Los agentes de contenido usan esas URLs para enriquecer posts/páginas

### 6. Cron drive sync

```
0 */2 * * * /home/nosvers/venv/bin/python3 /home/nosvers/agents/drive_to_wordpress.py >> /home/nosvers/logs/drive_sync.log 2>&1
```

## PÁGINAS WEB — Estado tras mis actualizaciones

YA PUBLICADAS (no tocar):
- nosvers.com/ — Homepage actualizada
- nosvers.com/extrait-vivant-de-lombric/ — ✅
- nosvers.com/pack-engrais-vert/ — ✅
- nosvers.com/atelier-sol-vivant/ — ✅
- nosvers.com/la-ferme-nosvers/ — ✅
- nosvers.com/contact-nosvers/ — ✅
- nosvers.com/club-du-sol-vivant/ — ✅

PENDIENTE — Menú de navegación WordPress:
Actualizar el menú principal para que incluya:
- Accueil → nosvers.com/
- Extrait Vivant → /extrait-vivant-de-lombric/
- Engrais Vert → /pack-engrais-vert/ (o /boutique/)
- Atelier → /atelier-sol-vivant/
- La Ferme → /la-ferme-nosvers/
- Club → /club-du-sol-vivant/
- Contact → /contact-nosvers/

Usar WP REST API:
GET /wp-json/wp/v2/menus para ver menús existentes
POST /wp-json/wp/v2/menu-items para actualizar items
