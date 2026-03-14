#!/usr/bin/env python3
"""
NosVers · Studio V2 → WordPress (Bricks Builder)
Convierte páginas exportadas del Studio HTML en templates PHP para Bricks Builder.

Uso:
    python3 studio-to-wordpress.py input.html [--output-dir ./templates]

El script:
1. Lee el HTML del Studio V2
2. Identifica las páginas/secciones
3. Genera templates PHP compatibles con Bricks Builder
4. Opcionalmente sube como draft via WP REST API
"""

import os
import re
import sys
import json
import argparse
from html.parser import HTMLParser
from datetime import datetime

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    from dotenv import load_dotenv
    load_dotenv('/home/nosvers/.env')
except ImportError:
    pass


# ── Config ────────────────────────────────────────────────
WP_URL = os.getenv('WP_URL', 'https://nosvers.com/wp-json/wp/v2/')
WP_USER = os.getenv('WP_USER', '')
WP_PASS = os.getenv('WP_PASS', '')

# Bricks Builder template structure
BRICKS_TEMPLATE = '''<?php
/**
 * NosVers · {page_name}
 * Generado desde Studio V2 — {timestamp}
 * Template para Bricks Builder
 */

if (!defined('ABSPATH')) exit;
?>

{bricks_elements}
'''

# Mapeo de clases CSS del Studio a elementos Bricks
STUDIO_TO_BRICKS = {
    'hero': 'section',
    'section': 'section',
    'header': 'header',
    'footer': 'footer',
    'cta': 'div',
    'card': 'div',
    'grid': 'div',
    'text': 'div',
    'image': 'img',
    'button': 'a',
    'heading': 'heading',
}

# Paleta NosVers
NOSVERS_STYLES = {
    'bg_warm': '#FEFAF4',
    'green': '#5A7A2E',
    'font_heading': 'Playfair Display',
    'font_body': 'DM Sans',
}


class StudioParser(HTMLParser):
    """Parse Studio V2 HTML and extract pages/sections."""

    def __init__(self):
        super().__init__()
        self.pages = []
        self.current_page = None
        self.current_section = None
        self.sections = []
        self.in_page = False
        self.depth = 0
        self.content_buffer = []
        self.tag_stack = []

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        classes = attrs_dict.get('class', '').split()
        data_page = attrs_dict.get('data-page', '')

        # Detect page containers
        if data_page or 'page' in classes:
            self.in_page = True
            self.current_page = {
                'name': data_page or attrs_dict.get('id', f'page-{len(self.pages)}'),
                'sections': [],
                'raw_html': ''
            }
            self.depth = 0

        # Detect sections within pages
        if self.in_page:
            self.depth += 1
            section_type = None
            for cls in classes:
                if cls in STUDIO_TO_BRICKS:
                    section_type = cls
                    break

            if section_type and self.depth <= 3:
                self.current_section = {
                    'type': section_type,
                    'bricks_element': STUDIO_TO_BRICKS[section_type],
                    'classes': classes,
                    'content': '',
                    'attrs': attrs_dict,
                }

        # Build raw HTML
        attr_str = ' '.join(f'{k}="{v}"' for k, v in attrs)
        self.content_buffer.append(f'<{tag} {attr_str}>' if attr_str else f'<{tag}>')

    def handle_endtag(self, tag):
        self.content_buffer.append(f'</{tag}>')

        if self.in_page:
            self.depth -= 1
            if self.depth <= 0:
                self.in_page = False
                if self.current_page:
                    self.current_page['raw_html'] = ''.join(self.content_buffer)
                    self.pages.append(self.current_page)
                    self.current_page = None
                self.content_buffer = []

    def handle_data(self, data):
        self.content_buffer.append(data)
        if self.current_section and data.strip():
            self.current_section['content'] += data


def extract_pages_from_js(html_content):
    """
    Extract pages from Studio V2 JavaScript template literal functions.
    Studio V2 defines pages as: function pageXxx(){return `...`;}
    The content is in JS template literals, not static HTML.
    """
    pages = []

    # Pattern: function pageXxx(){return `...content...`;}
    # Match function names like pageHome, pageExtrait, etc.
    func_pattern = re.compile(
        r'function\s+page(\w+)\s*\(\s*\)\s*\{return\s*`(.*?)`;\s*\}',
        re.DOTALL
    )

    for match in func_pattern.finditer(html_content):
        func_name = match.group(1)  # Home, Extrait, Engrais, etc.
        raw_content = match.group(2)

        # Clean JS template expressions: ${NAV()}, ${FOOTER()}, ${img(...)}, ${e()}
        # Remove NAV() and FOOTER() calls
        clean = re.sub(r'\$\{NAV\(\)\}', '', raw_content)
        clean = re.sub(r'\$\{FOOTER\(\)\}', '', clean)

        # Replace ${img(IMGS.xxx,'alt text','class')} with actual <img> tags
        def replace_img(m):
            args = m.group(1)
            # Parse img arguments: IMGS.key, 'alt', 'class'
            parts = re.findall(r"IMGS\.(\w+)|'([^']*)'|\"([^\"]*)\"", args)
            src_key = parts[0][0] if parts else ''
            alt = parts[1][1] if len(parts) > 1 else ''
            # Map known IMGS keys to URLs
            img_urls = {
                'extrait': 'https://nosvers.com/wp-content/uploads/2026/02/Lombrithe-arrosoir-1-600x1067.png',
                'arrosoir': 'https://nosvers.com/wp-content/uploads/2026/02/Lombrithe-arrosoir-600x1067.png',
                'engrais1': 'https://nosvers.com/wp-content/uploads/2026/02/pomelli-image-600x1067.png',
                'engrais2': 'https://nosvers.com/wp-content/uploads/2026/02/Gemini_Generated_Image_edw3yxedw3yxedw3-600x438.png',
                'engrais3': 'https://nosvers.com/wp-content/uploads/2026/02/Capture-decran-du-2026-02-19-20-49-53-600x746.png',
                'logo': 'https://nosvers.com/wp-content/uploads/2026/02/cropped-Capture-decran-du-2026-02-16-20-59-09.png',
                'jardin1': 'https://images.unsplash.com/photo-1416879595882-3373a0480b5b?w=800',
                'jardin2': 'https://images.unsplash.com/photo-1523348837708-15d4a09cfac2?w=800',
                'jardin3': 'https://images.unsplash.com/photo-1559329007-40df8a9345d8?w=600',
                'jardin4': 'https://images.unsplash.com/photo-1466637574441-749b8f19452f?w=600',
                'jardin5': 'https://images.unsplash.com/photo-1585320806297-9794b3e4eeae?w=600',
                'ferme': 'https://images.unsplash.com/photo-1500382017468-9049fed747ef?w=900',
                'africa': 'https://images.unsplash.com/photo-1542744173-8e7e53415bb0?w=900',
            }
            src = img_urls.get(src_key, f'https://nosvers.com/wp-content/uploads/placeholder-{src_key}.jpg')
            return f'<img src="{src}" alt="{alt}" loading="lazy">'

        clean = re.sub(r'\$\{img\(([^)]+)\)\}', replace_img, clean)

        # Remove ${e()} (contenteditable attributes for editor mode)
        clean = re.sub(r'\s*\$\{e\(\)\}', '', clean)

        # Remove any remaining ${...} JS expressions
        clean = re.sub(r'\$\{[^}]+\}', '', clean)

        # Clean up editor-only attributes
        clean = re.sub(r'\s*contenteditable="true"', '', clean)
        clean = re.sub(r'\s*data-e="1"', '', clean)
        clean = re.sub(r'\s*spellcheck="false"', '', clean)
        clean = re.sub(r'\s*data-img="1"', '', clean)
        clean = re.sub(r'\s*onclick="[^"]*"', '', clean)

        page_name = func_name.lower()
        # Map function names to readable page names
        name_map = {
            'home': 'Accueil',
            'extrait': 'Extrait Vivant',
            'engrais': 'Engrais Vert',
            'atelier': 'Atelier Sol Vivant',
            'about': 'La Ferme',
            'contact': 'Contact',
        }
        display_name = name_map.get(page_name, func_name)

        pages.append({
            'name': display_name,
            'slug': page_name,
            'html': clean.strip()
        })

    return pages


def extract_pages_simple(html_content):
    """
    Extract pages from Studio V2 HTML.
    First tries JS template literal extraction (Studio V2 format),
    then falls back to static HTML patterns.
    """
    # Studio V2 format: pages defined as JS functions
    pages = extract_pages_from_js(html_content)
    if pages:
        return pages

    # Fallback patterns for static HTML
    pages = []

    # Pattern 1: <!-- PAGE: name -->
    comment_pages = re.findall(
        r'<!--\s*PAGE:\s*(.+?)\s*-->(.*?)(?=<!--\s*PAGE:|$)',
        html_content, re.DOTALL
    )
    if comment_pages:
        for name, content in comment_pages:
            pages.append({'name': name.strip(), 'slug': re.sub(r'[^a-z0-9-]', '-', name.strip().lower()).strip('-'), 'html': content.strip()})
        return pages

    # Pattern 2: data-page="name"
    data_pages = re.findall(
        r'<[^>]+data-page="([^"]+)"[^>]*>(.*?)</(?:div|section|main)>',
        html_content, re.DOTALL
    )
    if data_pages:
        for name, content in data_pages:
            pages.append({'name': name.strip(), 'slug': re.sub(r'[^a-z0-9-]', '-', name.strip().lower()).strip('-'), 'html': content.strip()})
        return pages

    # Pattern 3: sections with id
    sections = re.findall(
        r'<section[^>]+id="([^"]+)"[^>]*>(.*?)</section>',
        html_content, re.DOTALL
    )
    if sections:
        for name, content in sections:
            pages.append({'name': name.strip(), 'slug': re.sub(r'[^a-z0-9-]', '-', name.strip().lower()).strip('-'), 'html': content.strip()})
        return pages

    # Fallback: treat entire content as one page
    pages.append({'name': 'homepage', 'slug': 'homepage', 'html': html_content})
    return pages


def html_to_bricks_json(page_name, html_content):
    """Convert HTML content to Bricks Builder JSON element structure."""
    elements = []
    element_id = 1000

    # Extract sections
    section_pattern = re.compile(
        r'<(section|div|header|footer)[^>]*class="([^"]*)"[^>]*>(.*?)</\1>',
        re.DOTALL
    )

    for match in section_pattern.finditer(html_content):
        tag, classes, inner = match.groups()

        element = {
            'id': f'nosvers_{element_id}',
            'name': tag,
            'parent': 0,
            'children': [],
            'settings': {
                '_cssClasses': classes,
                '_background': {
                    'color': NOSVERS_STYLES['bg_warm']
                },
                '_typography': {
                    'font-family': NOSVERS_STYLES['font_body']
                }
            }
        }

        # Extract text content
        texts = re.findall(r'<(?:h[1-6]|p|span)[^>]*>(.*?)</(?:h[1-6]|p|span)>', inner, re.DOTALL)
        for i, text in enumerate(texts):
            clean_text = re.sub(r'<[^>]+>', '', text).strip()
            if clean_text:
                child_id = f'nosvers_{element_id}_{i}'
                child = {
                    'id': child_id,
                    'name': 'text-basic',
                    'parent': element['id'],
                    'settings': {
                        'text': clean_text
                    }
                }
                element['children'].append(child_id)
                elements.append(child)

        # Extract images
        images = re.findall(r'<img[^>]+src="([^"]+)"[^>]*(?:alt="([^"]*)")?', inner)
        for i, (src, alt) in enumerate(images):
            child_id = f'nosvers_{element_id}_img_{i}'
            child = {
                'id': child_id,
                'name': 'image',
                'parent': element['id'],
                'settings': {
                    'image': {'url': src},
                    'altText': alt or ''
                }
            }
            element['children'].append(child_id)
            elements.append(child)

        elements.insert(0, element)
        element_id += 1

    return elements


def generate_bricks_template(page_name, elements, timestamp):
    """Generate PHP template file for Bricks Builder."""
    elements_json = json.dumps(elements, indent=2, ensure_ascii=False)

    template = f'''<?php
/**
 * NosVers · {page_name}
 * Generado desde Studio V2 — {timestamp}
 * Para importar en Bricks Builder: Bricks > Templates > Import
 */

if (!defined("ABSPATH")) exit;

// Bricks Builder elements data
$nosvers_{page_name.lower().replace(" ", "_").replace("-", "_")}_elements = json_decode(\'{json.dumps(elements, ensure_ascii=False)}\', true);

/**
 * Registrar template en Bricks
 * Añadir en functions.php o via Code Snippets plugin
 */
function nosvers_register_{page_name.lower().replace(" ", "_").replace("-", "_")}_template() {{
    if (!function_exists("bricks_is_builder")) return;

    // El template se importa via Bricks UI o REST API
    // Este archivo sirve como referencia y backup
}}
add_action("init", "nosvers_register_{page_name.lower().replace(" ", "_").replace("-", "_")}_template");
'''
    return template


def generate_wp_block_content(page_name, html_content):
    """
    Alternative: generate WordPress block editor (Gutenberg) compatible content.
    Useful as fallback if Bricks isn't available.
    """
    # Clean and convert HTML to WP blocks
    blocks = []

    # Process headings
    for match in re.finditer(r'<h([1-6])[^>]*>(.*?)</h\1>', html_content, re.DOTALL):
        level, text = match.groups()
        clean = re.sub(r'<[^>]+>', '', text).strip()
        blocks.append(f'<!-- wp:heading {{"level":{level}}} -->\n<h{level}>{clean}</h{level}>\n<!-- /wp:heading -->')

    # Process paragraphs
    for match in re.finditer(r'<p[^>]*>(.*?)</p>', html_content, re.DOTALL):
        text = match.group(1).strip()
        if text:
            blocks.append(f'<!-- wp:paragraph -->\n<p>{text}</p>\n<!-- /wp:paragraph -->')

    # Process images
    for match in re.finditer(r'<img[^>]+src="([^"]+)"[^>]*>', html_content):
        src = match.group(1)
        blocks.append(f'<!-- wp:image -->\n<figure class="wp-block-image"><img src="{src}" alt=""/></figure>\n<!-- /wp:image -->')

    return '\n\n'.join(blocks)


def upload_to_wordpress(page_name, content):
    """Upload page as draft to WordPress."""
    if not HAS_REQUESTS:
        print(f"  ⚠️  requests no instalado — no se puede subir a WordPress")
        return None

    if not WP_USER or not WP_PASS:
        print(f"  ⚠️  Credenciales WordPress no configuradas")
        return None

    try:
        r = requests.post(
            f"{WP_URL}pages",
            auth=(WP_USER, WP_PASS),
            json={
                'title': f'NosVers · {page_name}',
                'content': content,
                'status': 'draft'
            },
            timeout=30
        )
        if r.status_code in (200, 201):
            url = r.json().get('link', '')
            print(f"  ✅ Subido como draft: {url}")
            return url
        else:
            print(f"  ❌ Error WordPress: HTTP {r.status_code}")
            return None
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description='NosVers Studio V2 → WordPress converter')
    parser.add_argument('input', help='Archivo HTML del Studio V2')
    parser.add_argument('--output-dir', '-o', default='./templates', help='Directorio de salida')
    parser.add_argument('--upload', action='store_true', help='Subir como draft a WordPress')
    parser.add_argument('--format', choices=['bricks', 'gutenberg', 'both'], default='both',
                        help='Formato de salida')

    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"❌ Archivo no encontrado: {args.input}")
        sys.exit(1)

    print(f"🌿 NosVers · Studio V2 → WordPress")
    print(f"   Input: {args.input}")
    print(f"   Output: {args.output_dir}")
    print(f"   Formato: {args.format}")
    print()

    with open(args.input, 'r', encoding='utf-8') as f:
        html_content = f.read()

    print(f"   Leído: {len(html_content):,} bytes")

    # Extract pages
    pages = extract_pages_simple(html_content)
    print(f"   Páginas encontradas: {len(pages)}")
    print()

    os.makedirs(args.output_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')

    for page in pages:
        name = page['name']
        html = page['html']
        safe_name = page.get('slug', re.sub(r'[^a-z0-9-]', '-', name.lower()).strip('-'))

        print(f"📄 Procesando: {name}")

        # Bricks Builder template
        if args.format in ('bricks', 'both'):
            elements = html_to_bricks_json(name, html)
            bricks_php = generate_bricks_template(name, elements, timestamp)
            bricks_path = os.path.join(args.output_dir, f'{safe_name}.bricks.php')
            with open(bricks_path, 'w', encoding='utf-8') as f:
                f.write(bricks_php)
            print(f"   ✅ Bricks: {bricks_path} ({len(elements)} elementos)")

            # Also save raw JSON for Bricks import
            json_path = os.path.join(args.output_dir, f'{safe_name}.bricks.json')
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(elements, f, indent=2, ensure_ascii=False)

        # Gutenberg blocks
        if args.format in ('gutenberg', 'both'):
            blocks = generate_wp_block_content(name, html)
            blocks_path = os.path.join(args.output_dir, f'{safe_name}.gutenberg.html')
            with open(blocks_path, 'w', encoding='utf-8') as f:
                f.write(blocks)
            print(f"   ✅ Gutenberg: {blocks_path}")

            # Upload to WordPress
            if args.upload:
                upload_to_wordpress(name, blocks)

    print()
    print(f"✅ Completado: {len(pages)} páginas procesadas en {args.output_dir}/")
    print()
    print("Próximos pasos:")
    print("  1. Revisa los templates generados")
    print("  2. Para Bricks: Importa los .bricks.json desde Bricks > Templates")
    print("  3. Para Gutenberg: usa --upload para subir como draft a WordPress")
    print(f"  4. Ejemplo: python3 {sys.argv[0]} {args.input} --upload --format gutenberg")


if __name__ == '__main__':
    main()
