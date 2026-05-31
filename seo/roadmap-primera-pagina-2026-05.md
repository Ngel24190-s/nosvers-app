# Roadmap a primera página de Google — nosvers.com

**Fecha:** 2026-05-31 · **Objetivo:** posicionar NosVers en página 1 y traer tráfico orgánico.
**Herramientas:** 100% gratis — Google Search Console (Site Kit, ya conectado), Keyword Planner, Bing Webmaster. Sin Ahrefs de pago.

---

## ✅ YA HECHO (aplicado y verificado en producción)
Title + meta description optimizados en home (490), boutique (6), à-propos (22), contact (466).
Ver `seo/cambios-aplicados-2026-05-31.md`.

---

## 🔴 BLOQUE 1 — Limpiar canibalización de URLs (el mayor freno)

Inventario real (REST API). Hay **páginas duplicadas publicadas** compitiendo por la misma keyword:

| Tema | ✅ Canónica (mantener) | ❌ Duplicadas → 301 a la canónica |
|------|----------------------|-----------------------------------|
| **Home** | `490 /accueil/` | `343 /accueil-2/` |
| **Club Sol Vivant** | `515 /club-sol-vivant/` | `763 /club-du-sol-vivant/`, `510 /club-sol-vivant-rejoignez-la-communaute/` |
| **Contact** | `466 /contact/` | `768 /contact-2/` |
| **Guide gratuit** | producto WooCommerce (lead magnet) | `396 /guide-gratuit/` (página duplicada) |
| **Panel fotos** | `802 /panel-fotos/` (uso interno) | `59 /panel-fotos/` → noindex (no es para Google) |

Además: páginas/posts `/a-venir-*` ("próximamente") → **`noindex`** mientras sean placeholders sin contenido real (no deben competir ni gastar crawl budget).

**Por qué importa:** 3 URLs de "club" compitiendo entre sí = Google no sabe cuál mostrar → ninguna posiciona bien. Consolidar concentra toda la autoridad en una.

**⚠️ Por qué NO lo aplico todavía:** un 301 mal puesto puede tumbar una página que ya reciba visitas. Necesito 5 min de Search Console para ver cuál variante ya tiene impresiones y elegir esa como canónica. **Acción para Angel:** activar Dashboard Sharing en Site Kit, o aplicar los 301 tú con esta tabla.

**Cómo se aplican (cuando demos el OK):** plugin de redirecciones de AIOSEO (Redirects) — sin tocar ficheros. Reversible.

---

## 🟢 BLOQUE 2 — Estrategia de keywords (ganar donde se puede)

**Regla:** no pelear por términos genéricos saturados ("lombricompost", "engrais") al principio. Atacar **long-tail + local**, donde una ferme pequeña en Dordogne SÍ puede llegar a página 1.

### Keywords objetivo → página que las debe captar

| Keyword objetivo (long-tail/local) | Intención | Página destino | Estado |
|------------------------------------|-----------|----------------|--------|
| `lombricompost Dordogne` / `acheter lombricompost Périgord` | Transaccional local | producto humus de lombric | Optimizar title/H1 |
| `vers de pêche Dordogne` / `dendrobaena veneta acheter` | Transaccional | producto vers de pêche | ✅ ya buen title |
| `acheter vers compost eisenia` | Transaccional | producto vers Eisenia | ✅ ya buen title |
| `humus de lombric bio` | Transaccional | producto humus | Optimizar |
| `démarrer un lombricomposteur` | Informacional | `/demarrer-lombricomposteur-guide-debutant/` | ✅ existe → reforzar |
| `lombricompost ou compost classique` | Informacional | artículo comparación | ✅ existe |
| `recette lombrithé` / `thé de compost` | Informacional | **artículo nuevo** | Crear (AGT-04) |
| `engrais vert quand semer` | Informacional | **artículo nuevo** | Crear (AGT-04) |

### Patrón de contenido ganador (para cada artículo)
1. Responder la pregunta en el **primer párrafo** (gana posición 0 / IA).
2. Sección práctica "comment faire" con pasos.
3. Bloque **FAQ** (capta long-tail + citas en ChatGPT/Perplexity).
4. **Enlace interno al producto** relacionado (convierte tráfico en venta).

---

## 🟢 BLOQUE 3 — Enlazado interno (gratis, puro upside)

Cada artículo del blog debe enlazar a su producto. Sin esto, el tráfico informacional no convierte y la autoridad no fluye a las páginas de venta.

| Artículo existente | → enlaza a producto |
|--------------------|---------------------|
| Dendrobaena veneta / vers de pêche Dordogne | producto vers de pêche |
| Eisenia hortensis / vers horticulteur | producto vers Eisenia |
| Démarrer un lombricomposteur | producto vers Eisenia + humus |
| Lombricompost vs compost | producto humus de lombric |

**Reversible y sin riesgo** → esto SÍ puedo aplicarlo vía REST (editar contenido de post) si Angel quiere.

---

## 📅 BLOQUE 4 — Ritmo sostenido (AGT-04 · El Investigador)
- **1 artículo/semana** atacando una long-tail de la tabla (cron ya montado: lunes 7h).
- Cada artículo: patrón ganador + enlace a producto + FAQ.
- Todo en **draft** → aprobación de Angel antes de publicar (regla de oro).

---

## 📊 Medición (cuando haya acceso GSC)
- Revisar keywords en **posición 8-20** → las que con un empujón saltan a página 1. Son la prioridad real.
- CTR bajo con muchas impresiones → mejorar title/meta (como ya hicimos en home).
- Repetir auditoría mensual con el skill `claude-seo`.

---

## Resumen de qué necesito de Angel
1. **Acceso a Search Console** (Dashboard Sharing en Site Kit, 2 min) → desbloquea priorización con datos + validación segura de los 301.
2. **OK para enlazado interno** (Bloque 3) → lo aplico ya, sin riesgo.
3. **OK para empezar drafts de artículos** (Bloque 4) → primer artículo esta semana.
