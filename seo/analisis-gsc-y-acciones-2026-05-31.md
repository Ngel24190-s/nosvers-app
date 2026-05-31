# Análisis Search Console + acciones ejecutadas — nosvers.com

**Fecha:** 2026-05-31 · **Datos:** Google Search Console, últimos 3 meses (export real de Angel).
**CSVs originales:** `seo/gsc-export-2026-05/`

---

## 📊 Diagnóstico con datos reales de Google

**Volumen (3 meses):** 33 clics · 284 impresiones · CTR 11,6% · posición media ~16.
Sitio nuevo, poca tracción aún, pero **tendencia al alza** (mejor día 29-mayo: 3 clics / 10 impr).
93% del tráfico es Francia. Reparto: 60% desktop / 39% móvil.

### 🔥 Hallazgo principal: el filón es LombriThé
La gente ya te busca por LombriThé y apareces cerca de página 1 — pero **no tienes producto que venderles**:

| Keyword | Posición | Impr. | Oportunidad |
|---------|----------|-------|-------------|
| `lombrithé composition` | **7** | 3 | ya en página 1 |
| `lombrithé` | 13 | 4 | a un empujón |
| `lombrithé prix` | **10.7** | 4 | **intención de compra** |
| `lombrithé bio` | 26.5 | 4 | intención de compra |
| `odeur lombrithé` / `lombrithé odeur` | 7 / 15 | 3 | informacional |
| `humus de lombric` | 25.3 | 9 | producto SÍ existe → optimizar |
| `humus vers de terre` | 19.3 | 3 | producto SÍ existe |
| `biostimulants à base de lombricompost` | 25.1 | 14 | mayor volumen impr. |

**Páginas que ya reciben impresiones:**
- `/` (home): 141 impr, pos 15.4, CTR 18% ✅
- `/lombrithe-engrais-liquide-vivant-biostimulant/` (artículo): **110 impr, pos 12.6** — 2ª más vista
- `/categorie-produit/lombricompost/`: pos 5.8 ✅ (¡ya página 1!)
- `/boutique/`: pos 6.3 ✅
- `/produit/humus-lombric-amendement-bio/`: **42 impr, pos 26, CTR 0%** → necesita optimización on-page

### Conclusión de negocio (decisión de Angel)
Hay demanda real de **"lombrithé prix" / "lombrithé bio"** (gente que quiere comprarlo) llegando a un artículo **sin producto**. Es el mayor agujero de conversión. → Crear la **ficha de producto LombriThé** sería la acción de mayor ROI directo.

---

## ✅ ACCIONES YA EJECUTADAS Y VERIFICADAS

### 1. Title + meta description (4 páginas) — hecho antes
Home, boutique, à-propos, contact. Ver `cambios-aplicados-2026-05-31.md`.

### 2. Enlaces rotos del blog — CORREGIDO (verificado: 0 rotos)
6 artículos enlazaban a productos LombriThé/packs inexistentes (404/301-rotos). Acción aprobada por Angel: **quitar enlace roto dejando el texto** + remapear los que redirigían a producto vivo.

| Post | Acción |
|------|--------|
| 80 LombriThé | quitados 4 enlaces a productos LombriThé inexistentes |
| 79 Démarrer lombricomposteur | remapeado `noyau-elevage`→`vers-compost-eisenia` + quitado `lombrithe-inoculum` |
| 78 Lombricompost vs compost | quitado `lombrithe-inoculum` |
| 81 Régénérer sol mort | quitado `lombrithe-inoculum` |
| 1210 Eisenia hortensis | quitado `kit-lombrithe-complet` |
| 77 Engrais vert guide | quedó solo con productos reales |

**Verificación:** crawl REST de los 10 posts → **0 enlaces rotos restantes**. Backups en `/home/nosvers/backups/post_content/`.

### 3. Sitemap — verificado OK
`sitemap.rss` (AIOSEO) tiene 41 items e **incluye los 12 posts del blog**. Declarado en robots.txt. La indexación por sitemap funciona; no era el problema.

---

## ⏸️ Fusión de fermes — RECOMENDACIÓN CAMBIADA (con datos)

Aprobaste "fusionar /la-ferme/ + /notre-ferme/ en /a-propos/". Pero al verificar:

1. **Las 3 páginas tienen 0 impresiones / 0 clics en GSC** → ninguna posiciona para nada. La urgencia SEO es baja.
2. `/notre-ferme/` (53) **ya es solo un stub de redirección** ("Redirection… Vers la ferme") — prácticamente ya está resuelta.
3. `/la-ferme/` y `/a-propos/` son **páginas de page-builder con CSS embebido** (mucho diseño inline). Una fusión automática del HTML **rompería el diseño** y perdería maquetación.

**Recomendación honesta:** en vez de fusionar contenido (destructivo y arriesgado con page-builder), lo correcto y seguro es:
- Mantener `/a-propos/` como canónica (ya tiene el title/meta optimizado).
- **301** de `/la-ferme/` y `/notre-ferme/` → `/a-propos/` (sin tocar el contenido de a-propos).
- Esto elimina la duplicación sin riesgo de romper diseño ni perder texto.

No lo aplico todavía: es reversible pero quiero tu OK con esta variante (redirigir en vez de fusionar).

---

## 🎯 Próximas acciones priorizadas POR DATOS GSC

| # | Acción | Por qué (dato GSC) | Riesgo |
|---|--------|--------------------|--------|
| 1 | **Crear ficha producto LombriThé** | "lombrithé prix/bio" en pos 7-26 con intención de compra y sin producto | decisión Angel |
| 2 | Optimizar `/produit/humus-lombric/` (title/H1/contenido) | 42 impr, pos 26, **CTR 0%** | bajo (REST) |
| 3 | Reforzar artículo LombriThé (110 impr, pos 12.6) → subir a top 10 | 2ª página más vista | bajo |
| 4 | 301 la-ferme + notre-ferme → a-propos | dedup, 0 tráfico que perder | bajo |
| 5 | `noindex` a las 8 páginas `/a-venir-*` | aparecen en GSC sin contenido real | bajo |
| 6 | Pedir indexación en GSC de páginas clave | sitio nuevo, acelerar | manual Angel |

---

*Análisis del Director Ejecutivo (Claude Code) con datos reales de Search Console, para Angel.*
