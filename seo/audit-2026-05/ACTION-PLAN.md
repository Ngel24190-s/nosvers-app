# Plan de acción SEO — nosvers.com → Top 3 Google France

Priorizado por impacto/esfuerzo. Marcado **[OK Angel]** lo que requiere tu aprobación antes de ejecutar.

## 🔴 CRÍTICO (esta semana)

| # | Acción | Impacto | Esfuerzo | Quién |
|---|---|---|---|---|
| 1 | **Publicar producto Extrait Vivant** (`private`→`publish`) — hoy da 404 | Alto | 2 min | **[OK Angel]** |
| 2 | **Schema Product/Offer** en los 6 productos (precio, dispo, stock) | Alto | 30 min | Yo (AIOSEO/WC) |
| 3 | **Arreglar redirects + títulos duplicados** (lombrithe→club, guides/pack→boutique) | Alto | 30 min | Yo |
| 4 | **Reescribir metas >160c** (la-ferme, club, guide-gratuit, a-venir, 3 posts) | Medio | 40 min | Yo |
| 5 | **noindex a las páginas "à venir"** (9 posts + /a-venir/) | Medio | 15 min | Yo |

## 🟠 ALTO (este mes)

| # | Acción | Impacto | Esfuerzo |
|---|---|---|---|
| 6 | **Publicar artículo "LombriThé vs Extrait Vivant"** (post 1279) | Alto | **[OK Angel]** |
| 7 | Consolidar las 3 páginas "ferme" (notre-ferme/la-ferme/a-propos) en 1 fuerte + redirects | Medio | 1 h |
| 8 | Activar conversión **WebP** en LiteSpeed | Medio | 10 min |
| 9 | Engordar páginas thin (notre-ferme 101→500+ palabras) | Medio | 1 h |
| 10 | **Interlinking**: artículos de vers ↔ fichas producto ↔ home | Alto | 45 min |

## 🟡 MEDIO

| # | Acción | Impacto |
|---|---|---|
| 11 | `llms.txt` en raíz (citabilidad IA) | Medio (GEO) |
| 12 | FAQ schema en producto y artículos ("comment faire du lombrithé", "quel ver pour…") | Medio |
| 13 | Página pilar "lombricompost" como hub que enlace a todo el cluster | Alto a medio plazo |
| 14 | Optimizar title home con keyword delante | Bajo |

## 🟢 BACKLOG
- Backlinks: GBP (Google Business Profile) Neuvic + citaciones locales (annuaires FR agricoles).
- Reseñas → AggregateRating real en productos.
- Cluster de contenido: "engrais vert", "sol vivant", "thé de compost" (ver seo-cluster).

---

---

## ✅ EJECUTADO (2026-05-31)

| Acción | Resultado |
|---|---|
| **#1 Producto Extrait Vivant publicado** | ✓ `private`→`publish`. `/produit/extrait-vivant-de-lombric/` ahora HTTP **200**, 39€, en stock. |
| **#6 Artículo 1279 publicado** | ✓ `draft`→`publish`. `/lombrithe-ou-extrait-vivant-lombricompost/` HTTP **200**. |
| **#2 Schema Product/Offer** | ✓ Verificado: al publicarse, AIOSEO genera `Product`+`Offer`+`Brand`+`UnitPriceSpecification` automáticamente en los 6 productos. El "fallo" era consecuencia del 404. |
| **#5 noindex à-venir** | ✓ 8 posts (804-811) + página /a-venir/ (812) → `noindex` verificado en vivo. |
| **#4 Metas largas** | ✓ Reescritas a 136-147c con keyword delante: la-ferme, club-du-sol-vivant, guide-gratuit + 3 posts de vers. Verificado en vivo tras purgar cache. |
| **#11 llms.txt** | ✓ Ya existía (autogenerado por AIOSEO). Ver nota abajo. |

## ✅ EJECUTADO — 2ª tanda (2026-05-31): rework páginas ferme + consolidación

| Acción | Resultado |
|---|---|
| **#7 notre-ferme (53) retrabajada a fondo** | Era un placeholder vacío (101 palabras). Ahora **605 palabras**: contenido rico de la-ferme (3 piliers, método, valores) + **intro SEO** con keywords (ferme lombricole, Neuvic, Dordogne 24190) + **2 enlaces internos a productos** + botón CTA arreglado (apuntaba a un à-venir noindex → ahora /atelier/). Title + meta (142c) optimizados. |
| **a-propos (22) retrabajada a fondo** | **586 palabras**, 5 H2. Reescrita como página de **historia + E-E-A-T**: Angel/África, 2022, Neuvic, SIRET/MSA, ciclo real de producción. **Enlaces internos** a extrait vivant, engrais verts y los 2 artículos de vers. 2 enlaces rotos a páginas à-venir corregidos. Title + meta optimizados. |
| **la-ferme (465) consolidada** | Duplicaba a notre-ferme → **noindex + canonical → /notre-ferme/**. Elimina la canibalización entre las 3 páginas "ferme" sin perder la URL. |

**Resultado:** de 3 páginas que competían entre sí → **2 páginas fuertes y diferenciadas** (notre-ferme = la ferme/operaciones; a-propos = historia/quiénes somos) + 1 consolidada.

## ⚠️ Pendiente — SOLO accesible desde wp-admin (no hay REST API ni wp-cli)

WordPress está en hosting gestionado de Hostinger: solo llego por REST API, y estas 3 cosas no la exponen.

- **#8 WebP**: *LiteSpeed Cache → Image Optimization → activar "WebP Replacement"* (1 clic).
- **#3 Redirects** (addon Redirects de AIOSEO Pro, sin REST):
  - `/lombrithe/` → 301 a `/club-du-sol-vivant/` es **engañoso**. Reapuntar a `/lombrithe-ou-extrait-vivant-lombricompost/` (el artículo nuevo).
  - `/guides-formations/` y `/pack-engrais-vert/` → 301 a `/boutique/`: revisar si interesa conservarlos.
- **llms.txt**: el autogenerado por AIOSEO referencia URLs viejas/borradas (`/le-blog-de-la-lombriculture/`). Regenerar en *AIOSEO → Tools → llms.txt* o fijarlo manual.
