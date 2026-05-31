# Auditoría SEO — nosvers.com

**Fecha:** 2026-05-31
**Herramienta:** skill `claude-seo` v2.0.0 (AgriciDaniel) instalado en `.claude/skills/`
**Método:** crawl real del sitio vía VPS (curl server-side, HTML en vivo) + sitemaps Rank Math. Ahrefs API en plan *Starter* (sin Site Explorer); GSC sin proyecto configurado → métricas de tráfico pendientes (ver "Limitaciones").
**Idioma del sitio:** `fr-FR` · **Stack:** WordPress + WooCommerce + tema custom `nosvers` + LiteSpeed/nginx

---

## 🎯 SEO Health Score: **48 / 100**

| Categoría | Peso | Nota | Comentario |
|-----------|------|------|------------|
| Technical SEO | 22% | 60 | HTTPS y sitemap OK; **www sin redirección** (duplicado), sin cabeceras de seguridad |
| Content Quality (E-E-A-T) | 23% | 55 | Contenido propio y nicho fuerte; falta autoría/fechas y profundidad en fichas |
| On-Page SEO | 20% | 30 | **Meta descriptions vacías en TODO el sitio** + **home sin H1** |
| Schema / Datos estructurados | 10% | 5 | **0 JSON-LD** en todo el sitio (ni Organization, ni Product, ni LocalBusiness) |
| Performance (CWV) | 10% | 65 | LiteSpeed + gzip; faltan datos de campo (sin analytics) |
| AI Search Readiness (GEO) | 10% | 25 | Sin `llms.txt`, sin schema → baja citabilidad en IA |
| Images | 5% | 40 | Muchas imágenes sin `alt` (home: 9/14) |

> Puntuación orientativa. El mayor lastre son cosas **baratas de arreglar** (on-page + schema): hay margen para subir a ~75 en una sola semana de trabajo.

---

## 🔴 CRÍTICO (arreglar ya — bloquea visibilidad)

### C1 · Meta descriptions vacías en todas las páginas
Home, boutique, club, à-propos, contact y **las 5 fichas de producto** → `<meta name="description">` ausente.
- **Impacto:** Google inventa el snippet → menos CTR. Pierdes el control del mensaje comercial en la SERP.
- **Causa probable:** Rank Math/Yoast no detectado en el HTML servido (el CLAUDE.md dice Rank Math, pero no emite meta). Revisar si está activo y configurado.
- **Acción:** escribir meta description (140-155 car., en francés, con CTA) para cada URL. Empezar por home + 5 productos.
- **Falsable:** `curl -s URL | grep 'name="description"'` devuelve contenido no vacío.

### C2 · Cero datos estructurados (JSON-LD) en todo el sitio
No hay **Organization**, **LocalBusiness**, **Product/Offer**, **BreadcrumbList** ni **WebSite/SearchAction**.
- **Impacto:** sin rich results (precio, stock, estrellas), sin knowledge panel, sin pan de migas en SERP. Para e-commerce es pérdida directa de clics.
- **Acción mínima viable:**
  1. `Organization` + `WebSite` en home (logo, sameAs redes, nombre).
  2. `Product` + `Offer` (precio, disponibilidad, moneda EUR) en las 5 fichas.
  3. `LocalBusiness` (Neuvic, Dordogne 24190) en contact/à-propos.
  4. `BreadcrumbList` en boutique y fichas.
- **Herramienta:** `scripts/schema_generate.py` del skill + plantillas en `.claude/skills/seo/schema/`.
- **Falsable:** validar en Rich Results Test sin errores.

### C3 · Home sin etiqueta `<h1>`
La home (y club, à-propos, contact) no tienen H1. Solo H2.
- **Impacto:** Google pierde la señal jerárquica principal de la página más importante.
- **Acción:** añadir un único H1 descriptivo con keyword. Ej. home: `Lombriculture & sol vivant en Dordogne — NosVers`.
- **Falsable:** exactamente 1 `<h1>` por página.

---

## 🟠 ALTO (1 semana — impacta ranking)

### A1 · www no redirige → contenido duplicado
`https://www.nosvers.com/` responde **200** (debería ser 301 → no-www).
- **Acción:** redirección 301 `www → nosvers.com` en nginx/LiteSpeed. Confirmar canonical coherente.
- **Falsable:** `curl -I https://www.nosvers.com` → `301` a `https://nosvers.com/`.

### A2 · Sin analítica (GA4/GTM ausentes)
No se detecta `gtag`, GTM ni GA4 en el HTML.
- **Impacto:** ceguera total. No se puede medir conversión del Club ni de productos, ni priorizar SEO por datos.
- **Acción:** instalar GA4 + Google Search Console (property) + enlazar. Esto además desbloquea el módulo `seo-google` del skill y las métricas reales en futuras auditorías.

### A3 · Fichas de producto sin schema Product/Offer ni precio en meta
Ver C2. Específico e-commerce: sin `product:price:amount`, sin `Offer.availability`.
- **Acción:** activar salida de schema de WooCommerce (Rank Math WooCommerce module o snippet) con precio, stock, SKU, moneda.

### A4 · Imágenes sin texto alternativo
Home 9/14 sin `alt`; productos 2-4 sin `alt` cada uno.
- **Impacto:** accesibilidad + SEO de imágenes (Google Images es tráfico real en jardinería) + GEO.
- **Acción:** `alt` descriptivo en francés con keyword natural. Priorizar imágenes de producto y hero.

---

## 🟡 MEDIO (1 mes — optimización)

- **M1 · GEO / IA:** crear `/llms.txt` (404 actual) describiendo NosVers, productos y filosofía sol vivant para mejorar citabilidad en ChatGPT/Perplexity. Ver `skill seo-geo`.
- **M2 · E-E-A-T:** añadir autoría visible (Angel/África), fechas de publicación y bio en blog y à-propos. Enlazar SIRET/MSA como señal de confianza.
- **M3 · Cache-Control `no-cache` en HTML:** revisar config LiteSpeed; aunque hay `x-litespeed-cache: hit`, la cabecera dice `no-cache, must-revalidate, max-age=0`. Afinar para edge caching real.
- **M4 · Cabeceras de seguridad:** añadir `X-Content-Type-Options: nosniff`, `X-Frame-Options`/`CSP`. Señal menor de calidad.
- **M5 · Profundidad de contenido en fichas:** 356-512 palabras/ficha. Para competir en SERP de jardinería conviene 600-900 con sección "comment utiliser", beneficios y FAQ por producto.
- **M6 · Datos de campo CWV:** una vez haya GSC/CrUX, medir INP/LCP/CLS reales (móvil).

---

## 🟢 BAJO (backlog)

- B1 · Breadcrumbs visibles en boutique/fichas (UX + BreadcrumbList).
- B2 · Open Graph completo (og:description, og:type=product, twitter:card) — og:image ya existe en productos.
- B3 · Enlazado interno blog → fichas de producto (los 7 artículos publicados deberían apuntar a productos relacionados).
- B4 · Revisar `author-sitemap.xml` (evitar indexar perfiles de autor vacíos).

---

## ✅ Lo que ya está bien

- HTTPS con **301** desde HTTP y **HSTS** activo.
- `robots.txt` correcto, con `Disallow: /wp-admin/` y `Allow: admin-ajax.php`, y sitemap declarado.
- **Sitemap index Rank Math** funcionando (product, page, post, product_cat, author).
- Titles únicos, con marca (`· NosVers`) y longitud razonable (33-61 car.).
- `og:image` presente en las 5 fichas.
- LiteSpeed + gzip + nginx (buena base de rendimiento).
- Contenido **propio y de nicho** (sol vivant, LombriThé, Dr. Elaine Ingham) — base de autoridad temática real.

---

## 🚀 Plan de acción priorizado (encadenado con AGT-04 · El Investigador)

| # | Acción | Prioridad | Quién | Desbloquea |
|---|--------|-----------|-------|------------|
| 1 | Meta descriptions home + 5 productos (FR) | 🔴 | AGT-04 | CTR inmediato |
| 2 | H1 único en home/club/à-propos/contact | 🔴 | AGT-04 | jerarquía |
| 3 | JSON-LD: Organization+WebSite (home), Product+Offer (5 fichas), LocalBusiness (contact) | 🔴 | Infra + AGT-04 | rich results |
| 4 | 301 www → no-www | 🟠 | Infra (VPS) | dedup |
| 5 | GA4 + GSC property | 🟠 | Infra | medición + módulo seo-google |
| 6 | `alt` en imágenes (home + productos) | 🟠 | AGT-04/El Ojo | img SEO + a11y |
| 7 | `/llms.txt` | 🟡 | AGT-04 | GEO/IA |
| 8 | Ampliar contenido fichas a 600-900 pal. + FAQ | 🟡 | AGT-04 | ranking productos |

**Quick wins (1 día):** #1, #2, #7 — solo edición de templates/contenido, sin riesgo.
**Mayor ROI estructural:** #3 (schema) + #5 (medición).

### Siguiente paso recomendado con el skill
```
/seo schema https://nosvers.com/produit/extrait-vivant-de-lombric/   # genera Product+Offer
/seo page  https://nosvers.com/                                       # análisis profundo home
/seo local https://nosvers.com/contact/                              # LocalBusiness Dordogne
/seo geo   https://nosvers.com/                                       # plan llms.txt + citabilidad
```
> Nota: los slash commands `/seo …` quedan disponibles para Angel en la **próxima** sesión de Claude Code (la skill se acaba de instalar). Esta auditoría se ejecutó manualmente con los scripts del skill + crawl vía VPS.

---

## Limitaciones de esta pasada

- **Tráfico/keywords reales pendientes:** Ahrefs conectado en plan *Starter* (Site Explorer API no disponible → "Insufficient plan") y GSC sin proyecto en Ahrefs. Acción #5 (GSC property) lo resuelve y permitirá rankings/impresiones/CTR reales.
- **Core Web Vitals de campo:** sin CrUX/GA4 todavía. Estimación basada en stack (LiteSpeed+gzip), no en datos de usuarios.
- El contenedor de Claude Code no alcanza nosvers.com directamente (política de red); el crawl se hizo server-side desde el VPS — datos 100% reales del HTML en producción.

---

*Auditoría generada por el Director Ejecutivo (Claude Code) · skill claude-seo · para Angel, CEO de NosVers.*
