# Revisión final ficha Extrait Vivant — correcciones aplicadas

**Fecha:** 2026-05-31 · Producto 169 · sigue **PRIVATE** (pendiente OK de Angel para publish).
**Backup:** /home/nosvers/backups/extrait_activation/product169_PREreview_*.json

## Problemas detectados y corregidos

### 🔴 Técnicos (bloqueaban venta/envío)
1. **catalog_visibility: hidden → visible** — sin esto NO aparecería en la boutique ni búsquedas (el SEO no serviría de nada). Corregido.
2. **Peso/dimensiones vacíos → 2 kg, 30×25×20 cm** — necesario para calcular gastos de envío en checkout.
3. **Upsells a productos privados/duplicado (170,171,13) → [14,12,74]** productos reales publicados (vers Eisenia, humus, engrais vert) → cross-sell funcional + sube ticket medio.

### 🟠 SEO / coherencia
4. **Alt de imagen** "Manipulation des vers en production LombriThé" → "Kit Extrait Vivant de Lombric NosVers — lombricompost et matériel".
5. **Title SEO** "Kit DIY 20 L" → "Kit complet 20 L" (ya no es DIY, lleva la bomba).
6. **Meta description** reescrita: menciona "pompe, diffuseur et récipient inclus" + "Plus vivant qu'un lombrithé en bouteille".

### ✏️ Reescritura estratégica (decisión de Angel)
Añadida sección **« LombriThé… et notre Extrait Vivant : quelle différence ? »**:
- Capta la búsqueda "lombrithé" (que SÍ tiene volumen en GSC: lombrithé prix/bio/composition).
- Da la vuelta a la limitación legal: el lombrithé en bouteille se asfixia/necesita conservantes;
  el nuestro se hace **fresco, al pico de actividad microbiana, sin aditivos** → superior.
- Posiciona el Extrait Vivant como la versión mejor Y legal. La limitación → argumento de venta.

## Estado final verificado
| Campo | Valor |
|-------|-------|
| Nombre | Extrait Vivant de Lombric — Version Essentielle |
| URL | /produit/extrait-vivant-de-lombric/ |
| Precio | 39€ · stock instock · SKU NV-KIT-001 |
| Visibilidad | visible · status **private** |
| Envío | 2 kg · 30×25×20 cm |
| Kit completo | lombricompost + mélasse + farine + diffuseur + récipient + **pompe USB** + protocole |
| Title SEO | Extrait Vivant de Lombric — Kit complet 20 L · NosVers |
| Margen | ~74% (COGS ~10€ con pompe USB) |

## Pendiente OK de Angel para publicar
1. status `private` → `publish`.
2. CTA al producto desde artículo /lombrithe-engrais-liquide-vivant-biostimulant/ (110 impr, pos 12.6).
3. (Opcional) artículo de blog "LombriThé vs Extrait Vivant" para captar más búsquedas.
