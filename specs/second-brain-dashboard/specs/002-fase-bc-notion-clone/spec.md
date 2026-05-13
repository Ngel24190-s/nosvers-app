# Feature Specification: Second Brain Dashboard — Fase B+C (Notion-clone real)

**Feature Branch**: `002-fase-bc-notion-clone` (subproject is not its own git repo; staying on parent monorepo `main`, mismo convenio que Fase A)

**Created**: 2026-05-13

**Status**: Draft

**Input**: User description: "Fase B+C combinada del Second Brain Dashboard NosVers (proyecto 002), continuación directa de Fase A (commit 683a410). Construye experiencia Notion-clone real sobre el timeline ya existente, mezclando interactividad (B) y riqueza visual (C). 14 sub-componentes: 1) captura por texto desde el navegador (Ctrl+N → MCP dia_capturar); 2) editar nota in-place; 3) borrar nota con confirmación (soft delete); 4) estado infra en vivo en sidebar; 5) lanzar agente del unified-agent con un clic; 6) calendario Google integrado; 7) Gmail integrado bandeja prioritaria; 8) vistas múltiples sobre el timeline; 9) kanban proyectos NosVers (knowledge_base/proyectos/*.md); 10) wiki-links bidireccionales [[nota]]; 11) grafo de conexiones; 12) sidebar tipo Notion (árbol del vault); 13) statistics widget; 14) búsqueda global Ctrl+K command palette. Constraints: soberanía tecnológica, MCP-first, vault source of truth, NO romper Fase A, vault permanece markdown puro, JWT sub angel|africa con paridad."

## User Scenarios & Testing *(mandatory)*

<!--
  Las 14 historias derivan directamente de los 14 sub-componentes del brief.
  Cada una es independientemente testeable: implementada en aislamiento, sigue
  aportando valor sobre la línea de base de Fase A. Las prioridades reflejan
  el orden en que Angel y África empezarían a notar la diferencia entre
  "timeline bonito" y "Notion-clone real".
-->

### User Story 1 — Captura de nota por texto desde el navegador (Priority: P1)

Angel está en su Linux casa, abre el dashboard, y mientras lee el timeline le viene una idea sobre la fermentación del LombriThé. Sin cambiar de pestaña ni abrir la PWA voz, pulsa `Ctrl+N`, escribe la idea en un input flotante (con etiquetas opcionales y autor pre-rellenado a partir de su JWT) y la guarda. La nueva nota aparece arriba del timeline al instante. África, autenticada como `africa`, hace lo mismo desde su móvil y su nota se asocia automáticamente a su autor sin que tenga que escoger ningún desplegable.

**Why this priority**: Sin captura, el dashboard sigue siendo "biblioteca de notas ajenas". Esta historia es la que convierte el tablero en herramienta de trabajo activa y desbloquea casi todas las demás (editar, kanban, búsqueda global, etc. operan sobre notas que primero hay que crear). Es la frontera entre "Fase A bonita" y "Notion-clone real".

**Independent Test**: Con un JWT válido, abrir el dashboard, pulsar `Ctrl+N`, escribir "test captura nosvers" + etiqueta `idea`, pulsar guardar, ver la nota en el timeline en ≤ 1 s, y verificar que `knowledge_base/dia/<fecha>-<slug>.md` existe en el vault con `autor: angel` (o `autor: africa` si autenticó como ella) y frontmatter consistente.

**Acceptance Scenarios**:

1. **Given** un usuario autenticado con `sub: angel`, **When** pulsa `Ctrl+N`, rellena título y cuerpo, selecciona etiquetas `idea, nosvers` y guarda, **Then** se crea un archivo `.md` en `knowledge_base/dia/` con `autor: angel`, `fecha` del día actual, las etiquetas elegidas, y la nueva entrada aparece arriba del timeline sin recargar la página.
2. **Given** un usuario autenticado con `sub: africa`, **When** captura una nota desde móvil con la misma acción, **Then** la nota se guarda con `autor: africa` automáticamente, sin que el usuario haya tenido que elegir el autor en ningún momento (se infiere del JWT, no de un selector).
3. **Given** una captura sin título explícito, **When** se guarda, **Then** el sistema genera un slug a partir de la primera línea significativa del cuerpo y un título sensato; la nota es válida y aparece en el timeline.
4. **Given** un usuario sin JWT o con JWT inválido, **When** intenta enviar la captura, **Then** la petición es rechazada con 401 y la UI lo lleva al flujo de relogin sin perder el borrador.
5. **Given** el modal de captura abierto, **When** el usuario pulsa `Esc` o clic fuera, **Then** se cierra preservando el borrador en localStorage para reabrirlo intacto en la próxima invocación del atajo.

---

### User Story 2 — Editar nota in-place con preview markdown (Priority: P1)

África ha capturado por voz una nota sobre el composteur, pero la transcripción interpretó "Eisenia fetida" como "Eugenia fétida". Hace clic en la nota del timeline, ve el detalle markdown, pulsa el botón "Editar" y entra un editor con dos paneles (markdown source y preview en vivo). Corrige el nombre, pulsa guardar, el archivo `.md` del vault se reescribe atómicamente, el timeline refresca esa entrada y el `modified_at` del frontmatter se actualiza al instante.

**Why this priority**: La calidad del conocimiento depende de poder corregir errores rápido. Si Angel y África no pueden editar las notas mal transcritas, el vault se llena de ruido y dejan de confiar en la búsqueda. Esto se hace P1 porque sin él la captura (US1) se vuelve frustrante en cuanto aparece la primera errata.

**Independent Test**: Abrir cualquier nota del timeline, pulsar editar, cambiar una palabra, guardar; volver a abrir la nota y comprobar que el cambio persiste y que el archivo en `knowledge_base/dia/` ha sido reescrito (mtime más reciente). Comprobar que el cuerpo del archivo conserva el frontmatter intacto excepto el campo `modified_at` que se actualiza.

**Acceptance Scenarios**:

1. **Given** una nota existente con frontmatter `autor: angel` + etiquetas, **When** Angel la edita y guarda, **Then** el archivo `.md` se reescribe preservando todos los campos del frontmatter, actualizando solo `modified_at`, y la entrada del timeline refleja el nuevo contenido sin recargar.
2. **Given** el editor abierto con cambios sin guardar, **When** el usuario pulsa "cancelar", **Then** el sistema pide confirmación explícita ("descartar cambios?") antes de cerrar el editor.
3. **Given** dos pestañas abiertas sobre la misma nota en diferentes navegadores, **When** ambas envían un guardado con `modified_at` distinto del que ya está en disco, **Then** el segundo guardado recibe HTTP 409 Conflict y la UI propone "recargar y volver a aplicar mis cambios" en vez de pisar silenciosamente al otro autor.
4. **Given** el preview en vivo, **When** el usuario teclea, **Then** el preview se actualiza con debounce ≤ 250 ms y renderiza la misma sintaxis markdown que la vista detalle (encabezados, listas, código, imágenes, wiki-links).
5. **Given** una nota cuyo autor del frontmatter no coincide con el `sub` del JWT (p.ej. Angel intenta editar una nota de África), **When** envía el guardado, **Then** la petición es aceptada (paridad de acceso entre Angel y África) pero queda registrada en el log con `editor != autor` para trazabilidad.

---

### User Story 3 — Borrar nota con soft delete (Priority: P2)

Angel se da cuenta de que una nota es un duplicado de otra. Hace clic en el menú "..." de la entrada, elige "Archivar", confirma con un diálogo ("¿seguro? la nota se moverá a `dia/archivo/`"), opcionalmente escribe una razón ("duplicado de 2026-05-10"), y la nota desaparece del timeline. Si más tarde necesita recuperarla, abre la vista "Papelera" en el sidebar, ve la nota archivada, y la restaura con un clic.

**Why this priority**: El borrado real es destructivo y los vaults rara vez tienen UNDO. El soft delete protege contra arrepentimientos sin pedirle a Angel que entienda git. No es P1 porque los duplicados son tolerables a corto plazo, pero sí necesario antes de que el vault crezca lo suficiente para que el ruido moleste.

**Independent Test**: Crear una nota, archivarla, comprobar que ya no aparece en el timeline ni en búsquedas por defecto, abrir "Papelera", restaurarla, comprobar que reaparece en el timeline con su contenido intacto y su ruta original. Comprobar también que el archivo `.md` está físicamente en `knowledge_base/dia/archivo/` durante el archivado.

**Acceptance Scenarios**:

1. **Given** una nota visible en el timeline, **When** el usuario la archiva confirmando, **Then** el archivo se mueve a `knowledge_base/dia/archivo/<fecha>-<slug>.md`, se añade al frontmatter `archived_at: <iso>` y `archive_reason: "<texto opcional>"`, y la entrada desaparece del timeline y de los resultados de búsqueda por defecto.
2. **Given** la vista "Papelera" en el sidebar, **When** el usuario la abre, **Then** ve la lista de notas archivadas ordenadas por `archived_at` descendente, con razón y autor visibles.
3. **Given** una nota archivada, **When** se restaura, **Then** el archivo vuelve a su carpeta original (`knowledge_base/dia/`), los campos `archived_at` y `archive_reason` se eliminan del frontmatter, y la nota reaparece en el timeline.
4. **Given** un intento de archivar sin confirmar el diálogo, **When** el usuario pulsa "cancelar" en el modal, **Then** no se hace ninguna modificación al vault.

---

### User Story 4 — Vistas múltiples sobre el timeline (Priority: P1)

África quiere repasar lo que han escrito esta semana sobre `nosvers`. En la cabecera del timeline ve un selector con cinco vistas: Lista (actual), Tabla, Kanban por etiqueta, Calendario mensual y Galería de cards. Cambia a "Tabla" y aparece una vista con columnas filtrables (fecha, autor, etiquetas, primera línea). Cambia a "Kanban por etiqueta" y ve cinco columnas (`trabajo`, `nosvers`, `familia`, `mental`, `idea`, `otro`) con las notas como tarjetas. Cambia a "Calendario" y ve un mes con puntos en los días con notas. Cambia a "Galería" y ve cards con thumbnail si la nota tiene imagen. Los filtros activos (autor, etiqueta, rango fechas) se mantienen al cambiar de vista.

**Why this priority**: Esta es la diferencia visible más fuerte entre Fase A y B+C. Sin vistas múltiples, el dashboard es "Twitter cronológico"; con ellas, es "Notion". Es la historia que vuelve verosímil el resto.

**Independent Test**: Con un timeline de >20 notas, cambiar a cada una de las 5 vistas y comprobar (a) que la transición es ≤ 200 ms, (b) que los filtros aplicados se preservan, (c) que cada vista respeta los filtros y muestra los mismos N elementos.

**Acceptance Scenarios**:

1. **Given** el timeline con 30 notas y filtro `autor: africa + etiqueta: nosvers` activo, **When** el usuario cambia a vista "Tabla", **Then** ve esas mismas N notas en formato de tabla con columnas (fecha, autor, etiquetas, primera línea) ordenables por columna.
2. **Given** la vista "Kanban por etiqueta", **When** se renderiza, **Then** hay 6 columnas (una por etiqueta fija + "sin etiqueta"), cada nota aparece en la columna correspondiente a su primera etiqueta, y las notas multi-etiqueta aparecen replicadas (con badge visual indicando "1 de 2").
3. **Given** la vista "Calendario mensual", **When** se renderiza, **Then** muestra el mes actual con un círculo (o número) en cada día con notas; clic en un día filtra el timeline a esa fecha.
4. **Given** la vista "Galería", **When** la nota referencia una imagen (`![](attachments/...)`), **Then** la card muestra esa imagen como thumbnail; si no hay imagen, muestra un placeholder con la primera línea del cuerpo.
5. **Given** el usuario en cualquier vista, **When** recarga la página, **Then** la vista que tenía activa se restaura desde localStorage (preferencia persistente por usuario en el navegador).

---

### User Story 5 — Búsqueda global Ctrl+K estilo command palette (Priority: P1)

Angel pulsa `Ctrl+K` desde cualquier pantalla del dashboard. Aparece una paleta de comandos centrada estilo Notion/Linear/VS Code. Empieza a teclear: "lombri" — aparecen resultados agrupados en secciones: "Notas" (las 3 notas más recientes con ese término), "Proyectos" (proyectos NosVers que mencionan lombri), y "Acciones" (botones que disparan agentes o vistas). Pulsa flecha abajo, Enter, salta directamente a la nota seleccionada. Cierra la paleta con `Esc` sin tocar el ratón.

**Why this priority**: Con un vault de cientos de notas, navegar a una específica desde el timeline es lento. La paleta Ctrl+K es el patrón estándar para acceso rápido a cualquier objeto del sistema. Es la herramienta que convierte el dashboard en "el sitio donde encuentro cosas rápido", al nivel de Obsidian.

**Independent Test**: Pulsar `Ctrl+K` en cualquier vista, comprobar que la paleta abre en ≤ 100 ms, teclear un término conocido y ver resultados en ≤ 300 ms, navegar con flechas, pulsar Enter, comprobar que salta correctamente al objeto seleccionado. Comprobar que `Esc` cierra sin efecto colateral.

**Acceptance Scenarios**:

1. **Given** cualquier vista del dashboard, **When** el usuario pulsa `Ctrl+K` (o `Cmd+K` en macOS), **Then** se abre una paleta de comandos centrada con un input enfocado y una lista vacía hasta que el usuario teclee.
2. **Given** la paleta abierta con el query "lombri", **When** se actualiza el resultado, **Then** se muestran como máximo 5 ítems por sección (Notas / Proyectos / Acciones), agrupados visualmente con un encabezado de sección.
3. **Given** la paleta con resultados, **When** el usuario presiona flecha abajo y luego Enter, **Then** navega al objeto correspondiente (vista detalle de nota, vista kanban del proyecto, o ejecuta la acción) sin requerir clic.
4. **Given** la paleta abierta, **When** el usuario pulsa `Esc`, **Then** se cierra sin modificar la vista previa ni los filtros.
5. **Given** una query sin coincidencias, **When** se actualiza el resultado, **Then** la paleta muestra "sin resultados — ¿quieres capturar una nueva nota?" con un atajo directo a US1.

---

### User Story 6 — Kanban de proyectos NosVers con drag-and-drop (Priority: P2)

Angel quiere ver el estado de los proyectos NosVers (monetización, contenido, huerto, etc.). Abre el sidebar, pincha en "Proyectos" y entra una vista kanban con 4 columnas fijas: `todo`, `doing`, `done`, `blocked`. Cada tarjeta es un archivo `knowledge_base/proyectos/<slug>.md` con frontmatter `estado: <columna>`. Angel arrastra "Tienda Lemon Squeezy" de `todo` a `doing`; al soltar, el frontmatter del archivo se actualiza y un toast confirma "estado actualizado a doing". Si la carpeta `proyectos/` no existe, el dashboard la crea al primer acceso con un proyecto de bienvenida que explica el formato.

**Why this priority**: El kanban es el segundo gran patrón Notion-clone y desbloquea la gestión visible de proyectos sin depender de Trello/Linear externos. No es P1 porque puede sobrevivir un par de semanas usando notas con etiqueta `[proyecto:X]` (compatible con US4 Kanban por etiqueta).

**Independent Test**: Crear `knowledge_base/proyectos/test.md` con `estado: todo`, abrir la vista kanban, arrastrar la tarjeta a "doing", comprobar que el frontmatter del archivo se actualizó a `estado: doing`, recargar la página y verificar que la tarjeta persiste en la columna correcta.

**Acceptance Scenarios**:

1. **Given** la carpeta `knowledge_base/proyectos/` con 5 archivos en estados variados, **When** Angel abre la vista kanban, **Then** ve 4 columnas con las tarjetas correctamente clasificadas según el campo `estado` de cada frontmatter.
2. **Given** una tarjeta en `todo`, **When** el usuario la arrastra a `done`, **Then** el frontmatter del archivo `.md` se actualiza a `estado: done`, el archivo se reescribe atómicamente, y la UI muestra confirmación.
3. **Given** la carpeta `knowledge_base/proyectos/` inexistente, **When** un usuario abre la vista kanban por primera vez, **Then** el dashboard la crea con un archivo `bienvenida.md` que explica cómo crear proyectos (formato frontmatter, estados válidos), y el usuario ve esa tarjeta en `todo`.
4. **Given** un drag-and-drop en móvil, **When** el usuario hace long-press sobre una tarjeta y la arrastra, **Then** el reordenamiento funciona idéntico que en escritorio; alternativamente un menú "..." en cada tarjeta permite cambiar estado por selección.
5. **Given** un frontmatter con `estado` inválido (p.ej. `estado: xyz`), **When** la vista kanban se carga, **Then** la tarjeta aparece en una columna "sin estado" (5ª columna implícita) con badge de advertencia, en lugar de romper la vista.

---

### User Story 7 — Wiki-links bidireccionales [[nota]] con backlinks (Priority: P2)

Mientras edita una nota sobre `composteur`, África teclea `[[lombrithé]]` y guarda. El render markdown muestra el enlace como clicable (sintaxis tipo Obsidian). Cuando luego abre la nota `lombrithé.md`, ve al pie una sección "Referenciada desde" con la nota composteur. Los backlinks se actualizan automáticamente cada vez que una nota es creada, editada o archivada.

**Why this priority**: Los wiki-links son el corazón del sistema Obsidian que África y Angel usan. Sin ellos, el dashboard es un visualizador de notas planas y obliga a abrir Obsidian para "ver las conexiones". Con ellos, el dashboard sustituye a Obsidian para el uso cotidiano. No es P1 porque US1 + US4 + US5 ya dan ~70% del valor; los wiki-links son acelerador, no funcional crítico.

**Independent Test**: Crear nota A con cuerpo `[[B]]`, crear nota B vacía, abrir B, comprobar que el panel "Referenciada desde" lista A. Archivar A, recargar B, comprobar que A ya no aparece. Restaurar A, comprobar que vuelve.

**Acceptance Scenarios**:

1. **Given** una nota cuyo cuerpo contiene `[[lombrithé]]`, **When** se renderiza en la vista detalle, **Then** el texto aparece como hipervínculo clicable que abre la nota `lombrithé.md` si existe, o muestra "nota no creada — ¿crear?" si no existe.
2. **Given** la nota destino `lombrithé.md` abierta, **When** se renderiza la vista detalle, **Then** al pie aparece una sección "Referenciada desde" con la lista de notas que la apuntan (chip de autor + fecha + snippet del contexto del enlace).
3. **Given** una nota A con `[[B]]`, **When** A es archivada, **Then** la nota B ya no muestra A en su lista de backlinks (en ≤ 1 s tras el archivado o al próximo refresh).
4. **Given** un wiki-link a una nota inexistente (`[[ideas-2027]]`), **When** se renderiza, **Then** el enlace aparece visualmente distinto (color/subrayado discreto) y al hacer clic abre el flujo de US1 con el título prerrellenado.
5. **Given** la resolución del enlace, **When** existen múltiples notas con el mismo slug, **Then** se elige la más reciente y se indica con un tooltip que hay homónimos (sin romper el render).

---

### User Story 8 — Sidebar tipo Notion: árbol de navegación del vault (Priority: P2)

Angel abre el dashboard y ve, a la izquierda, un sidebar colapsable que muestra la jerarquía completa del vault: `knowledge_base/` raíz, y debajo `dia/`, `proyectos/`, `contexto/`, `operaciones/`, etc. Cada carpeta es expandible. Al hacer clic en una carpeta o nota, el contenido se carga en la parte principal. Para reorganizar (raro pero útil), arrastra una nota desde `dia/` a una subcarpeta nueva `dia/archivadas-2025/` que crea con el botón "+". Al soltar, el archivo se mueve físicamente en el vault.

**Why this priority**: El árbol del vault es lo que diferencia "dashboard de notas" de "explorador de conocimiento". Sin él, Angel sigue dependiendo de Obsidian para ver la estructura. No es P1 porque el timeline + búsqueda global cubren ~80% de la navegación; el árbol es para la reorganización ocasional.

**Independent Test**: Abrir el sidebar, expandir varias carpetas y comprobar que muestran su contenido real del vault. Arrastrar una nota de prueba a otra carpeta y comprobar que el archivo se ha movido físicamente (ruta nueva, ruta antigua ausente).

**Acceptance Scenarios**:

1. **Given** la estructura real de `knowledge_base/`, **When** el usuario abre el sidebar, **Then** ve un árbol jerárquico expandible con las mismas carpetas y archivos que existen en disco.
2. **Given** una carpeta colapsada, **When** el usuario la expande, **Then** se cargan sus contenidos directos (no recursivos) en ≤ 200 ms.
3. **Given** una nota arrastrada desde `dia/` a `proyectos/`, **When** se suelta, **Then** el archivo se mueve físicamente en disco, los wiki-links que la apuntan siguen funcionando (resolución por slug, no por ruta), y la UI refresca el árbol y el timeline.
4. **Given** el sidebar abierto, **When** el usuario crea una carpeta nueva con el botón "+" + nombre, **Then** la carpeta se crea en disco (`mkdir`) y aparece en el árbol sin recargar.
5. **Given** el sidebar en móvil < 768px, **When** se renderiza, **Then** se comporta como un drawer (oculto por defecto, abre con un botón hamburguesa, cierra al elegir un nodo) en lugar de columna fija.

---

### User Story 9 — Statistics widget: actividad por autor y etiquetas dominantes (Priority: P3)

África quiere saber cuántas notas ha escrito esta semana comparada con Angel. Abre el dashboard, en una zona discreta del top o en una página "Stats" del sidebar ve un widget con: (a) barras horizontales "notas por autor esta semana" (Angel: 12 / África: 8), (b) chips de etiquetas dominantes ordenadas por frecuencia esta semana (`nosvers ×11, trabajo ×6, idea ×4, ...`), (c) un mini-sparkline de "notas totales por día los últimos 30 días". Las cifras se actualizan en cada carga; no requieren WebSocket.

**Why this priority**: Los stats son útiles pero no críticos. P3 porque el valor diario marginal sobre US1-8 es bajo; sí aporta una métrica motivacional ("estamos escribiendo") sin la cual los stats del vault solo existen en el conteo manual de Obsidian.

**Independent Test**: Capturar 5 notas de Angel + 3 de África en una semana, abrir el widget, comprobar que las barras muestran (5, 3); cambiar el rango al mes y comprobar consistencia con el conteo real.

**Acceptance Scenarios**:

1. **Given** N notas en el vault con autores y fechas variados, **When** se carga el widget, **Then** muestra el conteo correcto de notas por autor para la semana corriente.
2. **Given** las notas semanales, **When** se calculan etiquetas dominantes, **Then** aparecen las top-10 etiquetas ordenadas por frecuencia descendente con su conteo numérico.
3. **Given** el sparkline de 30 días, **When** se renderiza, **Then** cada barra del sparkline corresponde a un día con su conteo de notas (incluyendo días con 0).
4. **Given** un usuario sin notas en la semana actual, **When** abre el widget, **Then** ve un estado vacío explicativo en lugar de un gráfico vacío que parezca roto.

---

### User Story 10 — Estado de la infra en vivo en sidebar (Priority: P3)

Angel quiere saber de un vistazo si todo está operativo. En el sidebar lateral colapsable hay una sección "Infra" con badges: ✅ VPS (uptime + load), ✅ WordPress online, ⚠️ Stripe revenue del día (€42), ✅ AEGIS/ALAMO último briefing (hace 2 h), ⚠️ cron job `agt05_africa` retrasado, ❌ freqtrade PnL -1.2%. Pinchando en un badge ve el detalle correspondiente (logs, último output, link a Grafana, etc.).

**Why this priority**: Visibilidad operacional importa, pero Angel ya recibe alertas por Telegram cuando algo se rompe. Este widget es complementario: vista de calma cuando todo va bien, no canal de alerta primario. Por eso P3, no P1.

**Independent Test**: Apagar manualmente un servicio (p.ej. parar el contenedor de WordPress en dev), recargar el dashboard y comprobar que el badge correspondiente se pone en ❌. Reanudar el servicio y comprobar que vuelve a ✅ en el próximo refresh (≤ 60 s).

**Acceptance Scenarios**:

1. **Given** todos los servicios up, **When** Angel abre el sidebar de infra, **Then** los 6 badges (VPS, WP, Stripe, AEGIS, cron, freqtrade) están en verde con su valor actual.
2. **Given** un servicio caído, **When** el dashboard hace polling (≤ 60 s), **Then** el badge correspondiente pasa a rojo con detalle ("conexión rechazada", "timeout", etc.) y se ofrece un botón "ver logs".
3. **Given** un valor que requiere lookup externo (Stripe revenue), **When** se carga, **Then** el dato se obtiene en ≤ 2 s; si falla, el badge se pone en gris con "sin datos" sin bloquear el resto del sidebar.

---

### User Story 11 — Lanzar un agente del unified-agent con un clic (Priority: P3)

Angel quiere disparar `agt05_africa` manualmente porque África acaba de responder un email importante y no quiere esperar al cron de las 18h. En el sidebar de infra, sección "Agentes", ve botones para los principales (`agt05_africa`, `agt_eisenia`, `agt07_diario`, `orchestrator`, etc.). Pulsa "ejecutar agt05_africa", aparece un spinner, y a los pocos segundos ve el output completo del agente en un panel lateral (mismo formato que `agente_logs` del MCP).

**Why this priority**: Útil pero replicable desde la CLI o el bot Telegram. Sin esto, Angel sigue pudiendo lanzarlos por otros canales. Por eso P3.

**Independent Test**: Pulsar el botón "ejecutar agt07_diario", esperar a que termine, comprobar que el output mostrado coincide con el de la herramienta MCP `agente_ejecutar` ejecutada manualmente.

**Acceptance Scenarios**:

1. **Given** la lista de botones de agentes, **When** Angel pulsa uno, **Then** se invoca la tool MCP `agente_ejecutar` con el slug correcto y se muestra un spinner hasta recibir respuesta.
2. **Given** un agente que tarda > 30 s, **When** llega al timeout configurado, **Then** la UI muestra "ejecución abortada — revisa logs" sin colgarse, consistente con el patrón conocido de `MCP_STALL_*` documentado en project memory.
3. **Given** un usuario `sub: africa`, **When** intenta ejecutar un agente, **Then** funciona igual que para Angel (paridad de acceso), pero el log registra `triggered_by: africa` para trazabilidad.

---

### User Story 12 — Grafo de conexiones entre notas (Priority: P3)

África abre la página "Grafo" en el sidebar. Ve un canvas con cientos de puntos (notas) conectados por líneas (wiki-links). Los nodos están coloreados por etiqueta dominante; los hubs (notas más referenciadas) son más grandes. Pasa el ratón sobre un punto y aparece un mini-tooltip con título + autor + primera línea. Hace clic, va a la vista detalle. Zoom y pan con la rueda y arrastre.

**Why this priority**: El grafo es el componente más "lujo Notion/Obsidian" pero el menos crítico para uso diario. Es la cereza, no el pastel. P3 confirmado.

**Independent Test**: Con ≥ 20 notas con wiki-links, abrir la vista grafo, comprobar que los nodos están conectados según los links reales, hacer hover sobre uno y verificar tooltip.

**Acceptance Scenarios**:

1. **Given** ≥ 20 notas con al menos 10 wiki-links totales, **When** se carga la vista grafo, **Then** el render inicial completa en ≤ 2 s y los nodos se distribuyen mediante simulación d3-force estable.
2. **Given** el grafo cargado, **When** el usuario pasa el ratón sobre un nodo, **Then** aparece un tooltip con título + autor + primera línea de la nota; clic abre la vista detalle.
3. **Given** un vault grande (≥ 500 notas), **When** se carga el grafo, **Then** el sistema aplica un sampling razonable (top-N por conexiones) o un nivel de zoom inicial conservador para evitar congelar el navegador móvil; se muestra contador "1234 notas, mostrando 500 principales".
4. **Given** el grafo en móvil, **When** se renderiza, **Then** la UX es usable (pinch-to-zoom, tap para abrir nota); si no rinde aceptablemente, se ofrece un fallback "abrir en escritorio".

---

### User Story 13 — Calendario Google integrado (vista lateral colapsable) (Priority: P3)

Angel abre el sidebar y expande "Calendario". Ve sus próximos 7 días con eventos sincronizados desde Google Calendar (vía el conector ya activo en `mcp__claude_ai_Google_Calendar__*`). Cada evento muestra título, hora y duración. Hace clic en uno, se abre un panel con detalles + link directo a calendar.google.com para edición avanzada. Si quiere crear un evento desde el dashboard, pulsa "+ Evento", rellena título + fecha + duración y al guardar el evento aparece tanto en GCal como en el sidebar.

**Why this priority**: El calendario es útil pero ortogonal al dashboard como "second brain". Angel ya tiene su Google Calendar accesible. Integrarlo es comodidad, no necesidad. P3.

**Independent Test**: Con al menos un evento en GCal, abrir el sidebar de calendario y comprobar que aparece con título y hora correctos. Crear uno desde el dashboard y comprobar que llega a GCal real.

**Acceptance Scenarios**:

1. **Given** el conector Google Calendar autenticado, **When** Angel abre el panel calendario, **Then** ve sus eventos de los próximos 7 días naturales con título, hora inicio, duración y calendario origen.
2. **Given** un evento clicado, **When** se abre el detalle, **Then** muestra descripción, asistentes, link a Meet si lo tiene, y botón "abrir en Google Calendar".
3. **Given** un evento nuevo creado desde el dashboard, **When** se envía, **Then** se llama al endpoint del conector y se confirma que el evento aparece en el sidebar tras refrescar (≤ 5 s).
4. **Given** el conector no autenticado o expirado, **When** Angel abre el panel, **Then** ve un CTA "conectar Google" con instrucciones, sin romper el resto del dashboard.

---

### User Story 14 — Gmail bandeja prioritaria (Priority: P3)

Angel abre el sidebar y expande "Gmail". Ve una lista de hilos prioritarios filtrados por el query Gmail `is:starred OR label:Lectura/Tech OR from:noreply@anthropic.com`. Cada hilo muestra remitente, asunto, snippet y fecha. Clic abre el hilo completo en un panel lateral con el cuerpo del último mensaje renderizado (HTML→texto saneado). Botón "responder" abre Gmail web en pestaña nueva.

**Why this priority**: Igual que el calendario — comodidad sobre necesidad. Gmail vive en otra pestaña ya. P3.

**Independent Test**: Con al menos 3 mensajes que cumplan el filtro, abrir el panel Gmail y comprobar que aparecen los 3 con los snippets correctos. Clic en uno → ver hilo en panel.

**Acceptance Scenarios**:

1. **Given** el conector Gmail autenticado, **When** Angel abre el panel, **Then** ve los hilos que cumplen el filtro priorizado, ordenados por fecha descendente.
2. **Given** un hilo clicado, **When** se carga el detalle, **Then** muestra el cuerpo del último mensaje renderizado de forma legible (HTML saneado o texto plano) con remitente y fecha.
3. **Given** un volumen alto de mensajes, **When** se carga el panel, **Then** se obtienen como máximo los 20 hilos más recientes que cumplen el filtro para no saturar la red.
4. **Given** el conector no autenticado, **When** Angel abre el panel, **Then** ve un CTA para autenticarse sin romper el resto del dashboard.

---

### Edge Cases

- **Vault con archivo `.md` corrupto en `dia/`**: la lectura del directorio salta el archivo problemático, lo registra en logs, y muestra una alerta discreta en el sidebar de infra ("1 nota ilegible"). No bloquea el timeline ni el grafo.
- **Guardado simultáneo de la misma nota desde Angel y África**: el primero gana; el segundo recibe HTTP 409 con detalle del conflicto y la UI ofrece "ver diff y combinar".
- **Captura con cuerpo enorme (> 1 MB)**: la captura se rechaza con error claro ("texto demasiado largo, dividirla en varias notas"). No se trunca silenciosamente.
- **Wiki-link circular `A → B → A`**: se renderizan ambos backlinks sin loop; el grafo lo muestra como ciclo.
- **Drag-and-drop de una nota archivada**: el sidebar bloquea la operación con un mensaje "restaura la nota primero".
- **Petición a Google Calendar/Gmail con conector caducado**: 401 desde el MCP; la UI muestra CTA de reconexión y no propaga el fallo al resto del dashboard.
- **Cambio de etiqueta de un proyecto desde kanban con frontmatter corrupto**: el sistema rehúsa guardar, muestra error específico ("frontmatter inválido en `proyectos/X.md`, corrige a mano") y no bloquea las otras tarjetas.
- **Estructura `knowledge_base/proyectos/` recién creada vacía**: la vista kanban muestra un onboarding ("crea tu primer proyecto") en lugar de columnas vacías.
- **Stat widget en vault nuevo (0 notas)**: muestra "empieza con `Ctrl+N`" en lugar de gráfico vacío.
- **Grafo en vault microscópico (< 5 notas, sin wiki-links)**: muestra nodos aislados con un texto guía "los wiki-links `[[nota]]` crearán conexiones aquí".
- **Reorganización drag-and-drop del sidebar que crearía colisión de nombre** (`mover A a carpeta donde ya hay A.md`): la UI detecta el conflicto antes de soltar y propone renombrar / cancelar.
- **Móvil con teclado virtual abierto durante Ctrl+K**: la paleta se ajusta para no quedar tapada por el teclado, manteniendo el input visible.
- **Búsqueda Ctrl+K con vault enorme y latencia alta**: se aplica un debounce de 250 ms y se muestra un skeleton hasta que llegan resultados.
- **Edición de una nota mientras otra pestaña la archiva**: el guardado retorna 404 "nota archivada"; la UI propone "restaurarla y guardar" o "descartar cambios".

## Requirements *(mandatory)*

### Functional Requirements

#### Captura y edición

- **FR-001**: El sistema MUST exponer un endpoint autenticado para crear notas que invoque la tool MCP `dia_capturar`, infiriendo el `autor` del claim `sub` del JWT, sin pedir al cliente que envíe el autor.
- **FR-002**: La UI MUST registrar el atajo `Ctrl+N` (`Cmd+N` en macOS) globalmente para abrir el modal de captura, sin colisionar con atajos del navegador.
- **FR-003**: El modal de captura MUST persistir el borrador en localStorage para sobrevivir cierres accidentales hasta que el usuario lo guarde o lo descarte explícitamente.
- **FR-004**: El sistema MUST exponer un endpoint autenticado para reescribir el cuerpo y/o frontmatter parcial de una nota existente, con un campo `modified_at` actualizado automáticamente.
- **FR-005**: El editor MUST mostrar simultáneamente el markdown fuente y un preview en vivo con debounce ≤ 250 ms, idéntico en sintaxis al render de la vista detalle.
- **FR-006**: El guardado de edición MUST emplear control de concurrencia optimista: si el `modified_at` enviado por el cliente no coincide con el actual en disco, MUST devolver HTTP 409 y NO sobrescribir.

#### Borrado / archivado

- **FR-007**: El sistema MUST implementar archivado lógico (soft delete) moviendo el archivo a `knowledge_base/dia/archivo/` y añadiendo `archived_at` y opcionalmente `archive_reason` al frontmatter.
- **FR-008**: Las notas archivadas MUST quedar excluidas del timeline, búsqueda y vistas múltiples por defecto, y visibles solo desde una vista explícita "Papelera".
- **FR-009**: El sistema MUST permitir restaurar una nota archivada moviendo el archivo de vuelta a su carpeta original y eliminando los campos `archived_at` y `archive_reason`.

#### Vistas múltiples

- **FR-010**: La cabecera del timeline MUST ofrecer un selector con al menos 5 vistas: Lista, Tabla, Kanban por etiqueta, Calendario mensual, Galería.
- **FR-011**: Cualquier vista MUST respetar los filtros activos (autor, etiqueta, rango fechas, búsqueda) sin recargar la página.
- **FR-012**: La preferencia de vista activa MUST persistir por usuario en localStorage entre sesiones.

#### Kanban proyectos

- **FR-013**: El sistema MUST leer archivos de `knowledge_base/proyectos/*.md` y agruparlos por el campo `estado` del frontmatter en columnas `todo`, `doing`, `done`, `blocked`.
- **FR-014**: Si la carpeta `knowledge_base/proyectos/` no existe, el sistema MUST crearla al primer acceso a la vista kanban junto con un archivo de bienvenida explicativo.
- **FR-015**: Un drag-and-drop entre columnas MUST actualizar el campo `estado` en el frontmatter del archivo `.md` correspondiente; el resto del archivo permanece intacto.
- **FR-016**: La UI móvil MUST ofrecer un mecanismo alternativo al drag-and-drop (long-press + menú) para cambiar el estado de una tarjeta sin gestos complejos.

#### Wiki-links y backlinks

- **FR-017**: El renderer markdown MUST reconocer la sintaxis `[[slug]]` y `[[slug|texto-visible]]` como wiki-link clicable que abre la nota destino si existe.
- **FR-018**: El sistema MUST mantener un índice de wiki-links: para cada nota destino, qué notas la referencian, refrescado tras crear/editar/archivar/restaurar cualquier nota.
- **FR-019**: La vista detalle de cada nota MUST mostrar al pie una sección "Referenciada desde" con la lista de backlinks (autor, fecha, snippet de contexto).
- **FR-020**: Un wiki-link a un slug inexistente MUST renderizarse visualmente distinto y, al hacer clic, abrir la modal de captura (US1) con el título prerrellenado.

#### Sidebar tipo Notion

- **FR-021**: El dashboard MUST mostrar un sidebar izquierdo colapsable con un árbol expandible que refleja la estructura real de `knowledge_base/`.
- **FR-022**: El árbol MUST cargar el contenido de una carpeta solo al expandirla (no recursivo en el primer render).
- **FR-023**: El sistema MUST permitir mover archivos entre carpetas mediante drag-and-drop, actualizando físicamente la ruta en disco.
- **FR-024**: El sistema MUST permitir crear una nueva carpeta dentro del árbol con un botón "+" y un nombre validado (sin caracteres prohibidos para FS).
- **FR-025**: En pantallas < 768 px, el sidebar MUST comportarse como drawer (oculto por defecto, abrir con botón hamburguesa, cerrar al elegir un nodo).

#### Búsqueda global Ctrl+K

- **FR-026**: La UI MUST registrar `Ctrl+K` (`Cmd+K`) como atajo global para abrir la paleta de comandos centrada con el input enfocado.
- **FR-027**: La paleta MUST agrupar los resultados en secciones: Notas, Proyectos, Acciones; máximo 5 ítems por sección.
- **FR-028**: Las acciones disponibles en la paleta MUST incluir, como mínimo: "capturar nueva nota", "abrir vista X", "lanzar agente Y", "ir a proyecto Z".
- **FR-029**: La paleta MUST ser navegable solo con teclado (flechas para mover, Enter para ejecutar, Esc para cerrar) sin necesidad de ratón.

#### Estado infra

- **FR-030**: El sidebar de infra MUST incluir al menos 6 badges con polling ≤ 60 s: VPS health, WordPress online, AEGIS/ALAMO último briefing, cron status, Stripe revenue del día, freqtrade PnL.
- **FR-031**: Un badge fallido MUST poder expandirse para mostrar mensaje de error y un link a logs/dashboard externo, sin propagar el error al resto del UI.

#### Lanzar agentes

- **FR-032**: El sidebar MUST incluir botones para ejecutar los agentes principales del unified-agent mediante la tool MCP `agente_ejecutar`, mostrando el output en un panel lateral.
- **FR-033**: Cualquier ejecución que supere un timeout configurable (default 30 s, consistente con el patrón `MCP_STALL_*`) MUST abortarse limpiamente con un mensaje claro al usuario.

#### Calendario y Gmail

- **FR-034**: El sidebar de calendario MUST mostrar los próximos 7 días naturales con eventos sincronizados vía el conector Google Calendar; clic abre detalle con link a calendar.google.com.
- **FR-035**: El dashboard MUST permitir crear eventos básicos (título + fecha + duración) que se persistan en Google Calendar a través del conector.
- **FR-036**: El sidebar de Gmail MUST listar los hilos que cumplen el filtro `is:starred OR label:Lectura/Tech OR from:noreply@anthropic.com`, máximo 20 hilos, ordenados por fecha descendente.
- **FR-037**: Un conector externo no autenticado o caducado MUST mostrar un CTA de reconexión en su panel correspondiente sin bloquear el resto del dashboard.

#### Stats widget

- **FR-038**: El widget de estadísticas MUST mostrar al menos: notas por autor en la semana actual, etiquetas top-10 por frecuencia, sparkline de notas/día en los últimos 30 días.
- **FR-039**: Los cálculos del widget MUST reflejar exclusivamente notas no archivadas y MUST consolidarse en el cliente sin requerir endpoints adicionales más allá del agregado básico que ya alimenta el timeline.

#### Grafo

- **FR-040**: La vista grafo MUST renderizar nodos (notas) y aristas (wiki-links) con simulación d3-force, agrupando nodos pequeños y agrandando hubs por número de conexiones.
- **FR-041**: En vaults grandes (≥ 500 notas), el sistema MUST aplicar sampling (top-N por número de conexiones) y mostrar el conteo total + visible al usuario.
- **FR-042**: Hover sobre un nodo MUST mostrar tooltip con título + autor + primera línea; clic abre la vista detalle.

#### No-regresión y constraints transversales

- **FR-043**: TODOS los endpoints existentes de Fase A (timeline, búsqueda, vista nota, whoami) MUST seguir respondiendo con el mismo contrato; los 78 tests de Fase A MUST seguir pasando sin cambios.
- **FR-044**: El sistema MUST seguir exigiendo JWT válido en todas las peticiones; `sub: angel` y `sub: africa` MUST tener paridad de acceso completa, incluyendo edición y archivado mutuo.
- **FR-045**: El vault permanece como markdown puro: todas las "bases de datos" tipo Notion (kanban, proyectos, etc.) son archivos `.md` con frontmatter; el sistema NO crea ninguna base de datos paralela.
- **FR-046**: El sistema NO instala AppFlowy, NotionAPI ni ninguna dependencia propietaria de tipo Notion; toda la funcionalidad se implementa con la stack ya elegida en Fase A (React + Vite + Tailwind + shadcn/ui + FastAPI) más librerías OSS estrictamente necesarias (d3 para grafo, dnd-kit o equivalente para drag-and-drop).
- **FR-047**: La interfaz MUST seguir funcionando en pantallas ≥ 360 px de ancho (móvil) y ≥ 1024 px (escritorio) sin pérdida de funcionalidad; el grafo y el árbol completo pueden ofrecer fallback simplificado en móvil.
- **FR-048**: La latencia inicial de carga del dashboard MUST mantenerse < 2 s sobre 4G simulado, equivalente al benchmark de Fase A.

### Key Entities *(include if feature involves data)*

- **Nota diaria** (`knowledge_base/dia/<fecha>-<slug>.md`): unidad mínima del timeline. Frontmatter con `autor`, `fecha`, `etiquetas`, opcionalmente `titulo`, `modified_at`, `archived_at`, `archive_reason`. Cuerpo en markdown con sintaxis enriquecida (wiki-links, imágenes, código).
- **Proyecto NosVers** (`knowledge_base/proyectos/<slug>.md`): tarjeta del kanban. Frontmatter con `estado ∈ {todo, doing, done, blocked}`, opcionalmente `responsable`, `deadline`, `etiquetas`. Cuerpo libre.
- **Wiki-link**: estructura derivada (no persistida en disco como entidad separada) que relaciona una nota fuente con una nota destino vía sintaxis `[[slug]]` en el cuerpo. El índice de backlinks es derivado y se reconstruye on-the-fly o se cachea con invalidación al guardar/archivar/restaurar.
- **Carpeta del vault** (`knowledge_base/<ruta>/`): cualquier directorio bajo `knowledge_base/` visible en el árbol del sidebar. Sin metadata propia más allá del nombre.
- **Vista**: enumeración cliente-only con valores `lista`, `tabla`, `kanban`, `calendario`, `galeria`. Persistida en localStorage.
- **Estado de infra**: estructura derivada de polling externo. Para cada servicio, un tupla `(nombre, estado ∈ {ok, warn, error}, valor, último_check)`.
- **Agente del unified-agent**: identificador (slug) que se pasa a la tool MCP `agente_ejecutar`. Lista predefinida en config del dashboard, no autodetectada del FS.
- **Evento de calendario / hilo de Gmail**: estructura derivada del conector externo; no persistida en el vault.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Un usuario autenticado puede capturar una nota nueva desde el navegador en ≤ 5 segundos desde pulsar `Ctrl+N` hasta verla en el timeline, en una conexión móvil 4G simulada.
- **SC-002**: Un usuario puede editar una nota existente, guardar el cambio y ver el resultado reflejado en el timeline en ≤ 1 segundo en escritorio.
- **SC-003**: Cambiar entre las 5 vistas del timeline (lista/tabla/kanban/calendario/galería) refresca el render en ≤ 200 ms preservando todos los filtros activos.
- **SC-004**: La paleta de comandos `Ctrl+K` abre en ≤ 100 ms y devuelve resultados de búsqueda en ≤ 300 ms p95 sobre el vault actual.
- **SC-005**: Mover una tarjeta entre columnas del kanban actualiza el archivo `.md` y su frontmatter en ≤ 500 ms, sin pérdida de campos del frontmatter no relacionados con `estado`.
- **SC-006**: El árbol del sidebar refleja con precisión la estructura del vault: durante una semana de uso real, ningún usuario reporta discrepancias entre lo que ve en el sidebar y lo que existe en disco.
- **SC-007**: Tras el deploy de Fase B+C, los 78 tests automatizados de Fase A pasan sin cambios y los flujos manuales de Fase A (timeline, filtros, búsqueda, vista detalle) siguen funcionando idénticos.
- **SC-008**: La latencia inicial del dashboard se mantiene < 2 s sobre 4G simulado, sin regresión medible frente a la línea base de Fase A.
- **SC-009**: Durante la primera semana de uso real con Angel y África, no se reporta ninguna pérdida de datos (notas borradas accidentalmente, frontmatter dañado, ediciones perdidas) ni ningún caso de notas con autor incorrecto.
- **SC-010**: El sistema soporta sin degradación medible un vault de hasta 1.000 notas y 5.000 wiki-links totales en las vistas timeline, búsqueda, kanban y árbol; la vista grafo soporta hasta 500 notas con sampling automático para tamaños mayores.
- **SC-011**: La tasa de errores 5xx de los nuevos endpoints (captura, edición, archivado, kanban, árbol, etc.) se mantiene por debajo del 0.1% durante la primera semana de uso real.
- **SC-012**: En el primer mes, Angel y África declaran (cualitativamente, por mensaje Telegram al sistema) que el dashboard ha reemplazado su uso cotidiano de Obsidian para captura, edición y navegación, recurriendo a Obsidian solo para tareas avanzadas no cubiertas.
- **SC-013**: Las integraciones externas (Google Calendar, Gmail, estado infra) no afectan la disponibilidad del dashboard: si un conector falla, el resto del dashboard sigue 100% funcional.
- **SC-014**: Una nota archivada y luego restaurada conserva exactamente el mismo contenido y frontmatter que antes del archivado, salvo los campos `archived_at` y `archive_reason` que se eliminan al restaurar.

## Assumptions

- **A-001**: Fase A está en producción y operativa: los módulos `tablero/timeline.py`, `tablero/nota.py`, `tablero/rest.py`, `tablero/log.py`, `tablero/scripts/dev_server.py` y la app React bajo `tablero/web/` son la base sobre la que se construye Fase B+C, sin reescrituras estructurales.
- **A-002**: Las tools MCP `dia_capturar`, `dia_contexto`, `dia_buscar` (proyecto 001) están operativas y exportadas; el dashboard las invoca para captura y búsqueda full-text, no reimplementa lógica equivalente.
- **A-003**: La autenticación JWT con `sub ∈ {angel, africa}` ya está consolidada por Fase A; Fase B+C no introduce cambios en el flujo de tokens.
- **A-004**: Los conectores Google Calendar y Gmail expuestos por `mcp__claude_ai_Google_Calendar__*` y `mcp__claude_ai_Gmail__*` están disponibles desde el contexto MCP que sirve el dashboard; alternativamente, el dashboard puede pasar las llamadas a través de un proxy autenticado contra la API REST de Google si la integración MCP directa no es posible en producción.
- **A-005**: La paridad de acceso entre Angel y África es absoluta: ambos pueden editar, archivar y restaurar cualquier nota independientemente del autor original. La trazabilidad se asegura por logging (`editor_sub` en cada operación), no por bloqueos.
- **A-006**: La concurrencia se gestiona con control optimista (campo `modified_at` en frontmatter + 409 Conflict). No se implementa locking server-side ni edición colaborativa en tiempo real (operational transform, CRDTs) — están explícitamente fuera de alcance para esta fase.
- **A-007**: La sincronización en tiempo real entre Angel y África NO se implementa con WebSocket en Fase B+C; un polling razonable (≤ 60 s para infra, refresh manual para timeline) cubre las necesidades reales. WebSocket queda como opción futura si la fricción aparece.
- **A-008**: La estructura `knowledge_base/proyectos/` se crea on-demand cuando un usuario abre por primera vez la vista kanban; no requiere migración previa.
- **A-009**: El renderer markdown extiende el de Fase A para añadir wiki-links `[[slug]]`; el resto de la sintaxis (encabezados, listas, código, imágenes, blockquotes, tablas) ya funciona de Fase A.
- **A-010**: Los soft deletes (notas en `dia/archivo/`) no se eliminan automáticamente nunca; quedan ahí indefinidamente. La carpeta de archivo no se sincroniza con el sparkline ni con stats. Si en el futuro se necesita purga, será una tarea manual o un agente cron separado.
- **A-011**: El widget de stats y la vista grafo se calculan en cliente a partir de los datos ya cargados (timeline + índice de wiki-links). No se introduce un servicio de analytics paralelo.
- **A-012**: Las pruebas automatizadas usan el mismo framework de Fase A (pytest backend + vitest frontend), extendiendo la suite existente sin cambiar la convención.
- **A-013**: El despliegue dev sigue siendo `tablero.72.61.160.108.nip.io` (ya activo). No se crea ningún nuevo subdominio ni se cambia el TLS.
- **A-014**: Los conventional commits agrupan trabajo por sub-componente (1-14) y se hacen sobre la rama `main` del monorepo `/home/nosvers/` siguiendo el convenio de Fase A. Angel hace el push manual al final.
- **A-015**: La purga de wiki-links rotos (notas borradas que dejaban referencias huérfanas) ocurre al render, no en disco: las notas que apuntan a slugs inexistentes muestran enlace estilizado como "crear", el frontmatter no se reescribe automáticamente.
