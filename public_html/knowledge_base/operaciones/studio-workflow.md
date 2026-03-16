# Studio V2 → WordPress · Workflow

> Documentado: 2026-03-13
> Archivos: `/home/nosvers/studio-to-wordpress.py` + `/home/nosvers/nosvers-studio-v2.html`

---

## Resumen

El Studio V2 es un editor visual standalone (HTML + JS) con 6 paginas completas del sitio nosvers.com. El script `studio-to-wordpress.py` convierte esas paginas en templates para Bricks Builder (PHP/JSON) y/o bloques Gutenberg (HTML), con opcion de subir como draft a WordPress via REST API.

---

## Paginas en el Studio V2

| # | Slug | Nombre | Contenido principal |
|---|------|--------|---------------------|
| 1 | home | Accueil | Hero, productos (Extrait 45EUR, Atelier 85EUR, Engrais 9.90EUR, Vers), engagements, testimonios, FAQ, ferme |
| 2 | extrait | Extrait Vivant | Ficha producto completa, cadena NosVers, 4 pasos uso, regla 4h, Service Frais 25EUR |
| 3 | engrais | Engrais Vert | Pack Universel, 3 especies (Trebol/Phacelie/Sarrasin), beneficios, modo de empleo, 4 packs estacionales |
| 4 | atelier | Atelier Sol Vivant | Programa dia completo con Africa, incluido (kit 45EUR, almuerzo, seguimiento 30d), reserva 85EUR |
| 5 | about | La Ferme | Historia Angel & Africa, equipo, vision/valores (sol vivant, resilience, soberania) |
| 6 | contact | Contact | Formulario, datos contacto (contact@nosvers.com, 07 82 25 92 77), FAQ |

---

## Arquitectura del Studio V2

El HTML es un SPA (Single Page Application). Las paginas NO estan en HTML estatico sino en funciones JavaScript que devuelven template literals:

```javascript
function pageHome(){return `...HTML content...`;}
function pageExtrait(){return `...`;}
// etc.
```

Elementos dinamicos:
- `${NAV()}` y `${FOOTER()}` - Componentes compartidos
- `${img(IMGS.key,'alt')}` - Imagenes con URLs reales de nosvers.com/wp-content
- `${e()}` - Atributos contenteditable para el modo editor

---

## El Script: studio-to-wordpress.py

### Que hace
1. Lee el archivo HTML del Studio V2
2. Extrae paginas desde las funciones JavaScript (regex sobre template literals)
3. Limpia el HTML: elimina `${e()}`, resuelve `${img(...)}` a URLs reales, quita NAV/FOOTER
4. Genera para cada pagina:
   - `{slug}.bricks.php` - Template PHP para Bricks Builder
   - `{slug}.bricks.json` - JSON de elementos Bricks (para importar en Bricks > Templates)
   - `{slug}.gutenberg.html` - Bloques Gutenberg (wp:heading, wp:paragraph, wp:image)
5. Opcionalmente sube como draft a WordPress via REST API

### Uso

```bash
# Generar templates (Bricks + Gutenberg)
/home/nosvers/venv/bin/python /home/nosvers/studio-to-wordpress.py \
  /home/nosvers/nosvers-studio-v2.html \
  --output-dir /home/nosvers/templates \
  --format both

# Solo Gutenberg + subir como draft a WordPress
/home/nosvers/venv/bin/python /home/nosvers/studio-to-wordpress.py \
  /home/nosvers/nosvers-studio-v2.html \
  --output-dir /home/nosvers/templates \
  --format gutenberg \
  --upload
```

### Argumentos

| Argumento | Default | Descripcion |
|-----------|---------|-------------|
| `input` | (requerido) | Ruta al HTML del Studio V2 |
| `--output-dir` / `-o` | `./templates` | Directorio de salida |
| `--format` | `both` | `bricks`, `gutenberg`, o `both` |
| `--upload` | off | Subir bloques Gutenberg como draft a WordPress |

### Variables de entorno (para --upload)

```bash
WP_URL=https://nosvers.com/wp-json/wp/v2/
WP_USER=claude_nosvers
WP_PASS=<ver credenciales>
```

---

## Dependencias

- Python 3.12 (disponible en `/home/nosvers/venv/bin/python`)
- `requests` - **PENDIENTE INSTALAR** para la opcion --upload

```bash
/home/nosvers/venv/bin/pip install requests
```

Sin `requests`, el script funciona para generar templates locales pero no puede subir a WordPress.

---

## Estado actual (2026-03-13)

- [x] Script creado y actualizado para leer formato Studio V2 (JS template literals)
- [x] Mapeo de imagenes IMGS.* a URLs reales de nosvers.com
- [x] Limpieza de atributos de editor (contenteditable, data-e, onclick)
- [ ] **PENDIENTE**: Instalar `requests` en venv (`pip install requests`)
- [ ] **PENDIENTE**: Ejecutar el script (requiere permisos Bash)
- [ ] **PENDIENTE**: Verificar templates generados
- [ ] **PENDIENTE**: Subir paginas como draft a WordPress con --upload

---

## Proximos pasos

1. **Ejecutar el script** (necesita permisos Bash):
   ```bash
   /home/nosvers/venv/bin/pip install requests
   /home/nosvers/venv/bin/python /home/nosvers/studio-to-wordpress.py \
     /home/nosvers/nosvers-studio-v2.html \
     -o /home/nosvers/templates --format both --upload
   ```

2. **Revisar templates** en `/home/nosvers/templates/`

3. **Importar en Bricks Builder**: Bricks > Templates > Import > subir los `.bricks.json`

4. **CSS custom**: Aplicar via Code Snippets plugin en wp_footer (paleta, tipografia ya definidas en el Studio)

5. **Reemplazar imagenes placeholder** (Unsplash) por fotos reales de la ferme cuando Africa las envie

---

## Imagenes reales vs placeholders

| Clave | Estado | URL |
|-------|--------|-----|
| extrait | REAL | nosvers.com/wp-content/uploads/2026/02/Lombrithe-arrosoir-1-600x1067.png |
| arrosoir | REAL | nosvers.com/wp-content/uploads/2026/02/Lombrithe-arrosoir-600x1067.png |
| engrais1 | REAL | nosvers.com/wp-content/uploads/2026/02/pomelli-image-600x1067.png |
| engrais2 | REAL | nosvers.com/wp-content/uploads/2026/02/Gemini_Generated_Image... |
| engrais3 | REAL | nosvers.com/wp-content/uploads/2026/02/Capture-decran... |
| logo | REAL | nosvers.com/wp-content/uploads/2026/02/cropped-Capture-decran... |
| jardin1-5 | PLACEHOLDER | Unsplash - reemplazar con fotos de Africa |
| ferme | PLACEHOLDER | Unsplash - reemplazar con foto real de la ferme |
| africa | PLACEHOLDER | Unsplash - reemplazar con foto real de Africa |
