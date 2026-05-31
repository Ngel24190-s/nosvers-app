# Auditoría SEO — nosvers.com

**Fecha:** 2026-05-31
**Herramienta:** skill `claude-seo` v2.0.0 (AgriciDaniel) instalado en `.claude/skills/`
**Método:** crawl real del sitio vía VPS (curl server-side, HTML en producción) + sitemap. Ahrefs API en plan *Starter* (sin Site Explorer → "Insufficient plan"); GSC sin proyecto Ahrefs → métricas de tráfico pendientes (ver "Limitaciones").
**Idioma:** `fr-FR` · **Stack:** WordPress + WooCommerce (instalado, sin tienda viva) + tema custom `nosvers-v2` + LiteSpeed/Hostinger
**Páginas indexables (sitemap):** 6 — Accueil, Boutique, Club Sol Vivant, À propos, Contact, Blog

---

## 🎯 SEO Health Score: **68 / 100**

| Categoría | Peso | Nota | Comentario |
|-----------|------|------|------------|
| Technical SEO | 22% | 78 | HTTPS+301, HSTS, cabeceras seguridad completas, LiteSpeed+brotli. Resta: sitemap incompleto, www no resuelve |
| Content Quality (E-E-A-T) | 23% | 70 | Contenido propio y de nicho, páginas con 600-1.240 palabras, autoría real (Angel/África). Falta fechas/bio estructuradas |
| On-Page SEO | 20% | 55 | H1 en todas las páginas ✅. **Home sin meta description + title genérico**; boutique meta demasiado larga; marca duplicada en titles |
| Schema / Datos estructurados | 10% | 90 | **Excelente:** Organization, LocalBusiness/Farm, WebSite, BreadcrumbList, ContactPoint, PostalAddress sitewide |
| Performance (CWV) | 10% | 65 | LiteSpeed+brotli+UCSS; faltan datos de campo (GSC/CrUX no enlazado) |
| AI Search Readiness (GEO) | 10% | 70 | `llms.txt` presente ✅ + schema sólido. Mejorable: profundidad citable por producto |
| Images | 5% | 65 | Mayoría con alt; home 1/9 sin alt |

> El sitio tiene una **base técnica fuerte** (schema + seguridad + rendimiento). Los problemas reales son **on-page concretos y baratos** + estrategia de sitemap/tienda. Subir a ~80 es cuestión de unos pocos arreglos.

---

## 🔴 ALTA PRIORIDAD (impacto directo en CTR/indexación)

### 1 · Home sin meta description y con title genérico
- `<title>` = **"Accueil - NosVers"** (17 car.): sin keyword, desperdicia la página más importante.
- `<meta name="description">` = **ausente** en la home (sí existe en club/à-propos/contact).
- **Acción:**
  - Title → algo como `NosVers · Lombricompost & sol vivant en Dordogne` (50-60 car., con keyword + localidad).
  - Meta description FR de 150-155 car. con propuesta de valor + CTA.
- **Falsable:** `curl -s https://nosvers.com/ | grep -i 'name="description"'` devuelve contenido; title contiene keyword.

### 2 · Sitemap incompleto + Rank Math redirigido (302)
- El sitemap activo es un **RSS hecho a mano** (`/sitemap.rss`) con **solo 6 URLs**. No incluye los **7 artículos de blog ya publicados** (IDs 458, 72, 77, 78, 79, 80, 81) ni futuras fichas.
- `sitemap_index.xml` de Rank Math responde **302** (desactivado o mal configurado).
- **Impacto:** los artículos del blog pueden tardar más en indexarse / no descubrirse.
- **Acción:** o bien activar correctamente el sitemap de Rank Math (incluye posts y CPTs), o ampliar el RSS para incluir todos los posts. Reenviar a GSC.
- **Falsable:** el sitemap lista las URLs de los 7 posts.

### 3 · Verificar enlazado y rastreo del blog
- `/blog/` no expone enlaces a los posts en el HTML servido (posible render JS o listado vacío). Si los 7 artículos no son alcanzables por enlaces internos + no están en sitemap → **huérfanos**.
- **Acción:** confirmar que `/blog/` lista y enlaza cada artículo en HTML; añadir enlaces internos desde home/boutique a artículos clave.
- **Falsable:** `curl /blog/ | grep href` muestra las URLs de los artículos.

---

## 🟠 MEDIA PRIORIDAD (1-2 semanas)

### 4 · Meta description de boutique demasiado larga
333 caracteres → Google la truncará (~155-160). **Acción:** reescribir a ~155 car. con keywords "lombricompost, LombriThé, engrais vert, Dordogne".

### 5 · Marca duplicada en los `<title>`
Ej.: `À propos · NosVers - NosVers`, `Club Sol Vivant · L'abonnement NosVers - NosVers`. La palabra "NosVers" aparece dos veces. **Acción:** quitar la marca del título editorial o el sufijo automático, dejar una sola.

### 6 · Estrategia de tienda / e-commerce SEO
WooCommerce está instalado pero **no hay fichas de producto vivas** (`/produit/...` → 404) ni enlaces de compra en boutique; es una página de presentación. Decisión estratégica para Angel:
- **Si se va a vender online:** crear fichas de producto reales (Extrait Vivant 45€, Service Frais 25€, Pack Engrais Vert 9,90€, Atelier 85€) con `Product`+`Offer` schema (precio, stock, EUR), e indexarlas. Esto abre tráfico transaccional + rich results de precio.
- **Si la venta es por contacto/Club:** dejar boutique como está, pero entonces NO se necesita WooCommerce indexable (evitar URLs /produit vacías).

### 7 · www no resuelve
`https://www.nosvers.com/` → no responde (sin DNS/cert para www). No es duplicado (bien), pero si alguien teclea www, falla. **Acción opcional:** añadir registro www + redirección 301 a no-www, o dejarlo documentado como decisión.

---

## 🟡 BAJA PRIORIDAD (backlog / optimización)

- **8 · E-E-A-T:** añadir fechas de publicación visibles y bio de autor (Angel/África) en blog y à-propos; enlazar SIRET/MSA como señal de confianza. Considerar `Article` + `author` schema en los posts.
- **9 · Alt en imágenes:** completar el `alt` que falta (home 1/9; revisar resto). Texto FR descriptivo con keyword natural.
- **10 · Profundidad citable (GEO):** enriquecer `llms.txt` (ya existe) con productos, precios y filosofía sol vivant para mejorar citabilidad en ChatGPT/Perplexity. Añadir secciones FAQ en páginas clave (beneficio AI/LLM).
- **11 · Open Graph completo:** verificar `og:description` y `og:type` por plantilla (og:image y og:title ya presentes).

---

## ✅ Lo que ya está MUY bien (no tocar)

- **Datos estructurados sitewide:** `Organization`, `LocalBusiness`/`Farm` con `PostalAddress` (Neuvic, 24190), `ContactPoint`, `City`, `Country`, `WebSite`, `WebPage`, `BreadcrumbList`, `ImageObject`. Base de **local SEO y rich results excelente**.
- **H1 único** en todas las páginas (home: "Un sol vivant ne se fabrique pas. Il se retrouve.").
- **Meta descriptions correctas** en club (160), à-propos (159), contact (160).
- **`llms.txt` presente** (HTTP 200) — adelantado en GEO/IA.
- **Seguridad:** HSTS (preload), `X-Frame-Options`, `X-Content-Type-Options: nosniff`, CSP `upgrade-insecure-requests`, Referrer-Policy, Permissions-Policy.
- **HTTP → HTTPS 301** correcto. HTTP/2 + HTTP/3 (alt-svc).
- **Analítica activa:** GA4 / Google Tag Manager detectados.
- **Rendimiento:** LiteSpeed + Brotli + UCSS + minificación CSS/JS.
- `robots.txt` correcto (bloquea wp-admin, includes, búsqueda; permite uploads).
- Contenido sustancial: club 1.241 pal., à-propos 1.056, contact 597. Titles descriptivos en páginas internas.

---

## 🚀 Plan de acción priorizado (encadenado con AGT-04 · El Investigador)

| # | Acción | Prioridad | Quién | Esfuerzo |
|---|--------|-----------|-------|----------|
| 1 | Title + meta description de la **home** (FR, con keyword+localidad) | 🔴 | AGT-04 | 15 min |
| 2 | Sitemap completo (Rank Math o ampliar RSS) con los 7 posts → reenviar a GSC | 🔴 | Infra | 30 min |
| 3 | Verificar/arreglar enlazado del blog (posts no huérfanos) | 🔴 | Infra + AGT-04 | 1 h |
| 4 | Acortar meta description de boutique a ~155 | 🟠 | AGT-04 | 10 min |
| 5 | Quitar marca duplicada en titles | 🟠 | Infra | 20 min |
| 6 | **Decisión Angel:** ¿tienda online indexable o solo presentación? | 🟠 | Angel | decisión |
| 7 | alt faltantes + llms.txt enriquecido + FAQ | 🟡 | AGT-04/El Ojo | 2 h |

**Quick wins (mismo día, sin riesgo):** #1, #4, #5.
**Mayor ROI estructural:** #2+#3 (que el blog se indexe) y la decisión #6.

### Siguiente paso con el skill (próxima sesión de Claude Code)
```
/seo page    https://nosvers.com/                 # afinar title+meta home
/seo sitemap https://nosvers.com/                 # validar/generar sitemap completo
/seo content https://nosvers.com/club-sol-vivant/ # E-E-A-T del Club
/seo geo     https://nosvers.com/                 # enriquecer llms.txt + citabilidad
/seo local   https://nosvers.com/contact/         # verificar LocalBusiness Dordogne
```
> Los slash commands `/seo …` quedan disponibles en la **próxima** sesión (la skill se instaló en esta). Esta auditoría se ejecutó manualmente con los scripts del skill + crawl server-side vía VPS.

---

## ⚠️ Nota de proceso

La primera versión de este informe (commit anterior) contenía hallazgos **incorrectos**
(afirmaba "0 schema", "home sin H1", "sin meta en todo el sitio", "sin analítica") porque
se redactó antes de recibir los datos del crawl. **Esta versión los corrige con el HTML real
en producción.** El sitio está, de hecho, técnicamente bien construido.

## Limitaciones de esta pasada

- **Tráfico/keywords reales pendientes:** Ahrefs en plan *Starter* (Site Explorer no disponible) y GSC sin proyecto en Ahrefs. Configurar property de GSC + plan Ahrefs con Site Explorer permitirá rankings/impresiones/CTR reales.
- **CWV de campo:** sin CrUX/GA4-API enlazado a esta auditoría todavía.
- El contenedor de Claude Code no alcanza nosvers.com (política de red del entorno); el crawl se hizo server-side desde el VPS → datos 100% reales del HTML en producción.

---

*Auditoría del Director Ejecutivo (Claude Code) · skill claude-seo · para Angel, CEO de NosVers.*
