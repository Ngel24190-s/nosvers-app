# repos-para-code
*2026-03-15 07:59*

# Repos GitHub para instalar en Claude Code — NosVers
*Seleccionados 2026-03-14*

## INSTALAR AHORA — Prioridad alta

### 1. obra/superpowers ⭐ 81k
```
/plugin marketplace add obra/superpowers-marketplace
/plugin install superpowers@superpowers-marketplace
```
Qué aporta: workflow TDD + brainstorm antes de codificar + git worktrees + subagentes en paralelo.
Por qué: Code deja de romper cosas al azar. Antes de tocar index.html, genera un plan y lo validas.

### 2. VoltAgent/awesome-claude-code-subagents ⭐ colección masiva
```
curl -sO https://raw.githubusercontent.com/VoltAgent/awesome-claude-code-subagents/main/install-agents.sh
chmod +x install-agents.sh
./install-agents.sh
```
Instalar específicamente:
- workflow-orchestrator — coordinación de tareas complejas
- research-analyst — buscar información antes de implementar
- python-expert — para los agentes Python de NosVers
- web-developer — para index.html y la web

### 3. wshobson/agents ⭐ 112 agentes especializados
```
/plugin install agents@superpowers-marketplace
```
O directamente: clonar y copiar los agentes relevantes a ~/.claude/agents/
Qué aporta: 16 orquestadores de workflow, 79 herramientas de desarrollo, agente SEO específico.

### 4. hesreallyhim/awesome-claude-code
Lista curada de los mejores plugins y skills. Leer antes de instalar nada más.
URL: https://github.com/hesreallyhim/awesome-claude-code
Destacados:
- Claude Session Restore — recuperar contexto entre sesiones (muy útil para NosVers)
- Design Review Workflow — revisar la web antes de publicar
- AgentSys — workflow automatización tarea → producción

## INSTALAR DESPUÉS — Cuando tengamos más tiempo

### 5. affaan-m/everything-claude-code
Sistema completo de optimización de rendimiento para Code.
Incluye: memoria, seguridad, research-first development.
```
npm install -g everything-claude-code
```

### 6. 0xfurai/claude-code-subagents
100+ subagentes especializados. Especialmente útil:
- bash-expert (para scripts en el VPS)
- python-expert (para los agentes NosVers)
- seo-expert (para AGT-04)

## CÓMO INSTALAR SUPERPOWERS EN EL VPS (para Code)

Ejecutar en la sesión tmux de Code:
```bash
# En Claude Code, escribir:
/plugin marketplace add obra/superpowers-marketplace
/plugin install superpowers@superpowers-marketplace
# Salir y reiniciar Claude Code
```

O manualmente:
```bash
git clone https://github.com/obra/superpowers.git ~/.claude/plugins/cache/superpowers
```

## RESULTADO ESPERADO

Con superpowers instalado, cuando Code vaya a modificar index.html:
1. Primero pregunta: "¿Qué quieres lograr exactamente?"
2. Genera un plan claro
3. Angel lo valida
4. Code ejecuta con TDD
5. No rompe lo que ya funcionaba


---
*2026-03-15 08:02*


---

## REPOS DISEÑO WEB + WORDPRESS — Añadir a Code

### 1. elvismdev/claude-wordpress-skills ⭐ CRÍTICO PARA NOSVERS
```
/plugin marketplace add elvismdev/claude-wordpress-skills
/plugin install claude-wordpress-skills@claude-wordpress-skills
```
Qué aporta: skills específicos para WordPress — performance, seguridad, Gutenberg, temas.
Comandos clave:
- `/wp-perf-review` — auditoría completa del sitio antes de deploy
- `/wp-perf` — escaneo rápido del tema nosvers-theme
Detecta: queries N+1, hooks caros, problemas de caché, bundles JS lentos.
Por qué: antes de tocar theme.json o CSS, Code hace auditoría automática.

### 2. Automattic/wordpress-agent-skills ⭐ OFICIAL DE WORDPRESS
```
/plugin marketplace add Automattic/wordpress-agent-skills
```
Qué aporta: skills oficiales de Automattic para crear temas WordPress completos con IA.
Incluye comando `/create-site` — describe el sitio y genera el tema completo.
Funciona con WordPress Studio y block themes (FSE).
Por qué: para reconstruir nosvers.com con el diseño del Studio V2 correctamente.

### 3. frontend-design (Anthropic oficial) ⭐ PARA LA WEB Y LA APP
```
/plugin install frontend-design@superpowers-marketplace
```
Qué aporta: Code genera interfaces production-grade que no parecen "AI slop".
Tipografía distintiva, paletas cohesivas con CSS variables, animaciones de alto impacto, composición espacial con asimetría y elementos que rompen la cuadrícula.
Por qué: exactamente lo que necesita nosvers.com para parecerse al Studio V2.

### 4. vercel-labs/web-interface-guidelines
```
/plugin install web-interface-guidelines@superpowers-marketplace
```
Qué aporta: 22k stars — valida el código HTML/CSS contra 22 reglas de calidad de interfaces web.
Fetcha las guidelines, lee los archivos, aplica todas las reglas y reporta violaciones.
Por qué: después de que Code modifique index.html o theme.json, lo valida automáticamente.

### 5. ComposioHQ/awesome-claude-plugins — Para el diseño
```
/plugin install canvas-design@superpowers-marketplace
/plugin install theme-factory@superpowers-marketplace
```
- `canvas-design` — crea posters, arte visual, diseño estático en PNG/PDF
- `theme-factory` — aplica temas profesionales (10 presets) a la web y posts de Instagram
theme-factory aplica fuentes y colores profesionales a slides, docs, reportes, y landing pages HTML.

### 6. webapp-testing (Playwright)
```
/plugin install webapp-testing@superpowers-marketplace
```
Qué aporta: Code abre un navegador real y testea nosvers.com visualmente.
Puede detectar: menú roto, botones que no funcionan, páginas que no cargan.
Por qué: en vez de que Code diga "debería funcionar", lo verifica él mismo en el navegador.

---

## CÓMO DECIRLE A CODE QUE LO INSTALE TODO

Pega esto en la terminal de Code:
```
/plugin marketplace add elvismdev/claude-wordpress-skills
/plugin install claude-wordpress-skills@claude-wordpress-skills
/plugin install frontend-design@superpowers-marketplace
/plugin install canvas-design@superpowers-marketplace
/plugin install webapp-testing@superpowers-marketplace
```

Después para arreglar nosvers.com:
```
Usa el skill wordpress y frontend-design para revisar 
nosvers.com y hacer que se parezca al diseño del Studio V2.
Tipografía: Playfair Display + DM Sans.
Paleta: #FEFAF4 fondo, #3D6B20 verde, #1c1510 texto.
```


---
*2026-03-15 08:05*


---

## REPOS REDES SOCIALES — Publicación automática

### ⭐ LA SOLUCIÓN COMPLETA: Ayrshare

**Qué es:** API de publicación social que conecta con 13+ redes desde un solo sitio.
Plataformas: Instagram, Facebook, TikTok, YouTube, Pinterest, Reddit, Threads, Bluesky y más.

**Por qué es la mejor opción para NosVers:**
- Una sola API key → publica en Instagram + Facebook + YouTube a la vez
- Programa posts con fecha/hora exacta
- Sube imágenes via URL (no hace falta mover archivos)
- Genera hashtags automáticamente
- Analytics de engagement por post
- MCP server disponible → yo puedo publicar directamente desde Claude.ai

**Precio:** desde ~29$/mes — pero cubre TODO el stack de RRSS de NosVers.

### 1. vanman2024/ayrshare-mcp ⭐ — MCP server oficial
```bash
git clone https://github.com/vanman2024/ayrshare-mcp
cd ayrshare-mcp && pip install -e .
```
75+ herramientas MCP para publicar en 13+ plataformas simultáneamente. Scheduling con ISO 8601, bulk operations, auto-hashtags, evergreen content con auto-reposting.

**Añadir al MCP del VPS** → así yo (Claude) publico directamente sin Code.

### 2. HagaiHen/facebook-mcp-server — Facebook gratuito
```bash
git clone https://github.com/HagaiHen/facebook-mcp-server
```
MCP server para Facebook Page via Graph API gratuita. Crear posts, moderar comentarios, obtener insights, filtrar feedback negativo. Conexión directa con Claude Desktop.

Requiere: Facebook App + Page Access Token (gratuito).

### 3. jlbadano/ig-mcp — Instagram MCP directo
```
github.com/jlbadano/ig-mcp
```
MCP server para Instagram Business. Publicación directa via Instagram Graph API oficial.
Requiere: cuenta Instagram Business + Meta App aprobada.

### 4. ayrshare/marketingskills — Skills de marketing para Code
```
/plugin install marketingskills@ayrshare
```
Skills de marketing para Claude Code: CRO, copywriting, SEO, analytics, growth engineering.
Directamente de Ayrshare — complementa el MCP server.

---

## FLUJO RECOMENDADO PARA NOSVERS

### Opción A — Ayrshare (de pago, más simple)
```
AGT-09 Content Director genera el brief
        ↓
AGT-02 genera caption + edita foto
        ↓
Ayrshare MCP publica simultáneamente en:
  @nosvers.ferme (Instagram)
  Página NosVers (Facebook)
  Blog nosvers.com (WordPress)
        ↓
Angel recibe confirmación por Telegram
```
Coste: ~29$/mes. Cubre TODO. Sin configurar APIs individuales.

### Opción B — Gratis con APIs individuales
```
Instagram → instagrapi (ya en pipeline)
Facebook → HagaiHen/facebook-mcp-server (gratis con Graph API)
YouTube → YouTube Data API v3 (gratis hasta 10k requests/día)
```
Coste: 0€. Más configuración inicial.

---

## PARA CODE — Instalar ahora

### Si Angel elige Ayrshare:
```bash
# En el VPS
git clone https://github.com/vanman2024/ayrshare-mcp /home/nosvers/ayrshare-mcp
cd /home/nosvers/ayrshare-mcp
/home/nosvers/venv/bin/pip install -e . -q

# Añadir al .env
echo "AYRSHARE_API_KEY=tu_api_key_aquí" >> /home/nosvers/.env

# Registrar en el MCP server de NosVers para que Claude.ai pueda usarlo
```

### Si Angel elige gratis:
```bash
# Facebook MCP
git clone https://github.com/HagaiHen/facebook-mcp-server /home/nosvers/facebook-mcp
cd /home/nosvers/facebook-mcp && npm install

# Instagram ya está con instagrapi (ver pipeline-instagram-automatico.md)
```

### Marketing Skills para Code:
```
/plugin install marketingskills@ayrshare
```
