# Estado de aplicación de cambios SEO — nosvers.com

**Fecha:** 2026-05-31 · **Estado:** ⚠️ NO aplicado todavía

## Qué pasó
Se intentó aplicar las fases 1-2 (title+meta) vía el VPS, pero **el WordPress de
nosvers.com NO está en el VPS**. El VPS (`/home/nosvers/public_html`) aloja la
*app granja* (`api.php`), no el WordPress. El WordPress real vive en **hosting
compartido de Hostinger** (DB `u859094205_zqrpl`), al que el VPS solo accede por HTTP.

Por eso: `wp-load.php` no existe en esa ruta, wp-cli no encontró la instalación,
y el intento de UPDATE no tocó nada. **El sitio está intacto** (verificado: la home
sigue mostrando `Accueil - NosVers`, sin cambios).

## Corrección de registro
Un commit anterior (`48d5d0a`) afirmó por error que los cambios estaban
"aplicados y verificados en producción". **Era incorrecto.** Este documento lo rectifica.

## Vía real de aplicación (a confirmar)
1. **WP REST API** (`https://nosvers.com/wp-json/`) con application password —
   escribir meta AIOSEO por página. Requiere credenciales WP (WP_USER/WP_PASS del CLAUDE.md).
2. **Manual** en WP-Admin → AIOSEO por página (5 min, Angel o yo con acceso).

Los textos propuestos siguen en `seo/propuesta-cambios-2026-05.md` (sin cambios).
