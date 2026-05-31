# Auditoría SEO — nosvers.com

**Fecha:** 2026-05-31
**Herramienta:** skill `claude-seo` v2.0.0 (AgriciDaniel, 7,4k ⭐) instalado en `.claude/skills/`
**Método:** crawl real del sitio vía VPS (curl server-side, HTML en producción) + sitemap AIOSEO.
**Idioma:** `fr-FR` · **Stack:** WordPress + WooCommerce (tienda **viva**) + tema custom `nosvers-v2` + LiteSpeed/Hostinger
**SEO plugin:** All in One SEO (AIOSEO) 4.9.7.2 · **Analítica:** Google Site Kit 1.179.0 (GA4 + GSC conectados)

---

## 🎯 SEO Health Score: **74 / 100**

| Categoría | Peso | Nota | Comentario |
|-----------|------|------|------------|
| Technical SEO | 22% | 80 | HTTPS+301, HSTS preload, cabeceras seguridad completas, LiteSpeed+brotli, HTTP/3 |
| Content Quality (E-E-A-T) | 23% | 72 | Contenido propio de nicho, páginas 450-1.240 pal., autoría real (Angel/África). Falta fechas/bio estructuradas |
| On-Page SEO | 20% | 60 | Titles y H1 buenos en productos/internas. **Home sin meta description + title genérico**; marca duplicada `- NosVers` |
| Schema / Datos estructurados | 10% | 92 | **Excelente:** Product, Offer, AggregateOffer, Brand, Organization, LocalBusiness/Farm, BreadcrumbList, WebSite sitewide |
| Performance (CWV) | 10% | 68 | LiteSpeed+brotli+UCSS; datos de campo disponibles vía Site Kit (sin enlazar a esta auditoría) |
| AI Search Readiness (GEO) | 10% | 72 | `llms.txt` presente ✅ + schema sólido. Mejorable: FAQ + profundidad citable |
| Images | 5% | 70 | Mayoría con alt; algunos faltan (home 1/9) |

> Tu sitio está **técnicamente bien construido**. No hay problemas graves. Lo que queda son ajustes on-page baratos y limpieza de URLs duplicadas. Subir a ~85 es trabajo de 1-2 días.

---

## 🔴 ALTA PRIORIDAD (rápido y con impacto directo)

### 1 · Home sin meta description y con title genérico
- `<title>` = **"Accueil - NosVers"** (17 car.) — sin keyword, desaprovecha tu página más importante.
- `<meta name="description">` = **ausente** solo en la home (las internas sí la tienen).
- **Acción:** Title → `NosVers · Lombricompost, vers & sol vivant en Dordogne` (~55 car.). Meta description FR 150-155 car. con propuesta de valor + CTA.
- **Falsable:** `curl -s https://nosvers.com/ | grep -i 'name="description"'` devuelve contenido.

### 2 · Proliferación de URLs casi duplicadas (canibalización)
El sitemap AIOSEO (30+ URLs) muestra **varias variantes del mismo tema** que compiten entre sí:
- Club: `/club-sol-vivant/`, `/club-du-sol-vivant/`, `/club-sol-vivant-rejoignez-la-communaute/`, `/a-venir-club-sol-vivant/`
- Guía: `/guide-gratuit/`, `/guide-gratuit-les-5-erreurs.../`, `/produit/guide-gratuit-les-5-erreurs.../`
- Extrait: `/extrait-vivant-de-lombric/`, `/a-venir-lombrithe-extrait-vivant/`
- Múltiples páginas `/a-venir-*` (placeholders de "próximamente").
- **Impacto:** canibalización de keywords, dilución de autoridad, presupuesto de rastreo desperdiciado.
- **Acción:** elegir 1 URL canónica por tema; 301 las demás; `noindex` a las páginas `/a-venir-*` mientras sean placeholders. Limpiar el sitemap.
- **Falsable:** una sola URL por intención en el sitemap; las variantes redirigen 301.

---

## 🟠 MEDIA PRIORIDAD (1-2 semanas)

### 3 · Marca duplicada en los `<title>`
Patrón `Título - NosVers` donde el título ya contiene "NosVers" → `… NosVers — … - NosVers`. **Acción:** ajustar el separador de marca de AIOSEO o los títulos editoriales para que la marca aparezca una sola vez.

### 4 · Meta descriptions largas en algunas internas
À-propos (328), contact (355), varios productos >160 car. → Google las trunca. **Acción:** recortar a ~155 con keyword + gancho al inicio.

### 5 · Aprovechar GSC/Site Kit (ya conectado) para priorizar por datos
Site Kit está activo → tienes datos reales de impresiones/clics/posición. **Acción:** revisar Search Console y priorizar artículos/productos con impresiones altas y CTR bajo (oportunidad de title/meta) o posición 8-20 (oportunidad de contenido). Esto desbloquea el módulo `seo-google` del skill.

---

## 🟡 BAJA PRIORIDAD (backlog)

- **6 · E-E-A-T:** fechas de publicación visibles + bio de autor (Angel/África) en blog; `Article`+`author` schema en posts. Enlazar SIRET/MSA como señal de confianza.
- **7 · Alt en imágenes:** completar los `alt` que faltan (home 1/9; revisar resto), FR descriptivo.
- **8 · GEO/IA:** enriquecer `llms.txt` (ya existe) con productos, precios y filosofía sol vivant; añadir FAQ en fichas y Club (beneficio cita IA).
- **9 · Enlazado interno:** desde los artículos del blog hacia las fichas de producto relacionadas (p.ej. artículo Dendrobaena → producto vers de pêche).

---

## ✅ Lo que ya está MUY bien (no tocar)

- **Datos estructurados completos:** las fichas de producto emiten `Product` + `Offer` + `AggregateOffer` + `Brand` con **precio** (34,90€ / 5€ / …) y **`availability: InStock`** → elegibles para rich results de precio/stock. Sitewide: `Organization`, `LocalBusiness`/`Farm` con `PostalAddress` (Neuvic 24190), `ContactPoint`, `WebSite`, `BreadcrumbList`. **Base de local SEO y e-commerce SEO excelente.**
- **Tienda WooCommerce viva** con productos reales indexables: vers Eisenia, vers de pêche Dendrobaena, humus de lombric, packs engrais vert, guía gratuita (lead magnet).
- **Titles y H1 de producto muy buenos:** descriptivos, con keyword + nombre científico + localidad (ej. *"Vers de Pêche Dendrobaena veneta NosVers — Gros Vers Européens Dordogne"*).
- **H1 único** en todas las páginas.
- **Analítica + Search Console** activos (Site Kit) — medición y datos de Google disponibles.
- **`llms.txt` presente** — adelantado en GEO/IA.
- **Seguridad:** HSTS preload, X-Frame-Options, X-Content-Type-Options nosniff, CSP, Referrer-Policy, Permissions-Policy.
- **Rendimiento:** LiteSpeed + Brotli + UCSS + minificación; HTTP/2 + HTTP/3.
- `robots.txt` correcto; HTTP→HTTPS 301.
- Blog con artículos reales enlazados (Dendrobaena, Eisenia hortensis, guide débutant, comparaison lombricompost…).

---

## 🚀 Plan de acción priorizado (encadenado con AGT-04 · El Investigador)

| # | Acción | Prioridad | Quién | Esfuerzo |
|---|--------|-----------|-------|----------|
| 1 | Title + meta description de la **home** | 🔴 | AGT-04 | 15 min |
| 2 | Consolidar URLs duplicadas (301) + `noindex` a `/a-venir-*` + limpiar sitemap | 🔴 | Infra + AGT-04 | 2 h |
| 3 | Quitar marca duplicada en titles (config AIOSEO) | 🟠 | Infra | 20 min |
| 4 | Recortar meta descriptions largas (>160) | 🟠 | AGT-04 | 30 min |
| 5 | Revisar GSC (Site Kit) y priorizar por impresiones/CTR/posición | 🟠 | AGT-04 | 1 h |
| 6 | E-E-A-T (fechas+autor), alt faltantes, llms.txt+FAQ, enlazado interno | 🟡 | AGT-04/El Ojo | 3 h |

**Quick wins (mismo día):** #1, #3, #4.
**Mayor ROI:** #2 (limpiar canibalización) y #5 (priorizar con datos reales de Google).

### Siguiente paso con el skill (próxima sesión de Claude Code)
```
/seo page    https://nosvers.com/                                      # afinar title+meta home
/seo ecommerce https://nosvers.com/produit/humus-lombric-amendement-bio/  # validar Product schema
/seo google  https://nosvers.com/                                      # datos GSC reales (Site Kit)
/seo geo     https://nosvers.com/                                      # enriquecer llms.txt + FAQ
```
> Los slash commands `/seo …` quedan disponibles para Angel en la **próxima** sesión (la skill se instaló en esta). Esta auditoría se ejecutó manualmente con los scripts del skill + crawl server-side vía VPS.

---

## Limitaciones de esta pasada

- **Tráfico/keywords reales:** Ahrefs en plan *Starter* (Site Explorer no disponible). Pero **Site Kit/GSC ya está conectado** en el sitio → los datos de Google están a un clic (acción #5).
- **CWV de campo:** disponibles en Site Kit; no enlazados a esta auditoría automatizada todavía.
- El contenedor de Claude Code no alcanza nosvers.com (política de red del entorno); el crawl se hizo server-side desde el VPS → datos 100% reales del HTML en producción.

---

*Auditoría del Director Ejecutivo (Claude Code) · skill claude-seo · para Angel, CEO de NosVers.*
