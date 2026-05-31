# Cambios SEO aplicados — nosvers.com

**Fecha:** 2026-05-31 · **Estado:** ✅ APLICADO y VERIFICADO en producción
**Vía:** WP REST API → AIOSEO (`POST /wp-json/aioseo/v1/post`) con Application Password del usuario `claude_nosvers` (id 2). Ejecutado desde el VPS.
**Alcance:** solo metadatos SEO (title + meta description). No se tocó contenido, post_title, menús, diseño ni plugins.
**Backups:** estado previo guardado en `/home/nosvers/backups/aioseo_rest/` antes de cada cambio.

## Fase 1-2 — Title + Meta description (verificado en el HTML en vivo)

| Página | ID | Title nuevo | Long. |
|--------|----|-------------|-------|
| Home | 490 | `NosVers · Lombricompost & vers vivants en Dordogne` | 50 |
| Boutique | 6 | `Boutique · Lombricompost, vers & engrais verts bio · NosVers` | 59 |
| À propos | 22 | `Notre ferme lombricole à Neuvic, Dordogne · NosVers` | 51 |
| Contact | 466 | `Contact · Ferme NosVers · Neuvic, Dordogne (24190)` | 50 |

**Meta descriptions** (todas en francés, 117-137 car., con keyword + localidad + gancho):
- Home: *"Ferme lombricole en Dordogne (24190). Lombricompost mûr, vers de compost et de pêche, engrais verts élevés à la main. Livraison en France."*
- Boutique: *"Achetez lombricompost mûr, vers de compost (Eisenia), vers de pêche et packs d'engrais verts. Produits vivants de notre ferme en Dordogne."*
- À propos: *"Angel & África, ferme NosVers à Neuvic (24190). Notre histoire et notre approche du sol vivant et de la lombriculture, sans chimie."*
- Contact: *"Une question, un atelier ou une commande sur mesure ? Écrivez à la ferme NosVers, réponse sous 48 h. Neuvic, Dordogne."*

### Mejoras conseguidas
- **Home:** antes `Accueil - NosVers` (genérico, sin keyword) + meta **vacía** → ahora orientada a keyword + localidad, con meta description presente. Era la mayor fuga de SEO/CTR del sitio.
- **Marca duplicada eliminada** en boutique y contact (antes `… - NosVers` con NosVers ya en el título).
- **Metas largas recortadas** (boutique 333→136, contact 355→117, à-propos 328→130) → ya no se truncan en la SERP.

## Verificación
`curl` al front de cada URL (cache-busting) → los `<title>` y `<meta name="description">` muestran los valores nuevos. ✅ las 4.

## Pendiente (no aplicado — requiere datos GSC)
- **Fase 3 — consolidar URLs duplicadas (301):** variantes de club / guide-gratuit / extrait + páginas `/a-venir-*`. Verificar antes en GSC cuál variante posiciona para no tumbarla.
- **Fase C — contenido:** enlazado interno blog→producto, FAQ en fichas, 1 artículo/semana (AGT-04), priorización por keywords en posición 8-20.

## Cómo revertir
Restaurar el JSON correspondiente de `/home/nosvers/backups/aioseo_rest/<id>_<timestamp>.json` con `POST /wp-json/aioseo/v1/post`.

## Nota de seguridad
La Application Password usada puede revocarse en WP-Admin → Usuarios → claude_nosvers → Application Passwords. No está almacenada en el repo.
