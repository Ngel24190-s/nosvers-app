# Roadmap a primera página de Google — nosvers.com

**Fecha:** 2026-05-31 · **Objetivo:** posicionar NosVers en página 1 y traer tráfico orgánico.
**Herramientas:** 100% gratis — Google Search Console (Site Kit, ya conectado), Keyword Planner, Bing Webmaster. Sin Ahrefs de pago.

---

## ✅ YA HECHO (aplicado y verificado en producción)
Title + meta description optimizados en home (490), boutique (6), à-propos (22), contact (466).
Ver `seo/cambios-aplicados-2026-05-31.md`.

---

## 🔴 BLOQUE 1 — Limpiar canibalización de URLs (el mayor freno)

Inventario **verificado por REST API** (29 páginas + 6 productos + posts). Duplicados reales confirmados (mismo título servido por varias URLs):

| Tema | ✅ Canónica (mantener) | ❌ Duplicadas → 301 a la canónica | Verificación |
|------|----------------------|-----------------------------------|--------------|
| **Club Sol Vivant** | `/club-sol-vivant/` | `399 /club-du-sol-vivant/`, `529 /club-sol-vivant-rejoignez-la-communaute/` (post) | ✅ las 3 sirven el mismo `<title>` |
| **La Ferme / À propos** | `22 /a-propos/` (la mejor escrita) | `465 /la-ferme/`, `53 /notre-ferme/` | ✅ la-ferme y notre-ferme = mismo `<title>` |
| **Guide gratuit** | `532 /produit/guide-gratuit-les-5-erreurs.../` (lead magnet Woo) | `780 /guide-gratuit/` (página duplicada) | Confirmar cuál capta el opt-in |
| **Extrait / LombriThé** | elegir 1: `462 /extrait-vivant-de-lombric/` o `394 /lombrithe/` | la otra → 301 | ⚠️ a verificar contenido de cada una |

**Placeholders `/a-venir-*` → `noindex`** (8 posts: atelier, club, kit-vie-sol, lombrithé, manuel, pack-automne, pack-été, service-frais) + página `812 /a-venir/`. Son "próximamente" sin contenido real → no deben competir ni gastar crawl budget. Cuando el producto exista, se convierte en su ficha real.

**Drafts/privados que NO indexan (OK, no tocar):** `793 /boutique-preview/`, `794 /preview-boutique-v2/` (draft), `71 /confidentialite/`, `10 /remboursements_retours/` (private).

**Por qué importa:** 3 URLs de "club" y 3 de "ferme" sirviendo el mismo contenido = Google no sabe cuál mostrar → ninguna posiciona bien. Consolidar concentra toda la autoridad en una sola.

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

## ⚠️ Estado del acceso a Search Console
Site Kit está **conectado** (`connected:true`), pero el usuario `claude_nosvers` (con el que entro por Application Password) **no tiene los permisos de Google** (`authenticated:false`, faltan scopes `webmasters`). Una Application Password autentica en WordPress pero **no puede conceder OAuth de Google** — esa conexión la hizo otro admin con su cuenta Google personal.

**Por eso no puedo leer las keywords/posiciones de GSC todavía.** Tres formas de desbloquearlo:
- **(a)** En Site Kit → Settings → **Dashboard Sharing**, compartir el dashboard de Search Console con el rol del usuario `claude_nosvers`. (2 min, lo más limpio.)
- **(b)** Que Angel entre en GSC y **exporte** el informe de Rendimiento (últimos 3 meses, por consulta y por página) y me pase el CSV.
- **(c)** Que el usuario `claude_nosvers` conecte su propia cuenta de Google en Site Kit.

## Resumen de qué necesito de Angel
1. **Desbloquear Search Console** (opción a, b o c arriba) → permite priorizar con datos reales y validar los 301 sin riesgo.
2. **OK para enlazado interno** (Bloque 3) → lo aplico ya, sin riesgo y sin GSC.
3. **OK para empezar drafts de artículos** (Bloque 4) → primer artículo esta semana.
