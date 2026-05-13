# Brief — Second Brain Dashboard NosVers (Proyecto 002)

Web dashboard que da una piel visual sobre el vault multi-usuario de Angel y África. NO construye un cerebro nuevo, pone una vista sobre el que ya existe.

## 1. Quiénes lo usan

Angel y África. Acceden desde:
- Móvil (Android) → mismo dispositivo donde tienen la PWA del proyecto 001
- Ordenador Linux casa (compartido)
- Cualquier navegador autenticado

Cada uno identificado por JWT con `sub: angel` o `sub: africa` (mismo sistema de tokens que el 001).

## 2. Dependencias del proyecto 001

Este proyecto SOLO arranca cuando 001 esté en producción con:
- Vault pool común multi-usuario funcionando (`knowledge_base/dia/` con metadata autor)
- Tools MCP `dia_capturar`, `dia_contexto`, `dia_buscar` expuestos
- Sistema de tokens JWT operativo
- Speaker ID Linux casa funcionando

Si 001 no está en producción, 002 no se inicia.

## 3. Componentes del dashboard

Ordenados por prioridad de implementación:

### Fase A — MVP (semana 1)
- **Timeline mezclado** Angel + África, ordenado por fecha desc
- **Filtros**: por autor, por etiqueta (`trabajo|nosvers|familia|mental|idea|otro`), por rango de fechas
- **Búsqueda full-text** sobre el vault (reusa `dia_buscar` del MCP)
- **Vista detalle nota**: clic en una entrada abre el `.md` con render markdown
- **Solo lectura**

### Fase B — Acción rápida (semana 2-3)
- **Capturar nota por texto** desde el navegador (cuando no quieras hablar) → llama a `dia_capturar` del MCP
- **Estado de la infra** en vivo: VPS health, AEGIS/ALAMO, cron status, Stripe, WordPress, freqtrade
- **Lanzar un agente del unified-agent** con un clic (agt05_africa, agt_eisenia, etc.)
- **Calendario integrado** (Google Calendar via conector ya activo) — vista lateral
- **Gmail integrado** (mismo) — bandeja prioritaria
- **Editar/borrar notas** del vault

### Fase C — Vistas avanzadas (mes 2)
- **Kanban proyectos NosVers**: tarjetas leídas desde `knowledge_base/proyectos/*.md`, drag-and-drop para mover entre columnas (To do / Doing / Done)
- **Grafo de conexiones** entre notas: si una nota referencia a otra con `[[link]]` estilo Obsidian, mostrar el grafo. Decisión a tomar en `/speckit-plan` del 002: ¿construir grafo propio con D3.js, o iframe a Obsidian Publish?
- **Estadísticas**: notas por autor por semana, etiquetas dominantes, productividad NosVers

### Fase D — Automatizaciones (mes 3+)
- **Triggers visuales** estilo n8n light: "si llega email de Y → ejecuta agente Z → notifica Telegram"
- Reglas almacenadas en `knowledge_base/automatizaciones/*.yaml`
- Ejecutor: extender `unified-agent`

## 4. Stack candidato (decidir en /speckit-plan del 002)

- **Frontend**: React + Vite + TailwindCSS + shadcn/ui. D3.js para grafo. react-beautiful-dnd para kanban.
- **Backend**: FastAPI (lo mismo que el MCP nosvers, ya estás familiarizado). Endpoints REST `GET /tablero/*` y `POST /tablero/*`. Reutiliza módulos `voz/*` del 001.
- **Auth**: mismos tokens JWT que el 001 (`sub: angel|africa`). Renovación silenciosa con refresh tokens.
- **Hosting**: subdominio `tablero.nosvers.com` o `panel.nosvers.com`. Nginx → FastAPI → archivos estáticos React.
- **WebSocket** para actualizaciones en tiempo real (cuando Angel captura una nota en el móvil, África lo ve en su navegador al instante).

## 5. Constraints

Mismas que el 001:
- Soberanía: nada propietario donde haya alternativa local
- MCP-first: la lógica vive en tools del MCP, el dashboard solo orquesta
- Vault es source of truth (lee/escribe `.md`, no BBDD paralela)
- No regresión

## 6. Definition of done para la Fase A (MVP)

- Angel abre `tablero.nosvers.com` desde el móvil, ve timeline con sus notas y las de África mezcladas
- Filtros funcionan
- Búsqueda funciona
- Vista detalle abre la nota
- Latencia de carga inicial < 2s sobre 4G

Hasta aquí es la primera entrega. El resto se construye encima.

## 7. Cuándo arrancar

**Cuando el proyecto 001 esté validado y en producción** — no antes. Si arrancamos en paralelo, los componentes del 002 que dependen del refactor multi-usuario del 001 quedan rotos.

---

*Brief escrito por Claude Opus 4.7 (sesión móvil) tras decisión arquitectónica de Angel, 2026-05-13 06:00 UTC*
 — eventos próximos en el timeline
- **Editar nota** existente: corregir transcripción de voz mal interpretada

### Fase C — Kanban proyectos NosVers (mes 2)
- **Tablero kanban** estilo Trello con columnas custom (Idea → En curso → Bloqueado → Hecho)
- **Tarjetas** son notas con etiqueta `[proyecto:X]` en su frontmatter; drag-and-drop actualiza el frontmatter
- **Proyectos NosVers** preconfigurados: monetización, contenido instagram, huerto, infra, sol-vivant
- **Asignación a Angel/África** opcional por tarjeta

### Fase D — Grafo y automatizaciones (mes 2-3)
- **Vista grafo** de conexiones entre notas (nodos = notas, aristas = `[[wikilinks]]` o tags compartidos)
- Decidir en `/speckit-plan` 002: integrar Obsidian Publish (gratis si tiene cuenta) vs grafo propio con D3
- **Automatizaciones visuales** light: trigger ("nota con etiqueta X creada") → acción ("ejecutar agente Y" / "notificar Telegram" / "crear evento calendario"). Estilo n8n simplificado.

## 4. Stack candidato

A validar en `/speckit-plan` 002:

- **Frontend**: React 18 + Vite + TypeScript + Tailwind + shadcn/ui (consistente con frontend-design skill de Anthropic)
- **Grafo**: D3 force-directed o react-force-graph
- **Kanban**: dnd-kit (más mantenido que react-beautiful-dnd)
- **Markdown render**: react-markdown + remark-gfm + rehype-highlight
- **Backend**: extiende el MCP server existente con endpoints REST adicionales en `voz/rest.py` (o módulo nuevo `dashboard/rest.py`). FastAPI.
- **Realtime**: Server-Sent Events para timeline (más simple que WebSockets, suficiente)
- **Auth**: JWT compartido con 001 (mismo `voz/auth.py`)

## 5. Hosting y deployment

- Subdominio: `tablero.nosvers.com` (registro DNS A apuntando al VPS)
- Servido por nginx con HTTPS Let's Encrypt
- Build estático: el frontend compila a `dist/` y nginx lo sirve; las llamadas `/api/*` se proxean al backend en localhost
- Repositorio: `/home/nosvers/dashboard/` con `dashboard/frontend/` (React) y `dashboard/backend/` (FastAPI extensions)

## 6. Constraints (heredados del 001)

- **Soberanía**: nada de servicios cloud propietarios para hosting. Todo en el VPS de NosVers.
- **MCP-first**: el dashboard CONSUME los tools MCP existentes; cualquier funcionalidad nueva se expone como tool antes de implementarse en el dashboard.
- **Vault como source of truth**: el dashboard NO tiene base de datos propia. Lee directo de `knowledge_base/`. Cualquier escritura va a markdown.
- **Sin frameworks pesados**: NO Next.js, NO Remix; Vite + React es suficiente.
- **Accesible offline parcialmente**: PWA install opcional, cache de últimas 30 notas en IndexedDB.

## 7. Plan temporal

- **Pre-condición**: 001 en producción y validado por Angel
- **Fase A (semana 1)**: MVP lectura → primer entregable usable
- **Fase B (semana 2-3)**: acción rápida → reemplaza el 70% del uso de app Claude móvil
- **Fase C (mes 2)**: kanban → soporte real para gestionar NosVers
- **Fase D (mes 2-3)**: grafo + automatizaciones → second brain completo
- **Total estimado**: 10-12 semanas con ritmo sostenible

## 8. Definition of done para Fase A (MVP)

- Angel y África pueden abrir `https://tablero.nosvers.com` y autenticarse con su token
- El timeline muestra notas de los últimos 30 días de ambos, mezcladas
- Los filtros por autor/etiqueta/fecha funcionan sin recargar página
- La búsqueda full-text devuelve resultados en <500ms
- Vista detalle de cualquier nota renderiza markdown correctamente
- Cero regresión sobre 001 (las PWAs, el voz Linux casa, el agt07_diario siguen funcionando)

## 9. Flujo Spec Kit a seguir

1. `/speckit-constitution` con principios heredados del 001 + "lectura es king, escritura siempre vía MCP, vault es la única verdad"
2. `/speckit-specify` con el alcance de Fase A solamente (no atacar todo a la vez)
3. `/speckit-clarify` para validar elecciones de stack
4. `/speckit-plan` para Fase A
5. `/speckit-tasks` desglose
6. `/speckit-implement` Fase A
7. STOP, validación Angel, después Fase B con nueva spec

---
*BRIEF 002 iniciado por Claude Code en VPS (06:01 UTC) y completado por Claude Opus 4.7 móvil (06:05 UTC), 2026-05-13. NO arrancar hasta que 001 esté en producción.*
