# Feature Specification: Claudio PWA Contextos (007)

**Feature Branch**: `007-claudio-pwa-contextos`
**Created**: 2026-05-14
**Status**: Approved — implementation autorisée sin parar
**Input**: `BRIEF.md` · pre-requisitos 001 ✓ 002 ✓ 005 ✓ 006 ✓

---

## Overview

Claudio gana cara móvil. Una PWA propia, instalable como app Android,
servida desde `claudio.72.61.160.108.nip.io`, con **tres contextos
aislados** (Casa, NosVers, Trabajo) que comparten infraestructura backend
(broker WS, vault familiar, intent_router) pero exhiben **identidades
visuales y dominios funcionales distintos** según el contexto activo.

El **contexto Trabajo** es el novedoso: dominio profesional del usuario
(DI Environnement — désamiantage / déplombage / décontamination), con
vault aislado en `knowledge_base/trabajo/`, 10 tools MCP nuevos
(`chantier_*`, `equipe_*`, `devis_*`, `ppsps_*`, `documento_trabajo_*`),
endpoints REST namespaced en `/tablero/api/v3/trabajo/*`, y estética
*bicromática rojo DI #D62828 + blanco + negro + tipografía condensada
MAYÚSCULAS* que rinde homenaje a la furgoneta de la empresa.

PTT (push-to-talk) global con 5 fases visuales reutiliza el ciclo
`voz → intent_router → tool → vault → respuesta hablada` de Fase 2,
añadiendo `context` al payload para que el router filtre tools accesibles.

---

## Principios no-negociables

1. **Aislamiento estricto del contexto Trabajo**. Vault, tools, endpoints
   y memorias del contexto Trabajo NO accesibles sin JWT con
   `context=trabajo`. África jamás recibe un token con ese scope; intento
   → `403`. Double-check server-side: solo `sub=angel` puede emitir tokens
   con `context=trabajo`.
2. **No romper nada existente**. PWA voz `nosvers-voz.*`, tablero
   `tablero.*`, cockpit con 19 widgets, automatizaciones, agentes, bot
   Telegram, mcp_server y sus 22 tools de Fase 1 siguen funcionando
   idénticos. La PWA nueva vive en su propio subdominio y consume APIs
   con parámetros adicionales.
3. **Soberanía**. Cero dependencias cloud nuevas. Todo self-hosted en VPS
   Hostinger. Sin Firebase, sin OneSignal, sin servicios externos de
   push. Web Push es opcional y diferido a Fase 8.
4. **Mobile-first real**. Diseño touch primario, gestos PTT, tipografía
   legible a un brazo de distancia, contraste AAA en contexto Trabajo
   (rojo DI sobre negro), respeto a `prefers-reduced-motion` y
   `prefers-color-scheme`.
5. **Offline-first sólo lectura**. Service Worker cachea
   `GET /tablero/api/v2/*` y `/tablero/api/v3/trabajo/*` con estrategia
   stale-while-revalidate. Las escrituras (PTT, action endpoints)
   requieren conectividad y muestran error claro.
6. **Bug telegram_enviar**. NO se invoca `telegram_enviar` en ningún
   paso intermedio. Si una verificación final lo necesita, abortar
   tras 30 s y marcar `MCP_STALL_RESOLVED_BY_OPUS_MOBILE` en tasks.md.
   (Memoria persistente del proyecto.)

---

## Personas

- **Angel** — CEO NosVers + jefe de obra DI Environnement. Único con
  acceso a los 3 contextos. Token JWT contendrá
  `available_contexts: ["casa", "nosvers", "trabajo"]` y `context` activo
  selecionable desde la PWA.
- **África** — Directora de Conocimiento NosVers. Acceso a 2 contextos:
  `available_contexts: ["casa", "nosvers"]`. El contexto Trabajo le es
  invisible; ni en pantalla ni en API.

---

## User Scenarios

### US-1 — Arranque y selección de contexto (P0)

Angel abre la PWA en su Android. Pantalla **Home**:
- Saludo dinámico ("Buenos días, Angel" si 6-12 h, "Buenas tardes" si
  12-19 h, "Buenas noches" si 19-6 h).
- 3 cards verticales grandes en orden Casa → NosVers → Trabajo:
  - **Casa**: gradient amber → orange, icono Home, "2 cosas hoy".
  - **NosVers**: gradient emerald → lime, icono Sprout, "387 € mes · 3 pedidos".
  - **Trabajo**: card bicromática (mitad blanca con logo DI texto en
    negro, mitad roja #D62828 con KPI "2 CHANTIERS").
- Hint inferior: "o di 'claudio' desde el PC casa".

Tap en card Trabajo → transición de tema (200 ms) → bottom tabs y header
DI cargan → ya está en contexto Trabajo. El JWT se "rota" en cliente
(mismo token, campo `context=trabajo` activo) y todas las llamadas a la
API llevan ese contexto. Backend valida.

### US-2 — PTT en contexto Trabajo (P0)

Angel ya en contexto Trabajo, tab "Chantiers". Mantiene pulsado el FAB
del micrófono (rojo DI con borde negro). El FAB se expande, aparece
overlay con:

- Waveform en vivo (Canvas + Web Audio AnalyserNode).
- Timer en MAYÚSCULAS condensadas: "0:03".
- Hint "DESLIZA ARRIBA PARA CANCELAR".

Suelta el botón. Estado pasa a **Sending** (spinner sutil), luego
**Thinking** (mini NeuralGraph estilo cockpit), luego **Speaking**:
el audio Piper TTS local reproduce la respuesta, texto visible, quick
replies opcionales ("VER CHANTIER", "AÑADIR JOURNAL").

Backend: `POST /voz/api/dictado-procesar` con JWT con `context=trabajo`.
El router decide `chantier_evento(...)` (tool del dominio Trabajo).
Si el dictado fuera "apunta 80 euros de gasolina", el router elige
`gasto_anotar` — pero el `context=trabajo` filtra: tools de casa están
fuera del whitelist en este contexto → cae a `dia_capturar` en
`trabajo/journal/` o devuelve "fuera de contexto".

### US-3 — África abre PWA (P0)

África abre la PWA. Su JWT trae `available_contexts: ["casa", "nosvers"]`.
La Home muestra **sólo 2 cards** (Casa y NosVers). El espacio donde
Angel ve "Trabajo" está oculto, no en gris. Si África inyectara
`context=trabajo` en el body de una llamada, backend responde `403`.

### US-4 — Casa, gastos del mes (P1)

Angel en contexto Casa, tab "Gastar". Widget GastosMes mobile-first: card
grande con total mes, 3 cards más pequeñas por categoría top. PTT:
"Apunta 12 de pan en supermercado." → router decide
`gasto_anotar(12, "pan", "supermercado", autor="angel")` → tool ejecuta
en `familia/gastos/` (vault Casa) → TTS "Apuntado, 12 euros en
supermercado. Llevas 287 este mes." → 60 s después widget refleja.

### US-5 — NosVers, ventas Stripe (P1)

Angel en contexto NosVers, tab "Tienda · Stripe". Widget reusa el worker
`revenue.py` existente que ya publica en canal WS `revenue`. PTT: "Cuánto
he vendido este mes?" → router decide tool de consulta o respuesta
directa con datos cacheados.

### US-6 — Vault Trabajo aislado (P0)

Angel desde la PWA en contexto Trabajo, tab "Chantiers", abre el
chantier "Bordeaux Nord". Ve INDEX.md con cliente, devis, equipe
asignada. Tap en "Journal" → lista entradas YYYY-MM-DD.md.
- PTT en este contexto: "Hoy hemos acabado la zona 2." → router
  decide `chantier_evento("bordeaux-nord", "avance", "acabada zona 2",
  "angel")` → tool escribe en
  `trabajo/chantiers/bordeaux-nord/journal/2026-05-14.md`.
- Backend valida que `JWT.context == "trabajo"` antes de aceptar la
  llamada al tool. Sin ese scope → 403.

### US-7 — Instalación PWA (P0)

Chrome Android detecta `manifest.json` y muestra "Añadir a inicio".
Angel acepta. App aparece como icono propio (no chrome embebido). Splash
verde NosVers con logo. Al abrir, va a Home si no hay contexto activo,
o al último contexto usado si lo hay (persistencia en `localStorage`).

### US-8 — Modo conversación 30 s (P2)

Angel hace doble-tap en el FAB micrófono. Overlay PTT entra en modo
**conversación**: 30 s sin tener que mantener pulsado. Cada turno de voz
detectado por VAD → enviar → respuesta → siguiente turno. Tras 30 s o
tras tap explícito, vuelve a Idle.

---

## Functional Requirements

### Bloque A — PWA scaffold (FR-A)

- **FR-A-1** Vite + React 18 + TypeScript + Tailwind 3, en
  `tablero/web-claudio/` (proyecto separado de `tablero/web/`).
- **FR-A-2** Tailwind con `darkMode: 'class'` y 3 theme variants
  configurados como data-attribute (`[data-context="casa"]`,
  `[data-context="nosvers"]`, `[data-context="trabajo"]`) que invierten
  variables CSS de fondos, texto, acentos.
- **FR-A-3** `manifest.json` válido (name, short_name, icons 192/512,
  start_url `/`, display `standalone`, theme_color por contexto).
- **FR-A-4** Service Worker en `public/sw.js` con Workbox-equivalent
  hecho a mano: precache shell + runtime cache stale-while-revalidate
  para GET API. NO cachea POST. Bumpear `CACHE_NAME` invalida.
- **FR-A-5** Bundle final < 2 MB (gzip). Lazy load de cada contexto.
- **FR-A-6** Splash + theme_color dependen del contexto previo si existe.

### Bloque B — JWT extendido (FR-B)

- **FR-B-1** Campo `context` en payload JWT (valores: `casa`, `nosvers`,
  `trabajo`). Default emisión: `casa`.
- **FR-B-2** Campo `available_contexts: list[str]` en JWT. Angel:
  `["casa", "nosvers", "trabajo"]`. África: `["casa", "nosvers"]`.
- **FR-B-3** Función `voz.auth.emitir_token(..., contexts=[...])` extendida.
  Valida que `trabajo` solo se conceda si `autor == "angel"`. Si África
  pidiera trabajo, `ValueError`.
- **FR-B-4** `validar_token` devuelve payload incluyendo
  `available_contexts`. Default `["casa", "nosvers"]` si campo ausente
  (retro-compat para tokens viejos).
- **FR-B-5** Helper `voz.auth.check_context(payload, requested)`:
  - Devuelve `True` si `requested in payload.available_contexts`.
  - Si `requested == "trabajo"` y `payload.sub != "angel"` → `False`.
- **FR-B-6** Endpoint para cambiar contexto activo:
  `POST /voz/api/contexto-set` con body `{"context": "..."}`. Si OK,
  devuelve nuevo JWT con `context` actualizado, misma jti, mismo exp.
  Si scope insuficiente, 403.

### Bloque C — Vault Trabajo aislado (FR-C)

- **FR-C-1** Crear estructura en
  `public_html/knowledge_base/trabajo/`:
  ```
  chantiers/
    INDEX.md
    {slug}/
      INDEX.md
      ppsps.md
      plan-retrait.md
      devis.md
      equipe.yaml
      journal/YYYY-MM-DD.md
  equipe/
    operateurs.yaml
    formations/{operario}/{año}.md
  documents/
    ppsps/{chantier}.md
    plans-retrait/
    devis/
    certificats/
    diag-amiante/
  clients/
    INDEX.md
    {nombre}/
  materiel/
    inventario.yaml
    mantenimiento/
  normes/
    inrs-ed-6262.md
    code-travail.md
    proteccion-individual.md
  formations/
    {operario}/{año}.md
  ```
- **FR-C-2** README.md en `trabajo/` con: dominio, scope JWT requerido,
  vínculo a tools MCP, ejemplo de jerarquía.
- **FR-C-3** Validación path traversal: cualquier acceso a `trabajo/`
  pasa por `voz.auth.check_context(p, "trabajo")` ANTES de tocar disco.
- **FR-C-4** Memorias del contexto Trabajo viven en
  `knowledge_base/claudio/memorias/angel/trabajo/` (separadas de
  `casa/` y `nosvers/`).

### Bloque D — 10 Tools MCP Trabajo (FR-D)

Módulo nuevo `claudio_tools/trabajo.py`. Funciones síncronas, devuelven
`str`. Registradas en `mcp_server.py` con guard de contexto al estar
expuestas vía MCP RPC y vía dictado-procesar.

- **FR-D-1** `chantier_listar(estado: str = "activos") -> str`
  - `estado` ∈ `activos | archivados | urgentes | todos`.
  - Lee `trabajo/chantiers/INDEX.md` + frontmatter de cada chantier.
- **FR-D-2** `chantier_crear(nombre, direccion, cliente, devis_eur, equipe_ids, fecha_inicio, fecha_fin_prev) -> str`
  - Slug del nombre, crea carpeta + INDEX.md + journal/ vacío.
  - Añade entry en `chantiers/INDEX.md`.
- **FR-D-3** `chantier_evento(chantier_id, tipo, descripcion, autor) -> str`
  - `tipo` ∈ `avance | incidente | seguridad | journal | otro`.
  - Append a `chantiers/{slug}/journal/YYYY-MM-DD.md`.
- **FR-D-4** `chantier_estado(chantier_id) -> str`
  - Snapshot: equipo, último evento, días desde inicio, %% según devis.
- **FR-D-5** `equipe_listar() -> str`
  - Lee `equipe/operateurs.yaml`, devuelve activos con cualificaciones.
- **FR-D-6** `equipe_anotar(operario, evento, fecha) -> str`
  - Append a `equipe/formations/{operario}/{año}.md`.
- **FR-D-7** `devis_anotar(cliente, monto_eur, chantier_ref) -> str`
  - Append a `documents/devis/{cliente}.md` (crea si no existe).
- **FR-D-8** `ppsps_crear(chantier_id, version, observaciones) -> str`
  - Crea `documents/ppsps/{chantier}.md` con plantilla mínima.
- **FR-D-9** `documento_trabajo_archivar(tipo, contenido, chantier_ref) -> str`
  - `tipo` ∈ `certificat | diag-amiante | plan-retrait | otro`.
  - Archiva en `documents/{tipo}/{slug}.md`.
- **FR-D-10** `chantier_documento_listar(chantier_id, tipo: str = "todos") -> str`
  - Lista documents asociados a un chantier (devis, ppsps, etc.).

Todas las tools del bloque D:
- Reciben `autor` server-side desde JWT (nunca del cliente).
- Validan `context=trabajo` en JWT (verificación en wrapper, no en la
  función pura — para que tests puedan llamarla directamente).
- Loguean a `claudio/logs/YYYY-MM-DD.jsonl` con `tool`, `args`, `result`.

### Bloque E — Endpoints v3 Trabajo (FR-E)

Nuevo módulo `tablero/v2/api_trabajo.py` o handlers en `tablero/v2/ws.py`:

- **FR-E-1** `GET /tablero/api/v3/trabajo/chantiers?estado=activos`
  → JSON `{chantiers: [...], total: n}`.
- **FR-E-2** `GET /tablero/api/v3/trabajo/chantier/{slug}`
  → JSON snapshot.
- **FR-E-3** `GET /tablero/api/v3/trabajo/equipe`
  → JSON lista operadores.
- **FR-E-4** `GET /tablero/api/v3/trabajo/documents?tipo=ppsps`
  → JSON lista documentos.
- **FR-E-5** Todos validan JWT con `check_context(p, "trabajo")`.
- **FR-E-6** WS canal `trabajo` (worker `trabajo.py`, refresca 60 s,
  publica snapshot `{chantiers_activos: n, alertas: [...], ultimo_evento: {...}}`).

### Bloque F — Endpoints contextuales v2 (FR-F)

Existentes /tablero/api/v2/* aceptan ?context= y filtran:
- **FR-F-1** `GET /tablero/api/v2/timeline?context=casa|nosvers|trabajo`.
- **FR-F-2** `GET /tablero/api/v2/recordatorios?context=...`.
- **FR-F-3** `GET /tablero/api/v2/gastos?context=...&mes=YYYY-MM`.
- **FR-F-4** WS `ws?token=&context=...` filtra canales suscritos al
  contexto del cliente.

### Bloque G — Endpoint /voz/api/dictado-procesar contextual (FR-G)

- **FR-G-1** Acepta `context` desde JWT (NO del body). El cliente PWA
  manda token con `context` ya activo.
- **FR-G-2** Router filtra ALLOWED_TOOLS según contexto:
  - `casa` → 22 tools Fase 1 (whitelist actual).
  - `nosvers` → subset (consultas + agentes + analytics, no familia).
  - `trabajo` → 10 tools nuevos del bloque D + `dia_capturar` fallback.
- **FR-G-3** Si dictado no encaja en contexto activo, fallback a
  `dia_capturar` con `categoria=contexto` (apunta nota en el vault del
  contexto activo).
- **FR-G-4** Compose voice response añade frase contextual:
  - `casa` → tono cariñoso ("Apuntado en casa.").
  - `nosvers` → tono sobrio KPI.
  - `trabajo` → tono francés técnico ("Noté dans Bordeaux-Nord.").

### Bloque H — Home + selector contexto (FR-H)

- **FR-H-1** Saludo según hora local (no UTC).
- **FR-H-2** 3 cards (o 2 si África) con métricas live:
  - Casa: contador recordatorios pendientes hoy (de canal WS).
  - NosVers: total mes en € de canal `revenue`.
  - Trabajo: chantiers activos (de canal `trabajo`).
- **FR-H-3** Card Trabajo bicromática:
  - Mitad izquierda blanca, logo "DI" en negro `font-black tracking-tighter`.
  - Mitad derecha roja `#D62828`, KPI MAYÚSCULAS blancas.
  - Línea negra divisoria 2 px.
- **FR-H-4** Transición de tema con `framer-motion` 200 ms al tocar card.
- **FR-H-5** Footer hint: "o di 'claudio' desde el PC casa".

### Bloque I — Contextos UI (FR-I)

#### Casa — `[data-context="casa"]`
- **FR-I-Casa-1** Bottom tabs (5): Hoy / Listas / Gastar / Recordar / Casa.
- **FR-I-Casa-2** Theme: bg `#FEFAF4` (cálido NosVers), text `#1c1510`,
  acentos amber + verde `#34d399` para CTA.
- **FR-I-Casa-3** Tipografía: Playfair Display titulares + DM Sans cuerpo.
- **FR-I-Casa-4** Reusa canales WS existentes:
  `recordatorios`, `gastos`, `compras`, `medicacion`, `coche`,
  `menu_dia`, `bris`.

#### NosVers — `[data-context="nosvers"]`
- **FR-I-Nos-1** Bottom tabs (5): Hoy granja / Huerto / Tienda · Stripe /
  AAPPMA / Cockpit-mini.
- **FR-I-Nos-2** Theme: bg `#FEFAF4` también (mismo design system), verde
  `#5A7A2E` para acentos primarios + emerald `#10b981` para datos.
- **FR-I-Nos-3** Mismo Playfair + DM Sans + DM Serif Display subtítulos.
- **FR-I-Nos-4** Canales WS: `revenue`, `nosvers_huerto`, `nosvers_aappma`,
  `health` (cockpit-mini).

#### Trabajo — `[data-context="trabajo"]`
- **FR-I-Tra-1** Bottom tabs (4): Aujourd'hui / Chantiers / Équipe / Docs.
- **FR-I-Tra-2** Theme:
  - bg `#FFFFFF` puro + secciones `#000000`.
  - Acento primary `#D62828` (rojo DI).
  - Texto MAYÚSCULAS `font-black tracking-tighter` para titulares.
  - Tipografía: sans-serif condensada (Inter Condensed o Bebas Neue como
    fallback de fuente del sistema; cargar local).
- **FR-I-Tra-3** Header bicromático asimétrico:
  - Mitad blanca con logo DI.
  - Franja roja con label "COND. TRAVAUX" + nombre Angel.
- **FR-I-Tra-4** Cards `border-2 border-black`, headers negro o rojo DI
  con texto blanco MAYÚSCULAS.
- **FR-I-Tra-5** Chips de servicios negro/blanco:
  `DÉSAMIANTAGE`, `DÉPLOMBAGE`, `DÉCONTAMINATION`, `DÉMOLITION`.
- **FR-I-Tra-6** FAB micrófono: círculo rojo DI 64 px con borde negro 3 px,
  icono micrófono blanco.
- **FR-I-Tra-7** Datos: canal WS `trabajo`, endpoints v3.

### Bloque J — PTT hold-to-talk 5 fases (FR-J)

- **FR-J-1** Componente global `<PTTOverlay>` montado en App root,
  visible solo cuando estado != idle.
- **FR-J-2** Estados:
  - `idle` → FAB color del contexto.
  - `recording` → overlay full-screen translúcido, waveform Canvas live
    + timer + hint cancel.
  - `sending` → spinner sutil en lugar del waveform.
  - `thinking` → mini NeuralGraph (homenaje cockpit), 400-1500 ms.
  - `speaking` → ondas radiales + texto + quick replies opcionales.
- **FR-J-3** Gestos:
  - `pointerdown` en FAB + hold ≥ 300 ms → recording.
  - `pointerup` → sending (envía a /voz/api/dictado-procesar).
  - `pointermove` con desplazamiento Y > 80 px ↑ → cancela (vuelve idle,
    no envía).
  - `pointercancel`/`blur` → cancela.
  - Tap simple < 300 ms → toggle (accesibilidad teclado / botón fijo).
  - Doble-tap < 300 ms separación → modo conversación 30 s.
- **FR-J-4** Web Audio: `getUserMedia` audio, `AudioContext`,
  `MediaRecorder` (WebM Opus), `AnalyserNode` para FFT del waveform.
- **FR-J-5** Encoder: WebM Opus → POST como multipart al endpoint, mismo
  shape que `/voz/api/capturar`.
- **FR-J-6** Respuesta speaking: `voice_response.text` mostrado + `audio_url`
  reproducido con `<audio>` (Piper TTS local).
- **FR-J-7** Respeta `prefers-reduced-motion`: sin waveform, solo barra
  de progreso fija.

### Bloque K — Service Worker offline read (FR-K)

- **FR-K-1** Precache shell HTML/CSS/JS al install.
- **FR-K-2** Runtime cache: GET `/tablero/api/v2/*` y
  `/tablero/api/v3/trabajo/*` con stale-while-revalidate.
- **FR-K-3** POST nunca cacheado.
- **FR-K-4** Mensaje "modo offline · lectura" en UI si fetch falla y
  hay cache.

### Bloque L — Caddy vhost (FR-L)

- **FR-L-1** Añadir bloque `claudio.72.61.160.108.nip.io` en
  `/etc/caddy/Caddyfile`.
- **FR-L-2** `root * /home/nosvers/tablero/web-claudio/dist`,
  `try_files {path} /index.html`.
- **FR-L-3** Reverse proxy `/tablero/api/*` y `/voz/api/*` a localhost:8766.
- **FR-L-4** Service Worker `/sw.js` con `Cache-Control: no-cache`.
- **FR-L-5** `request_body max_size 20MB` (audio multipart).

---

## Non-Functional Requirements

- **NFR-1** Latencia PTT: ≤ 2 s desde release hasta primera onda
  speaking. (Stacking previous: ≤ 1.5 s router + 500 ms encode + red.)
- **NFR-2** Cold start PWA: ≤ 1.5 s en Pixel-class Android tras instalado.
- **NFR-3** Bundle: ≤ 2 MB gzip total. Cada chunk de contexto ≤ 300 KB.
- **NFR-4** A11y: contraste AAA en Trabajo (rojo/blanco/negro), AA en
  Casa/NosVers. Touch targets ≥ 48 px.
- **NFR-5** Tests: smoke E2E de los 3 contextos (Playwright o Vitest +
  jsdom); unit tests JWT scope (pytest extends 001).
- **NFR-6** Cero deps cloud nuevas: NO Firebase, NO OneSignal, NO Sentry,
  NO Vercel Analytics.

---

## Out of Scope (Fase 8+)

- Wake-word móvil background (require TWA o Capacitor).
- Push notifications nativas Android.
- Google Calendar OAuth, Stripe webhook real-time, Home Assistant.
- Edición optimista de items desde la UI (mark recordatorio done desde
  PWA) — read-only en esta fase, escritura solo via PTT.
- Multi-tool en un dictado (1 tool por dictado, ver D3 de Fase 2).

---

## Definition of Done

- [x] Sub-dominio `claudio.72.61.160.108.nip.io` sirve la PWA con cert
  Let's Encrypt automático.
- [x] 3 contextos navegables con identidades visuales diferenciadas (Casa
  cálido, NosVers verde tierra, Trabajo bicromático rojo DI).
- [x] PTT hold-to-talk funcional con 5 fases visuales y gestos
  documentados.
- [x] `/voz/api/dictado-procesar` consume `context` desde JWT y filtra
  tools accesibles.
- [x] Vault `knowledge_base/trabajo/` creado con estructura y README.
- [x] 10 tools MCP nuevos del dominio Trabajo registrados en
  `claudio_tools/trabajo.py` y `mcp_server.py`.
- [x] Token Angel emitido con `available_contexts: [casa, nosvers,
  trabajo]`. Token África emitido con `[casa, nosvers]`. Intento de
  África con `context=trabajo` → 403.
- [x] Frontend bundle compilado (`< 2 MB gzip`).
- [x] Service Worker registrado y verificado (offline-lectura).
- [x] Tests: scope JWT (pytest), smoke 3 contextos (Vitest jsdom),
  intent_router con contexto (pytest existente extendido).
- [x] Documentación `knowledge_base/claudio/PWA_CONTEXTOS.md`.
- [x] CHANGELOG / commits agrupados conventional (≤ 10 commits).

---

## Risks & Mitigations

| Riesgo | Impacto | Mitigación |
|---|---|---|
| Bundle excede 2 MB | NFR-3 fail | Lazy-load cada contexto, tree-shake icons, no incluir framer-motion completo |
| Service Worker bloquea actualizaciones | UX rota | `skipWaiting` + `clientsClaim` + bumpear CACHE_NAME en cada release |
| África ve UI Trabajo por bug | Aislamiento roto | Test E2E con JWT África verifica que la card no renderiza ni en DOM |
| iOS no soporta `MediaRecorder` Opus | PTT roto en iOS | Detectar y caer a `audio/mp4` codec; iOS no es target principal pero no romper |
| Caddy renueva cert nip.io | Posible rate-limit | Compartir wildcard si existe; ya hay 5 vhosts nip.io funcionando |

---

*Spec NosVers Claudio Fase 7 — 2026-05-14*
