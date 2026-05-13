# Feature Specification: Second Brain Dashboard — Fase A (MVP read-only)

**Feature Branch**: `001-second-brain-fase-a` (subproject is not its own git repo; staying on parent monorepo `main`)

**Created**: 2026-05-13

**Status**: Draft

**Input**: User description: "Web dashboard NosVers — Fase A: vista unificada de las notas diarias de Angel y África en el vault, con filtros, búsqueda full-text y vista detalle. Solo lectura. Sobre la base del proyecto 001 (voz/auth, voz/buscar, voz/vault_io, vault `knowledge_base/dia/*.md`, JWT con sub angel|africa). Sin escritura, sin regresión, sin frameworks pesados."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Timeline unificado de los últimos 30 días (Priority: P1)

Angel (o África) abre el dashboard en su móvil o navegador, inicia sesión con su token JWT, y la pantalla principal le muestra una lista de las notas diarias propias y las de la otra persona, mezcladas y ordenadas por fecha descendente. Cada entrada lleva un chip de autor visible ("Angel" o "África") para que la mezcla no sea confusa. La ventana por defecto es los últimos 30 días, lo cual cubre el ritmo de trabajo NosVers sin sobrecargar la primera carga.

**Why this priority**: Este es el corazón de la propuesta de valor — "ver la cabeza compartida del proyecto en una sola vista". Sin esto, no hay dashboard; con solo esto, ya hay valor para ambos. Es lo único estrictamente necesario para hablar de MVP.

**Independent Test**: Se valida abriendo `https://tablero.nosvers.com` con un JWT válido en `Authorization: Bearer ...`, viendo notas de los dos autores en una sola lista ordenada por fecha, y comprobando que sin token la pantalla rechaza el acceso. Si esta historia funciona sola, ya hay producto.

**Acceptance Scenarios**:

1. **Given** existen notas en `knowledge_base/dia/` con `autor: angel` y `autor: africa` fechadas en los últimos 30 días, **When** un usuario autenticado con `sub: angel` abre el dashboard, **Then** ve una única lista con notas de ambos autores ordenadas de la más reciente a la más antigua, cada una con su chip de autor.
2. **Given** existen notas con fecha de hace más de 30 días, **When** el usuario carga la vista por defecto, **Then** esas notas antiguas no aparecen (quedan accesibles solo vía filtro de rango o búsqueda).
3. **Given** un usuario sin token o con token inválido/caducado, **When** intenta abrir el dashboard, **Then** ve una pantalla de "no autenticado" y no recibe ningún dato del vault.
4. **Given** un usuario autenticado con `sub: africa`, **When** abre el dashboard, **Then** ve exactamente la misma mezcla de notas que vería Angel (paridad de acceso; no hay administrador).

---

### User Story 2 — Filtros combinables (autor, etiqueta, rango de fechas) (Priority: P2)

El usuario refina la vista del timeline aplicando uno o varios filtros simultáneamente: solo Angel, solo África, o ambos; una etiqueta concreta entre las seis fijas (trabajo, nosvers, familia, mental, idea, otro); y/o un rango de fechas custom. Los filtros se combinan con AND y se aplican sin recargar la página.

**Why this priority**: El timeline puro responde "¿qué hemos pensado últimamente?". Los filtros responden "¿qué hemos pensado sobre X?" — un salto de utilidad real, pero no estrictamente necesario para la primera demo.

**Independent Test**: Con el timeline cargado, abrir el panel de filtros, elegir "solo África + etiqueta nosvers + últimos 7 días" y comprobar que la lista se reduce a las notas que cumplen las tres condiciones. Quitar un filtro a la vez y verificar que la lista se expande consistentemente.

**Acceptance Scenarios**:

1. **Given** el timeline con 30 días cargado, **When** el usuario activa el filtro "autor: África", **Then** la lista se reduce a las notas con `autor: africa` sin recargar la página.
2. **Given** filtros "autor: Angel" + "etiqueta: nosvers" activos, **When** se aplican, **Then** la lista contiene exactamente las notas que cumplen ambas condiciones (intersección), y el panel de filtros muestra los chips activos para que el usuario sepa qué tiene puesto.
3. **Given** el usuario selecciona un rango de fechas que cubre solo 3 días, **When** se aplica, **Then** la lista muestra únicamente notas dentro de ese rango (inclusivo en ambos extremos).
4. **Given** un set de filtros activo, **When** el usuario clica "limpiar filtros", **Then** el timeline vuelve al estado por defecto (últimos 30 días, ambos autores, todas las etiquetas).

---

### User Story 3 — Búsqueda full-text del vault (Priority: P2)

El usuario escribe en una barra de búsqueda visible permanentemente en la cabecera. A medida que escribe (con un pequeño debounce), aparecen resultados ordenados por relevancia: notas cuyo cuerpo o frontmatter contiene el término. Cada resultado lleva el chip de autor, fecha y un snippet con el match resaltado.

**Why this priority**: La búsqueda es la segunda forma de navegar el vault, complementaria al timeline cronológico. Sin ella, encontrar "esa idea que tuvimos hace dos meses sobre el composteur" es imposible.

**Independent Test**: Escribir un término que sepamos que existe en al menos una nota, comprobar que aparece, comprobar que el resaltado del match es correcto, y medir la latencia desde tecleo hasta render del primer resultado.

**Acceptance Scenarios**:

1. **Given** existe una nota que contiene la palabra "lombrithé" en el cuerpo, **When** el usuario teclea "lombrithé" en la búsqueda, **Then** esa nota aparece en los resultados en ≤ 500 ms p95, con un snippet que muestra el contexto del match.
2. **Given** una consulta que no coincide con ninguna nota, **When** se envía, **Then** la UI muestra un mensaje claro de "sin resultados" sin romperse ni colgar la barra.
3. **Given** el usuario escribe muy rápido, **When** la entrada cambia varias veces en un segundo, **Then** solo se ejecuta una búsqueda contra el backend (debounce), evitando 5 peticiones simultáneas.
4. **Given** un usuario sin token, **When** intenta usar la búsqueda, **Then** recibe 401 y la UI le indica que reautentique (sin filtrar datos por sub: la búsqueda devuelve notas de ambos autores como el timeline).

---

### User Story 4 — Vista detalle de una nota (Priority: P3)

El usuario hace clic en una entrada del timeline o de los resultados de búsqueda. Se abre una vista detalle (panel lateral en escritorio, pantalla completa en móvil) que muestra el contenido completo del archivo `.md` renderizado: encabezados con jerarquía, listas con bullets, bloques de código con resaltado básico, enlaces clicables y referencias a imágenes (`![alt](attachments/...)`) cargadas desde el vault.

**Why this priority**: Sin esta vista, el timeline solo es una lista de titulares — útil pero incompleto. Es prioridad P3 porque puede empezar como una versión muy básica (markdown plano) y mejorar luego; el valor incremental sobre US1/US2/US3 es menor.

**Independent Test**: Hacer clic en una nota con encabezados, listas, código y una imagen embebida, y comprobar que cada elemento se renderiza correctamente. Comprobar que la apertura es percibida como instantánea (≤ 300 ms desde clic a contenido visible).

**Acceptance Scenarios**:

1. **Given** una nota con sintaxis markdown variada (heading, lista, código, enlace), **When** el usuario hace clic en ella, **Then** la vista detalle muestra cada elemento correctamente formateado en ≤ 300 ms.
2. **Given** una nota que referencia una imagen vía `![texto](attachments/foto.jpg)`, **When** se abre el detalle, **Then** la imagen se carga desde el vault y se muestra inline; si la imagen no existe, aparece un placeholder claro en lugar del HTML roto.
3. **Given** la vista detalle abierta, **When** el usuario pulsa "cerrar" (o Esc en escritorio, swipe en móvil), **Then** vuelve al timeline sin perder los filtros ni la posición de scroll.
4. **Given** una nota con frontmatter YAML, **When** se renderiza, **Then** el frontmatter aparece en una zona separada y discreta (no se mezcla con el cuerpo markdown como si fuera contenido).

---

### Edge Cases

- **Vault vacío**: si la carpeta `knowledge_base/dia/` no contiene ninguna nota, el timeline muestra un estado vacío explicativo ("Aún no hay notas en los últimos 30 días — captura la primera con la PWA voz") en lugar de una lista en blanco.
- **Nota con frontmatter malformado**: una nota cuyo YAML no parsea correctamente NO debe romper el timeline; debe aparecer con un indicador de "metadata corrupta" y seguir mostrando el cuerpo de markdown si está accesible.
- **Token expirado a mitad de sesión**: si el access token caduca mientras el usuario navega, la siguiente petición devuelve 401, la aplicación intenta renovar silenciosamente con el refresh token; si la renovación falla, la UI fuerza relogin sin perder el estado de filtros (se restauran tras autenticar).
- **Pérdida temporal de red en móvil**: si el dashboard pierde conectividad, las últimas 30 notas vistas siguen disponibles desde la caché local; cualquier interacción que requiera el servidor muestra un banner "offline — algunos datos pueden estar desactualizados" sin romper la UI.
- **Reloj del cliente mal ajustado**: el orden por fecha del timeline usa el campo `fecha` del frontmatter (autoritativo desde el vault), no la hora local del navegador; un cliente con reloj 6 h por delante o por detrás ve el mismo orden que cualquier otro cliente.
- **Búsqueda con caracteres especiales o acentos**: una consulta como "lombrithé" o "café" debe encontrar notas que contengan esa palabra independientemente de mayúsculas/minúsculas y acentos.
- **Concurrencia: Angel captura mientras África lee**: en Fase A no hay sincronización en tiempo real; África verá la nueva nota de Angel al recargar el timeline o al cambiar de filtro. Es una concesión consciente; el push en vivo se trata en Fase B.
- **Nota con cuerpo muy grande (> 200 KB)**: la vista detalle debe seguir rindiendo aceptablemente; si excede un umbral razonable, se permite render parcial con "ver más" para no congelar el navegador móvil.
- **Filtro de rango con fechas invertidas (fin < inicio)**: la UI debe rechazar el rango antes de enviar la petición, mostrando un aviso claro al usuario.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema MUST exigir un JWT válido en todas las peticiones de lectura de notas; sin token o con token caducado, el sistema MUST responder con 401 sin filtrar ningún dato del vault.
- **FR-002**: El sistema MUST distinguir al usuario que llama por el claim `sub` (valores aceptados: `angel`, `africa`) y registrar ese identificador en los logs de cada petición.
- **FR-003**: La vista principal MUST mostrar un timeline mezclado de notas con `autor: angel` y `autor: africa` extraídas del vault, ordenadas por el campo `fecha` del frontmatter de manera descendente.
- **FR-004**: Por defecto, el timeline MUST mostrar las notas de los últimos 30 días naturales (hoy incluido); notas más antiguas NO aparecen sin un filtro de rango explícito.
- **FR-005**: Cada entrada del timeline MUST mostrar al menos: chip de autor, fecha (formato local), título o primera línea significativa de la nota, y etiquetas presentes en el frontmatter.
- **FR-006**: Los usuarios MUST poder filtrar el timeline por autor (Angel / África / ambos — por defecto), por etiqueta (una de las seis fijas: trabajo, nosvers, familia, mental, idea, otro), y por rango de fechas custom; los filtros se combinan con AND.
- **FR-007**: Aplicar o quitar cualquier filtro MUST refrescar la vista sin recargar la página completa.
- **FR-008**: Los usuarios MUST poder ejecutar una búsqueda full-text sobre el cuerpo y frontmatter de las notas; los resultados MUST incluir chip de autor, fecha y un snippet con el término resaltado.
- **FR-009**: La búsqueda MUST normalizar acentos y mayúsculas/minúsculas (búsqueda insensible a `é/e` y a caso) para que consultas en español funcionen como espera un hablante nativo.
- **FR-010**: La entrada de búsqueda MUST aplicar un debounce de al menos 250 ms para evitar peticiones excesivas mientras el usuario teclea.
- **FR-011**: Los usuarios MUST poder hacer clic en una entrada (de timeline o de búsqueda) para abrir una vista detalle que renderice el contenido completo de la nota como markdown.
- **FR-012**: La vista detalle MUST renderizar encabezados, listas, bloques de código con resaltado básico, enlaces clicables, citas (blockquotes), tablas y referencias a imágenes locales del vault (rutas relativas tipo `attachments/...`).
- **FR-013**: La vista detalle MUST mostrar el frontmatter YAML en una sección visualmente diferenciada del cuerpo de la nota (no como contenido de markdown).
- **FR-014**: El sistema MUST NOT exponer endpoints de escritura (POST/PUT/PATCH/DELETE) sobre el vault desde el dashboard durante Fase A; cualquier intento de petición de escritura desde el frontend MUST fallar a nivel de código (no existe el endpoint).
- **FR-015**: El sistema MUST tolerar gracefully notas con frontmatter inválido o ausente: la nota sigue siendo listable usando defaults razonables (autor desconocido, fecha del `mtime` del archivo, sin etiquetas) y se marca visualmente como "metadata incompleta".
- **FR-016**: La interfaz MUST ofrecer un estado "offline" cuando la red falle: el usuario sigue viendo la última copia cacheada del timeline (hasta 30 notas) y se le indica que los datos pueden estar desactualizados.
- **FR-017**: Cuando un access token expira durante la sesión, el sistema MUST intentar renovarlo automáticamente con el refresh token; si la renovación falla, MUST pedir relogin preservando los filtros activos para restaurarlos tras autenticar.
- **FR-018**: El sistema MUST registrar todas las peticiones de lectura (timestamp, sub, ruta, latencia, código de estado) en un log estructurado consistente con el del proyecto 001.
- **FR-019**: Errores 5xx repetidos en endpoints críticos MUST disparar una notificación al CEO vía el canal Telegram existente, con deduplicación para evitar inundación.
- **FR-020**: La interfaz MUST funcionar correctamente en pantallas móviles ≥ 360 px de ancho (Android moderno) y en escritorio ≥ 1024 px sin pérdida de funcionalidad.

### Key Entities *(include if feature involves data)*

- **Nota diaria** (`knowledge_base/dia/<fecha>-<slug>.md` o equivalente): archivo markdown con frontmatter YAML (`autor`, `fecha`, `etiquetas`, opcionalmente `titulo` y otros) más cuerpo. Es la unidad mínima del timeline. Identificada únicamente por su ruta relativa dentro del vault.
- **Autor**: enumeración cerrada con dos valores: `angel`, `africa`. Determina el chip mostrado y se mapea uno-a-uno con el `sub` del JWT del usuario que la creó (asignado por el flujo del proyecto 001).
- **Etiqueta**: enumeración cerrada de seis valores en Fase A: `trabajo`, `nosvers`, `familia`, `mental`, `idea`, `otro`. Una nota puede tener 0..N etiquetas.
- **Usuario del dashboard**: identidad establecida por el JWT, con `sub ∈ {angel, africa}`. No hay perfil server-side adicional; cualquier preferencia (filtros recordados, tema oscuro/claro) vive en localStorage del navegador.
- **Sesión**: pareja (access token, refresh token) emitida por el sistema de auth del proyecto 001. Stateless desde el punto de vista del servidor del dashboard; el dashboard solo verifica firma y caducidad.
- **Resultado de búsqueda**: estructura derivada (no persistida) que incluye la ruta de la nota, autor, fecha, etiquetas, y un snippet con resaltado del término.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Un usuario autenticado ve el timeline mezclado de los últimos 30 días en ≤ 2 s en una conexión móvil 4G simulada (medido como Lighthouse "Time to Interactive" sobre una página de timeline con ~30 notas).
- **SC-002**: Aplicar o quitar cualquier combinación de filtros refresca la lista visible en ≤ 200 ms, sin recargar la página, en un dispositivo móvil de gama media.
- **SC-003**: Una búsqueda full-text con un término no vacío devuelve resultados visibles al usuario en ≤ 500 ms p95 sobre el vault actual de NosVers.
- **SC-004**: Al hacer clic en una entrada, la vista detalle muestra el contenido completo renderizado en ≤ 300 ms.
- **SC-005**: Tras desplegar el dashboard a `tablero.nosvers.com`, los health checks de las PWAs voz, del agt07_diario, del bot Telegram, de WordPress y de los bots de trading siguen pasando con los mismos resultados que antes del deploy (cero regresión observable).
- **SC-006**: Una petición a cualquier endpoint de lectura sin JWT válido recibe HTTP 401 en ≤ 50 ms y ningún byte del vault es devuelto en el cuerpo de la respuesta.
- **SC-007**: Angel y África pueden usar el dashboard durante una semana completa sin reportar ninguna pérdida de datos, ninguna nota que aparezca con autor incorrecto, y ningún caso en que un filtro retorne notas que no cumplen sus criterios.
- **SC-008**: La tasa de error 5xx de los endpoints del dashboard se mantiene por debajo del 0.1% del total de peticiones durante la primera semana de uso real.

## Assumptions

- El proyecto 001 está en producción y los módulos del vault y de autenticación (auth, search, vault I/O, contexto del día) son estables y compatibles hacia adelante.
- Las notas en `knowledge_base/dia/` siguen un convenio consistente: frontmatter YAML con al menos los campos `autor` (uno de `angel`, `africa`), `fecha` (YYYY-MM-DD), y `etiquetas` (lista de strings). Casos sin estos campos se tratan con defaults (ver FR-015) y no impiden el funcionamiento del timeline.
- Las imágenes referenciadas desde notas viven en una carpeta `attachments/` accesible al servidor que sirve el dashboard; el servidor las expone bajo un path de solo lectura.
- El subdominio `tablero.nosvers.com` está disponible o se configurará en el DNS durante la implementación; pruebas locales pueden ejecutarse contra `http://localhost:<puerto>` sin bloquear la entrega.
- Los usuarios usan navegadores modernos (las últimas dos versiones de Chrome móvil/escritorio, Safari iOS, Firefox); IE/legacy no son objetivo.
- La conexión móvil de referencia es 4G en zona rural francesa (perfil Lighthouse "Slow 4G" como aproximación).
- Lighthouse en modo móvil simulado es un proxy aceptable de la experiencia real de Angel; no se requieren pruebas con hardware real para la firma de Fase A.
- Las 30 últimas notas cacheadas en el navegador no contienen información que requiera borrado proactivo si Angel pierde el móvil (asunción consistente con el hecho de que el vault entero ya está en su Obsidian local; no se introduce riesgo nuevo).
- La búsqueda full-text usa el índice/lógica ya implementada en el proyecto 001 (no se construye uno paralelo en Fase A).
