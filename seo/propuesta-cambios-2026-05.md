# Propuesta de cambios SEO — nosvers.com

**Fecha:** 2026-05-31 · **Estado:** 🟡 PROPUESTA — pendiente de aprobación de Angel
**Objetivo:** primera página de Google + tráfico orgánico. Ningún cambio aplicado todavía.
**Riesgo:** bajo. Todo son metadatos (editables campo a campo en AIOSEO) y redirecciones 301. No se toca contenido ni diseño. Reversible.

---

## 🆓 Herramientas gratuitas (sustituyen a Ahrefs de pago)

- **Google Search Console** (ya conectado vía Site Kit) → fuente principal de keywords reales.
- **Google Keyword Planner** (gratis con cuenta Ads) → volumen de keywords nuevas.
- **Bing Webmaster Tools** + **Ahrefs Webmaster Tools** (tier gratis, solo tu sitio) → backlinks.

**No contratar Ahrefs de pago.** GSC cubre lo esencial.

---

## 📌 PARTE A — Cambios on-page (metadatos AIOSEO)

> Cómo se aplica: WordPress → cada página/producto → caja AIOSEO → Title / Description.
> Sin riesgo: solo cambia lo que ve Google en la SERP, no la web.

### A1 · Home (la prioridad nº1)
| | Actual | Propuesto |
|---|---|---|
| **Title** | `Accueil - NosVers` (17) | `NosVers · Lombricompost & vers vivants en Dordogne` (50) |
| **Meta** | *(vacía)* | `Ferme lombricole en Dordogne (24190). Lombricompost mûr, vers de compost et de pêche, engrais verts — élevés à la main. Livraison en France.` (148) |

### A2 · Boutique
| | Actual | Propuesto |
|---|---|---|
| **Title** | `Boutique NosVers · Lombricompost, LombriThé et Engrais Verts - NosVers` (70, marca x2) | `Boutique · Lombricompost, vers & engrais verts bio · NosVers` (59) |
| **Meta** | 333 car. (se trunca) | `Achetez lombricompost mûr, vers de compost (Eisenia), vers de pêche et packs d'engrais verts. Produits vivants de notre ferme en Dordogne.` (152) |

### A3 · À propos
| | Actual | Propuesto |
|---|---|---|
| **Title** | `À Propos - NosVers` (18) | `Notre ferme lombricole à Neuvic, Dordogne · NosVers` (51) |
| **Meta** | 328 car. | `Angel & África, ferme NosVers à Neuvic (24190). Notre histoire, notre approche du sol vivant et de la lombriculture, sans chimie.` (140) |

### A4 · Contact
| | Actual | Propuesto |
|---|---|---|
| **Title** | `NosVers · Contact - NosVers` (27, marca x2) | `Contact · Ferme NosVers · Neuvic, Dordogne (24190)` (50) |
| **Meta** | 355 car. | `Une question, un atelier ou une commande sur mesure ? Écrivez à la ferme NosVers, réponse sous 48 h. Neuvic, Dordogne.` (133) |

### A5 · Fichas de producto (patrón general)
Los titles son buenos pero algunos pasan de 60 car. y repiten marca. Patrón propuesto: dejar el nombre + keyword + localidad, **quitar el sufijo `- NosVers` duplicado** (config global AIOSEO, ver B1). Revisar meta >160 → recortar a ~155 con keyword al inicio. (Detalle por producto en una segunda pasada con datos de GSC.)

---

## 📌 PARTE B — Ajustes globales

### B1 · Separador de marca duplicado
En AIOSEO → Search Appearance → Global Settings, el patrón de título añade `- NosVers` aunque el título ya contenga la marca. **Acción:** ajustar el "Title Separator / Site Title" para que la marca aparezca **una sola vez**. Afecta a varias páginas de golpe (boutique, contact, productos).

### B2 · Consolidar URLs duplicadas (canibalización) — el cambio de mayor impacto
Hoy compiten varias URLs por el mismo tema. Propuesta de canónica + 301:

| Tema | Mantener (canónica) | Redirigir 301 → | `noindex` |
|---|---|---|---|
| Club | `/club-sol-vivant/` | `/club-du-sol-vivant/`, `/club-sol-vivant-rejoignez-la-communaute/` | — |
| Guía gratuita | `/produit/guide-gratuit-les-5-erreurs.../` (lead magnet WooCommerce) | `/guide-gratuit/`, `/guide-gratuit-les-5-erreurs.../` (duplicadas) | — |
| Extrait/LombriThé | `/extrait-vivant-de-lombric/` | — | `/a-venir-lombrithe-extrait-vivant/` |
| Próximamente | — | — | **todas las `/a-venir-*`** mientras sean placeholders |

**Acción:** redirecciones 301 (plugin de redirecciones o .htaccess/LiteSpeed) + `noindex` a placeholders (AIOSEO por página) + limpiar el sitemap. **Verificación previa:** confirmar con GSC qué variante ya recibe impresiones para elegirla como canónica (no romper la que ya posiciona).

---

## 📌 PARTE C — Estrategia para llegar a primera página (tráfico orgánico)

La regla: **no pelear por keywords genéricas y competidísimas** ("lombricompost", "engrais") al principio. Atacar **long-tail + local**, donde NosVers puede rankear rápido, y escalar.

### C1 · Keywords objetivo realistas (a validar con Keyword Planner/GSC)

**Ganables ya (local + long-tail, baja competencia):**
- `lombricompost Dordogne` / `acheter lombricompost Périgord`
- `vers de pêche Dordogne` / `dendrobaena veneta acheter`
- `vers compost eisenia acheter France`
- `humus de lombric bio` / `acheter humus de ver de terre`
- `démarrer un lombricomposteur` (informacional → ya tienes artículo)

**Medio plazo (más volumen, más esfuerzo):**
- `engrais vert bio`, `sol vivant jardin`, `lombrithé recette`

### C2 · Acciones de contenido (vía AGT-04 · El Investigador)
1. **Enlazado interno blog → producto:** cada artículo enlaza a su producto (artículo Dendrobaena → ficha vers de pêche; artículo Eisenia → ficha vers compost). Reparte autoridad y guía a la compra.
2. **FAQ en fichas y artículos:** preguntas reales ("combien de vers pour démarrer ?", "lombricompost ou compost ?") → captan long-tail + citas en IA (ChatGPT/Perplexity).
3. **1 artículo/semana** atacando una long-tail de la lista C1 (ya tienes el cron AGT-04 montado).
4. **Profundizar fichas** a 600-900 palabras con uso, beneficios y dosis.

### C3 · Medición (con GSC gratis)
- Revisar en GSC qué keywords están en **posición 8-20** → son las que con un empujón (title/meta/contenido) saltan a primera página. Esas son la prioridad real, las sabremos con datos, no a ciegas.

---

## ✅ Orden de ejecución propuesto (cuando apruebes)

| Fase | Qué | Riesgo | Aplica |
|---|---|---|---|
| 1 | A1 (home title+meta) + B1 (marca duplicada) | Nulo | Hoy mismo |
| 2 | A2-A4 (meta boutique/à-propos/contact) | Nulo | Hoy mismo |
| 3 | B2 (consolidar URLs) — **previa verificación GSC** | Bajo | Tras revisar GSC |
| 4 | C2 (enlazado interno + FAQ) | Nulo | Semana 1 |
| 5 | C2.3 (1 artículo/semana) + C3 (medición) | Nulo | Continuo |

**Nada de esto se aplica sin tu OK.** Las fases 1-2 las puedo dejar hechas en 30 min vía VPS en cuanto digas; la fase 3 quiero verla contigo con los datos de GSC delante para no tumbar una URL que ya posicione.

---

*Propuesta del Director Ejecutivo (Claude Code) para Angel, CEO de NosVers.*
