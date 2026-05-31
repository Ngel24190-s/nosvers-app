# Producto "Extrait Vivant" — preparado para revisión (NO publicado)

**Fecha:** 2026-05-31 · **Estado:** 🟡 PRIVATE — esperando OK de Angel para publicar.

## Qué es y por qué
Versión **DIY** del extracto de lombricompost: kit de materiales + protocolo para que el
cliente fabrique 20 L de extrait aérobie en casa. Al vender un **kit + know-how** (no un
líquido embotellado como bioestimulante), **esquiva la homologación AMM** francesa que sí
afectaría a un LombriThé líquido. Aprovecha la demanda real detectada en GSC
("lombrithé prix/bio", "humus de lombric") que hasta ahora caía en artículos sin producto.

## Estado del producto (ID 169)
| Campo | Valor |
|-------|-------|
| Nombre | Extrait Vivant de Lombric — Version Essentielle |
| Precio | **45,00 €** · SKU NV-KIT-001 · stock: instock |
| URL | `https://nosvers.com/produit/extrait-vivant-de-lombric/` |
| Imagen | ✅ (lombrithe-proceso-vers-gants.jpg) · Categoría: Sol Vivant |
| Contenido | 1.949 car. (qué es, la cadena NosVers, contenido del kit) |
| **Status** | **private** ← no visible al público (anónimo recibe 404) |

## Cambios aplicados (todos reversibles, con backup)
1. **Slug optimizado:** `kit-lombrithe-complet` → `extrait-vivant-de-lombric`
   (evita el término "lombrithe"; usa la marca real del producto).
2. **Liberación del slug:** la página vieja 462 (era solo un stub "Redirection… Vers
   l'Extrait Vivant", 63 car.) → renombrada `extrait-vivant-info` + pasada a `draft`.
   Conservada, no borrada.
3. **Title SEO:** `Extrait Vivant de Lombric — Kit DIY 20 L · NosVers`
4. **Meta description:** *"Kit pour fabriquer 20 L d'extrait aérobie de lombricompost chez
   vous. Lombricompost NosVers, substrats pré-dosés et protocole. Multipliez ×1000 la vie
   de votre sol."* (~158 car.)

## Verificado
- Producto sigue **private** (anónimo → 404). ✅
- Slug viejo y page vieja → 301 (sin colisión). ✅
- Title/meta SEO guardados en AIOSEO. ✅
- Backups: `/home/nosvers/backups/extrait_activation/` (page462, product169, seo169).

## Pendiente de tu OK para publicar
1. Cambiar status `private` → `publish`.
2. Añadir CTA/enlace al producto desde el artículo estrella
   `/lombrithe-engrais-liquide-vivant-biostimulant/` (110 impr, pos 12.6) → convertir esas
   visitas en ventas.
3. (Opcional) añadir `Product` schema review/precio si no lo emite ya WooCommerce.

## Cómo revertir
Restaurar desde `/home/nosvers/backups/extrait_activation/*_<TS>.json`:
product169 (slug), page462 (slug+status), seo169 (title/meta).
