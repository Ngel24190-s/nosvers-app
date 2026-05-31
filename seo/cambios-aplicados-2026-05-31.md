# Cambios SEO aplicados — nosvers.com

**Fecha:** 2026-05-31 · **Aplicado por:** Director Ejecutivo (Claude Code) vía VPS
**Backup:** `/home/nosvers/backups/aioseo_posts_20260531_064500.sql` (tabla wpmm_aioseo_posts)
**Método:** `$wpdb->update` sobre `wpmm_aioseo_posts` (solo metadatos AIOSEO; no se tocó contenido, post_title, menús ni diseño) + purga LiteSpeed. Reversible con el backup.

## ✅ Fase 1-2 — Title + meta description (verificado en producción)

### Home (page 490)
- **Title:** `NosVers · Lombricompost & vers vivants en Dordogne` (50)
- **Meta:** `Ferme lombricole en Dordogne (24190). Lombricompost mûr, vers de compost et de pêche, engrais verts élevés à la main. Livraison en France.` (137)
- Antes: title `Accueil - NosVers` (genérico) · meta **vacía**.

### Boutique (page 510)
- **Title:** `Boutique · Lombricompost, vers & engrais verts bio · NosVers` (59)
- **Meta:** `Achetez lombricompost mûr, vers de compost (Eisenia), vers de pêche et packs d'engrais verts. Produits vivants de notre ferme en Dordogne.` (136)
- Antes: title con marca duplicada · meta de 333 car. (truncada).

### À propos (page 515)
- **Title:** `Notre ferme lombricole à Neuvic, Dordogne · NosVers` (51)
- **Meta:** `Angel & África, ferme NosVers à Neuvic (24190). Notre histoire et notre approche du sol vivant et de la lombriculture, sans chimie.` (130)

### Contact (page 343)
- **Title:** `Contact · Ferme NosVers · Neuvic, Dordogne (24190)` (50)
- **Meta:** `Une question, un atelier ou une commande sur mesure ? Écrivez à la ferme NosVers, réponse sous 48 h. Neuvic, Dordogne.` (117)
- Antes: title `NosVers · Contact - NosVers` (marca duplicada) · meta de 355 car.

**Resultado:** marca duplicada `- NosVers` eliminada; home con title orientado a keyword+localidad y meta description presente.

## ⏳ Pendiente (no aplicado — requiere tu revisión)
- **Fase 3 (consolidación de URLs duplicadas, 301):** verificar antes con datos de GSC cuál variante posiciona.
- **Fase C (contenido):** enlazado interno blog→producto, FAQ, 1 artículo/semana (AGT-04).

## Cómo revertir
`php /tmp/wp-cli.phar --path=/home/nosvers/public_html db import /home/nosvers/backups/aioseo_posts_20260531_064500.sql --allow-root` + purgar LiteSpeed.
