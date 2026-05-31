# Auditoría SEO completa — nosvers.com

**Fecha:** 2026-05-31 · **Objetivo:** Top 3 Google France
**Tipo de negocio:** E-commerce local (WooCommerce) + ferme lombricole · Neuvic, Dordogne (24190) · FR
**Método:** Crawl real server-side (VPS) + WordPress/WooCommerce REST API.
*(Ahrefs y GSC MCP no disponibles en este plan — "Insufficient plan"; los datos de keywords usados son los ya confirmados antes en GSC.)*

---

## 🎯 SEO Health Score: **72 / 100**

| Categoría | Peso | Nota | Comentario |
|---|---|---|---|
| Técnico | 22% | 78 | HTTPS, HSTS, CSP, canonical, sitemaps OK. Problemas de duplicados/redirecciones. |
| Contenido | 23% | 70 | Buenos artículos largos (2.000+ palabras), pero varias páginas thin. |
| On-Page | 20% | 65 | Títulos y metas duplicados; metas demasiado largas. |
| Schema | 10% | 60 | Excelente LocalBusiness/Org, pero **falta Product/Offer en productos**. |
| Rendimiento | 10% | 80 | LiteSpeed cache, lazy-load OK. Sin WebP. |
| AI / GEO | 10% | 78 | Schema rico + contenido citable. Sin llms.txt. |
| Imágenes | 5% | 75 | Casi todas con alt; sin formato WebP. |

**El sitio está técnicamente bien montado** (AIOSEO, LiteSpeed, schema LocalBusiness completo). Lo que separa de un top 3 son **fugas concretas**, no la base.

---

## 🔴 TOP 5 CRÍTICO (corregir ya)

### 1. El producto estrella "Extrait Vivant" da **404** a los visitantes
`/produit/extrait-vivant-de-lombric/` → **HTTP 404 + noindex** (está en `private`).
Es el destino del CTA del artículo nuevo y del enfoque "lombrithé". **Hoy no se puede comprar ni indexar.**
→ Publicar el producto (`private` → `publish`).

### 2. Productos WooCommerce **sin schema Product/Offer**
Las fichas de producto solo tienen `Organization/WebPage/Breadcrumb`. **No hay `Product`, `Offer` ni `price`.**
Sin esto Google no muestra precio, disponibilidad ni rich snippet de producto — clave en e-commerce.
→ Activar schema Product en AIOSEO/WooCommerce para los 6 productos.

### 3. Títulos y meta descriptions **duplicados**
- `/lombrithe/` → 301 a `/club-du-sol-vivant/` (mismo title "Club du Sol Vivant").
- `/guides-formations/` y `/pack-engrais-vert/` → 301 a `/boutique/` (title idéntico a Boutique).
Hay **redirecciones que no deberían existir** (una URL "lombrithe" mandando a "club") y títulos clonados.
→ Revisar redirects; cada URL viva debe tener title único.

### 4. Meta descriptions **demasiado largas** (se truncan en Google)
`/la-ferme/` 341c · `/club-du-sol-vivant/` 332c · `/guide-gratuit/` 360c · `/a-venir/` 357c · posts 300–338c.
Google corta ~155–160 caracteres → se pierde el gancho.
→ Reescribir a 150–160 caracteres con keyword + beneficio.

### 5. Páginas **"À venir" thin/duplicadas indexables**
9 posts `a-venir-*` (coming soon) + página `/a-venir/`. Contenido fino y repetitivo que diluye autoridad.
→ `noindex` a todos los "à venir" hasta que tengan contenido real.

---

## 🟢 TOP 5 QUICK WINS

1. **Publicar el artículo "LombriThé vs Extrait Vivant"** (post 1279, draft) — captura keyword "lombrithé" con volumen real en GSC.
2. **Title de home** a ≤60c con keyword principal delante: hoy 54c, correcto, pero optimizable hacia "Lombricompost & vers vivants · Dordogne | NosVers".
3. **Convertir imágenes a WebP** (LiteSpeed lo hace solo activando la opción) — 0 WebP hoy.
4. **Añadir `llms.txt`** en la raíz para citabilidad en IA (ChatGPT/Perplexity/AI Overviews).
5. **Interlinking**: enlazar los 3 artículos de vers (Dendrobaena, Eisenia) entre sí y hacia las fichas de producto correspondientes.

---

## Detalle por categoría

### Técnico
- ✅ HTTP/2, LiteSpeed, HSTS (preload), CSP `upgrade-insecure-requests`, X-Frame SAMEORIGIN, X-Content-Type nosniff, Permissions-Policy.
- ✅ `lang="fr-FR"`, canonical, viewport, robots.txt correcto (bloquea wp-admin, permite uploads).
- ✅ Sitemaps AIOSEO: post(21) + product(5) + page(20) + category(2) + product_cat(5).
- ⚠️ Redirecciones 301 confusas (lombrithe→club, guides/pack→boutique).
- ⚠️ `sitemap.rss` declarado en robots en vez del XML index (menor).

### Contenido
- ✅ Artículos sólidos: Eisenia hortensis (2.405 palabras), Vers de pêche (2.066), con `BlogPosting`+`Person` (E-E-A-T).
- ⚠️ Thin: `/notre-ferme/` (101 palabras), `/contact/` (226), varios "à venir".
- ⚠️ Posible canibalización: `/notre-ferme/` vs `/la-ferme/` vs `/a-propos/` — tres páginas "sobre la ferme".

### On-Page
- ✅ 1 H1 por página en todas las URLs revisadas; jerarquía H2/H3 correcta en home.
- ❌ Títulos duplicados (ver crítico #3); metas largas (#4).

### Schema
- ✅ Excelente en home: `LocalBusiness, Organization, PostalAddress, ContactPoint, City, Country, WebSite, WebPage, BreadcrumbList`.
- ❌ Falta `Product`/`Offer`/`AggregateRating` en fichas de producto (crítico #2).

### Rendimiento
- ✅ LiteSpeed cache, 8/9 imágenes lazy-load, solo 1 CSS, 6 JS.
- ⚠️ 0 imágenes en WebP. 13 bloques `<style>` inline (CSS crítico, aceptable).

### AI / GEO
- ✅ Schema rico + contenido en bloques citables + autor (Person).
- ⚠️ Sin `llms.txt`. Sin FAQ schema (oportunidad para AI Overviews en consultas "comment faire lombrithé").

### Imágenes
- ✅ Solo 1 img sin alt en home; mediateca con alt descriptivos en FR.
- ⚠️ Sin WebP/AVIF.

---

*Datos recogidos server-side el 2026-05-31. Ver ACTION-PLAN.md para el plan priorizado.*
