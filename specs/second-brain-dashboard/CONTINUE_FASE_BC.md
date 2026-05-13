# CONTINUE — Fase B + C combinadas (sin parar entre ellas)

Fase A del proyecto 002 cerrada (commit `683a410`). Angel ha validado visualmente y pidió continuar con el plan previsto **pero combinando B y C en un solo bloque continuo, sin pausa entre ellas**.

## Por qué combinar B+C

Fase A en solitario se ve "vacía" (solo timeline lectura). La sensación Notion-style real requiere B+C juntas:
- B aporta interactividad (editar in-place, capturar desde web, integraciones)
- C aporta la riqueza visual (kanban, vistas múltiples, grafo, wiki-links bidireccionales)

Por separado, B sin C todavía se siente "tipo lista con botones". Por separado, C sin B es "bonita pero solo lectura". **Combinadas = experiencia Notion-clone real**.

## Alcance B + C combinado

### De Fase B (interactividad)
1. **Captura por texto desde el navegador**: form rápido o atajo de teclado (`Ctrl+N`) → `dia_capturar` del MCP, autor inferido del JWT
2. **Editar nota in-place**: clic en una entrada del timeline → editor markdown con preview, guardar → reescribe el `.md` en el vault
3. **Borrar nota** con confirmación (soft delete: mover entrada a `dia/archivo/` con razón opcional)
4. **Estado infra en vivo** en sidebar lateral: VPS health, AEGIS/ALAMO último briefing, cron status, Stripe revenue del día, WordPress online, freqtrade pnl
5. **Lanzar un agente del unified-agent** con un clic (botones para agt05_africa, agt_eisenia, agt07_diario manual, orchestrator, etc.)
6. **Calendario integrado** Google Calendar via conector — vista lateral colapsable
7. **Gmail integrado** — bandeja prioritaria (`is:starred OR label:Lectura/Tech OR from:noreply@anthropic.com`), abrir hilo en panel lateral

### De Fase C (riqueza visual)
8. **Vistas múltiples** sobre el timeline: lista (actual), tabla (con columnas filtrables), board/kanban por etiqueta, calendario mensual, galería de cards
9. **Kanban proyectos NosVers**: leer `knowledge_base/proyectos/*.md` (crear estructura si no existe) con frontmatter `estado: todo|doing|done|blocked`, drag-and-drop entre columnas
10. **Wiki-links bidireccionales `[[nota]]`** estilo Obsidian: parsear referencias entre notas, mostrar backlinks en cada nota
11. **Grafo de conexiones**: nodos = notas, aristas = wiki-links, layout con d3-force. Hover muestra preview de nota
12. **Sidebar tipo Notion**: árbol de navegación del vault completo (`knowledge_base/*`), expandible, drag-and-drop reorganización (escribe al vault)
13. **Statistics widget**: notas por autor por semana, etiquetas dominantes, productividad NosVers (gráfica de barras simple)
14. **Búsqueda global Ctrl+K** estilo command palette de Notion: salta a cualquier nota, ejecuta acciones rápidas

## Constraints (no negociables)

- Mantener todo lo que define el proyecto: soberanía tecnológica, MCP-first, vault source of truth, reuso del 001
- NO instalar AppFlowy, NotionAPI, ni similares
- NO romper la Fase A: el timeline actual debe seguir funcionando, las vistas múltiples son ADITIVAS
- Frontend: seguir con React + Vite + Tailwind + shadcn/ui ya elegidos en Fase A
- Backend: extender `tablero/rest.py` con los endpoints nuevos, mismo patrón JWT-auth
- Vault permanece como markdown puro — todas las "bases de datos" que parezcan tipo Notion son en realidad ficheros `.md` con frontmatter
- TODOS los tests verdes antes de cada commit
- Commit conventional commits, agrupados por sub-componente (no un solo mega-commit)

## Flujo Spec Kit

1. `/speckit-specify` — escribe spec para Fase B+C combinada
2. `/speckit-clarify` — resuelve ambigüedades con Angel **solo si crítico**. Si las decisiones son técnicas/menores, decide tú con buen criterio anotando en `decisions.md` y continúa
3. `/speckit-plan` — stack/arquitectura
4. `/speckit-tasks` — desglose en tareas testables, agrupadas por sub-componente del 1-14
5. `/speckit-implement` — ejecuta sin parar, agrupando commits por sub-componente
6. Al cerrar: Telegram a Angel con resumen + cambios manuales pendientes (si los hay)

## Bug de permisos ya resuelto

`~/.claude/settings.json` global tiene auto-aprove para:
- Las 15 tools MCP `nosvers-mcp-2026`
- `Bash(*)`, `Read(*)`, `Edit(*)`, `Write(*)`, `Glob(*)`, `Grep(*)`

Si aún así te pide permiso para algo específico, **acepta opción 2 ("don't ask again")** una sola vez por categoría. No esperes 9h. Si una tool MCP se cuelga >30s, abortala y reintenta una vez más antes de continuar.

## Estimación

3-4 semanas si fuera trabajo humano. Para ti son varias horas, posiblemente toda la tarde+noche del 13 de mayo. **No te detengas a esperar validación intermedia** — Angel ya validó visualmente Fase A. Solo para si encuentras un bloqueo real que requiera decisión humana imposible de inferir.

## Definition of done

- 14 sub-componentes implementados y testeados (78/78 tests Fase A + nuevos)
- Despliegue dev funcional sobre `tablero.72.61.160.108.nip.io` (ya activo)
- Documentación en `tablero/README.md` actualizada con screenshots/asciinema (si se puede generar)
- Commit limpio por sub-componente, sin push (Angel hace push manual)
- Telegram a Angel al cerrar

## Última nota

Cuando termines, NO arranques Fase D (automatizaciones visuales). Esa es decisión separada de Angel y va en otro proyecto Spec Kit (`003-automation-engine` o similar).

---
*Instrucciones preparadas por Claude Opus 4.7 (sesión móvil), 2026-05-13 12:50 UTC*
