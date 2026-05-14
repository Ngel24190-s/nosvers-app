# Tasks — Claudio PWA Contextos (007)

Marcadores: `[ ]` pending · `[~]` in progress · `[x]` done · `[!]` blocker

---

## Bloque A — Backend JWT contextual (T100)

- [x] **T101** `voz/auth.py`:
  - extender `emitir_token(autor, ttl, device_label, contexts)` con default
    `["casa","nosvers","trabajo"]` si autor=angel, `["casa","nosvers"]` si africa
  - validar trabajo solo Angel (`ValueError` si africa pide trabajo)
  - validar valores ∈ {casa, nosvers, trabajo}
  - `validar_token` ya devuelve payload — no toca
  - `check_context(payload, requested) -> bool`
- [x] **T102** Tests `tests/test_auth_contexts.py`:
  - emite token Angel con 3 contextos
  - emite token África con 2 contextos
  - intenta emitir África+trabajo → ValueError
  - check_context Angel trabajo → True
  - check_context África trabajo → False
  - check_context valor inválido → False
  - retro-compat: token viejo sin `available_contexts` → casa OK, nosvers OK, trabajo NO

---

## Bloque B — Vault Trabajo (T110)

- [x] **T111** Crear esqueleto físico vía script:
  ```
  public_html/knowledge_base/trabajo/
  ├── README.md (descripción, scope, ejemplo)
  ├── chantiers/INDEX.md
  ├── chantiers/_ejemplo/INDEX.md
  ├── chantiers/_ejemplo/journal/.gitkeep
  ├── equipe/operateurs.yaml
  ├── equipe/formations/.gitkeep
  ├── documents/{ppsps,plans-retrait,devis,certificats,diag-amiante}/.gitkeep
  ├── clients/INDEX.md
  ├── materiel/inventario.yaml
  ├── normes/inrs-ed-6262.md (stub)
  ├── normes/code-travail.md (stub)
  ├── normes/proteccion-individual.md (stub)
  └── formations/.gitkeep
  ```
- [x] **T112** README.md trabajo con scope JWT, jerarquía, ejemplo PTT.

---

## Bloque C — Tools MCP Trabajo (T120)

- [x] **T121** `claudio_tools/trabajo.py`:
  - imports comunes (slugify, append_md, log_jsonl, vault_root)
  - `_ensure_skeleton()` idempotente
  - `chantier_listar(estado="activos")`
  - `chantier_crear(nombre, direccion, cliente, devis_eur, equipe_ids, fecha_inicio, fecha_fin_prev)`
  - `chantier_evento(chantier_id, tipo, descripcion, autor)`
  - `chantier_estado(chantier_id)`
  - `chantier_documento_listar(chantier_id, tipo="todos")`
  - `equipe_listar()`
  - `equipe_anotar(operario, evento, fecha)`
  - `devis_anotar(cliente, monto_eur, chantier_ref)`
  - `ppsps_crear(chantier_id, version, observaciones)`
  - `documento_trabajo_archivar(tipo, contenido, chantier_ref)`
- [x] **T122** Registrar los 10 tools en `mcp_server.py` (decorar con
  `@mcp.tool()`).
- [x] **T123** Tests `tests/test_trabajo_tools.py` (mínimo 8 casos:
  crear chantier + listar lo encuentra, evento se persiste, estado
  refleja último evento, equipe listar vacía OK, devis anotar crea
  cliente nuevo, ppsps crear con versión, document archivar tipo OK,
  slug normalizado).

---

## Bloque D — Endpoints v3 + Worker WS (T130)

- [x] **T131** `tablero/v2/api_trabajo.py`:
  - `GET /tablero/api/v3/trabajo/chantiers?estado=`
  - `GET /tablero/api/v3/trabajo/chantier/{slug}`
  - `GET /tablero/api/v3/trabajo/equipe`
  - `GET /tablero/api/v3/trabajo/documents?tipo=`
  - Todos validan `check_context(p, "trabajo")`
- [x] **T132** Montar `routes_v3` en `tablero/v2/__init__.py` o `ws.py`.
- [x] **T133** `tablero/v2/workers/trabajo.py` snapshot 60 s.
- [x] **T134** Extender `VALID_CHANNELS` en `tablero/v2/ws.py` con
  `"trabajo"`. WS handler verifica `?context=trabajo` y JWT scope antes
  de aceptar suscripción.
- [x] **T135** Extender `tablero/v2/workers/__init__.py` para registrar
  trabajo worker.

---

## Bloque E — Intent Router contextual (T140)

- [x] **T141** `voz/intent_router.py`:
  - kwarg `contexts_permitidos: set[str] | None = None`
  - construir prompt con tools_visibles
  - validar decision.tool ∈ contexts_permitidos
- [x] **T142** `voz/rest.py` `dictado_procesar_handler`:
  - leer `X-Claudio-Context` header (fallback "casa")
  - `check_context(payload, ctx)` → 403 si no
  - pasar `TOOLS_POR_CONTEXTO[ctx]` al router
- [x] **T143** Test `tests/test_intent_router_context.py`:
  - contexto trabajo + dictado "apunta 30 de gasolina" → fallback (tool
    de casa NO accesible) → dia_capturar en trabajo/
  - contexto casa + dictado "crea chantier X" → fallback (tool trabajo
    no accesible) → dia_capturar en familia/
  - contexto trabajo + dictado "hoy hemos acabado zona 2" →
    chantier_evento

---

## Bloque F — Caddy vhost (T150)

- [x] **T151** Backup Caddyfile (`/etc/caddy/Caddyfile.bak-YYYYMMDD`).
- [x] **T152** Añadir bloque
  `claudio.72.61.160.108.nip.io { ... }` al final.
- [x] **T153** Validar config: `caddy validate --config /etc/caddy/Caddyfile`.
- [x] **T154** Reload tras build del frontend (NO antes de tener dist/):
  `systemctl reload caddy`.

---

## Bloque G — PWA scaffold (T160)

- [x] **T161** `mkdir -p tablero/web-claudio/{src/{lib,components,styles,tests},public}`.
- [x] **T162** `package.json`, `vite.config.ts`, `tailwind.config.ts`,
  `postcss.config.js`, `tsconfig.json`, `index.html`.
- [x] **T163** `npm install` (resolverá ~250 deps; aceptar 3-5 min).
- [x] **T164** `public/manifest.json` con name "Claudio", short_name
  "Claudio", icons 192/512 (placeholders SVG), theme_color por contexto
  default `#5A7A2E`.
- [x] **T165** `public/sw.js` manual:
  - install: precache shell.
  - fetch GET API → stale-while-revalidate.
  - fetch POST → bypass.
  - message `SKIP_WAITING` → `self.skipWaiting()`.
- [x] **T166** `public/icon-192.svg` + `public/icon-512.svg` placeholder
  (SVG inline "C" en verde NosVers, después Angel pone PNG real).

---

## Bloque H — PWA core libs (T170)

- [x] **T171** `src/lib/auth.ts`:
  - `getToken() / setToken(t) / clearToken()` (localStorage).
  - `decodeJwt(t)` (parse claims sin verificar; cliente confía en backend).
  - `getAvailableContexts()` del JWT.
- [x] **T172** `src/lib/api.ts`:
  - `apiFetch(path, opts)` añade `Authorization: Bearer ${token}` y
    `X-Claudio-Context: ${currentContext}`.
  - 401 → `clearToken()` + redirect.
- [x] **T173** `src/lib/context.ts`:
  - `ContextProvider`, `useContext()` hook.
  - Aplica `document.documentElement.dataset.context = current`.
  - Persiste `localStorage.claudio.context`.
- [x] **T174** `src/lib/ws.ts`:
  - `useWebSocket(channel)` reusable, abre WS con `?token=&context=`.
- [x] **T175** `src/lib/audio.ts`:
  - `recordStart()` → `{ mediaRecorder, analyser, chunks }`.
  - `recordStop()` → Blob WebM.
  - `analyserSnapshot(analyser)` → Float32Array para waveform.
- [x] **T176** `src/lib/api-types.ts`:
  - `TimelineItem`, `ChantierResumen`, `Operario`, `Documento`,
    `Recordatorio`, `Gasto`, etc.

---

## Bloque I — PWA styles (T180)

- [x] **T181** `src/styles/index.css` Tailwind imports + variables CSS
  base.
- [x] **T182** `src/styles/themes.css` con `[data-context="casa"]`,
  `[data-context="nosvers"]`, `[data-context="trabajo"]` cada uno
  redefiniendo `--bg`, `--fg`, `--primary`, `--accent`, `--border`,
  `--on-primary`, `--font-display`, `--font-body`.
- [x] **T183** `tailwind.config.ts` extiende theme con
  `colors: { bg: 'var(--bg)', ... }` y `fontFamily: { display:
  'var(--font-display)', ... }`.

---

## Bloque J — Home + ContextSwitcher (T190)

- [x] **T191** `src/components/home/HomeScreen.tsx` con saludo dinámico
  + 3 cards (filtra `available_contexts`).
- [x] **T192** `CardCasa.tsx` con métrica live "recordatorios pendientes"
  vía WS canal `recordatorios`.
- [x] **T193** `CardNosVers.tsx` con métrica € mes vía WS canal `revenue`.
- [x] **T194** `CardTrabajo.tsx` bicromático (mitad blanca DI + mitad
  roja #D62828 con KPI chantiers).
- [x] **T195** `ContextSwitcher.tsx` discreto en header (para volver a
  Home desde un contexto).

---

## Bloque K — Contextos Casa, NosVers (T200)

- [x] **T201** `CasaShell.tsx` + BottomTabs 5 entries.
- [x] **T202** `casa/tabs/Hoy.tsx` (eventos del día desde
  /tablero/api/v2/timeline?context=casa).
- [x] **T203** `casa/tabs/Listas.tsx` (lista compras desde
  /tablero/api/v2/lista_compras).
- [x] **T204** `casa/tabs/Gastar.tsx` (gastos mes).
- [x] **T205** `casa/tabs/Recordar.tsx` (recordatorios).
- [x] **T206** `casa/tabs/Casa.tsx` (settings + logout).
- [x] **T207** `NosVersShell.tsx` + BottomTabs 5 entries.
- [x] **T208** `nosvers/tabs/HoyGranja.tsx`.
- [x] **T209** `nosvers/tabs/Huerto.tsx`.
- [x] **T20A** `nosvers/tabs/Tienda.tsx` (€ Stripe del worker revenue).
- [x] **T20B** `nosvers/tabs/AAPPMA.tsx` (placeholder, dato low priority).
- [x] **T20C** `nosvers/tabs/CockpitMini.tsx` (resumen 3-4 KPIs).

---

## Bloque L — Contexto Trabajo (T210)

- [x] **T211** `TrabajoShell.tsx` con header bicromático asimétrico +
  BottomTabs 4 entries.
- [x] **T212** `trabajo/tabs/Aujourdhui.tsx` (chantier hoy + último evento).
- [x] **T213** `trabajo/tabs/Chantiers.tsx` (lista cards
  `border-2 border-black`, chips DÉSAMIANTAGE etc.).
- [x] **T214** `trabajo/tabs/Equipe.tsx` (lista operadores).
- [x] **T215** `trabajo/tabs/Docs.tsx` (PPSPS, devis, etc. categorizados).
- [x] **T216** Estilos específicos: clase utilitaria `.di-card`,
  `.di-chip`, `.di-header-stripe` en `themes.css`.

---

## Bloque M — PTT overlay (T220)

- [x] **T221** `PTTFab.tsx` botón flotante con color/borde según contexto
  (`var(--primary)`, borde negro en trabajo).
- [x] **T222** `PTTOverlay.tsx` state machine 5 fases con framer-motion
  transiciones.
- [x] **T223** `Waveform.tsx` Canvas + AnalyserNode FFT → barras vertical.
- [x] **T224** `NeuralGraph.tsx` SVG con 6 nodos y líneas pulsantes
  (homenaje cockpit, simple).
- [x] **T225** Gestos:
  - pointerdown (hold 300 ms) → recording
  - pointermove dy > -80 px → "cancel hint" visible; release → cancel
  - pointerup normal → sending
  - double-tap < 300 ms → conversación 30 s
- [x] **T226** Fetch POST `/voz/api/dictado-procesar` con body
  `{transcript, context}`, headers JWT + `X-Claudio-Context`.
- [x] **T227** Reproducir audio respuesta (`<audio src={audio_url}>`,
  autoplay tras gesto del usuario).
- [x] **T228** `prefers-reduced-motion` → sin waveform animado, barra
  progress simple.

---

## Bloque N — Build + deploy (T230)

- [x] **T231** `cd tablero/web-claudio && npm run build`.
- [x] **T232** Verificar `dist/` tamaño total y bundle gzip < 2 MB.
- [x] **T233** `caddy validate --config /etc/caddy/Caddyfile`.
- [x] **T234** `systemctl reload caddy`.
- [x] **T235** Smoke curl
  `https://claudio.72.61.160.108.nip.io` → 200 HTML.
- [x] **T236** Smoke curl
  `https://claudio.72.61.160.108.nip.io/sw.js` → 200 con header `Cache-Control: no-cache`.
- [x] **T237** Smoke curl
  `https://claudio.72.61.160.108.nip.io/manifest.json` → 200 JSON válido.

---

## Bloque O — Tests (T240)

- [x] **T241** `tests/test_auth_contexts.py` (T102 ya cubierto, mover aquí).
- [x] **T242** `tests/test_trabajo_tools.py` (T123, mover aquí).
- [x] **T243** `tests/test_intent_router_context.py` (T143 mover aquí).
- [x] **T244** Vitest `src/tests/home.test.tsx`:
  - Render con JWT Angel → 3 cards.
  - Render con JWT África → 2 cards (no Trabajo en DOM).
- [x] **T245** Vitest `src/tests/ptt.test.tsx`:
  - State machine transitions correctas.
  - Cancel gesture funciona.
- [x] **T246** Vitest `src/tests/context-scope.test.tsx`:
  - apiFetch añade `X-Claudio-Context`.
  - 403 → no crash, UI muestra estado scope.

---

## Bloque P — Docs + commits (T250)

- [x] **T251** `public_html/knowledge_base/claudio/PWA_CONTEXTOS.md`:
  - Cómo emitir tokens (script).
  - Cómo añadir un tool al contexto trabajo.
  - Cómo añadir un widget al contexto Casa o NosVers.
  - Cómo editar themes.
  - Caddy vhost reload.
- [x] **T252** `npm scripts` y `Makefile` opcional para build/deploy.
- [x] **T253** Commits agrupados (conventional, ~8):
  - `feat(007-auth): JWT con available_contexts y check_context`
  - `feat(007-vault): vault trabajo aislado con estructura inicial`
  - `feat(007-tools): 10 tools MCP del contexto trabajo`
  - `feat(007-api): endpoints v3 trabajo + worker WS`
  - `feat(007-router): intent_router filtra tools por contexto`
  - `feat(007-pwa): scaffold Vite+React+TS+Tailwind con 3 themes`
  - `feat(007-pwa): home + contextos Casa NosVers Trabajo`
  - `feat(007-ptt): PTT hold-to-talk 5 fases con waveform`
  - `feat(007-deploy): Caddy vhost claudio.* + build inicial`
  - `docs(007): PWA_CONTEXTOS.md`

---

## Notas operativas

- Bug `telegram_enviar`: no se invoca. Si la verificación final lo
  necesitase, abortar tras 30 s y marcar el task como
  `[!] MCP_STALL_RESOLVED_BY_OPUS_MOBILE`.
- Tras cada bloque, ejecutar tests del bloque antes de pasar al siguiente.
- Para el frontend, `npm install` puede tardar ~5 min — paciencia, no
  reintentar prematuramente.
- Service Worker: bumpear `CACHE_NAME` (`claudio-pwa-v1`,
  `claudio-pwa-v2`...) cada deploy.

---

*Tasks NosVers Claudio Fase 7 — 2026-05-14*
