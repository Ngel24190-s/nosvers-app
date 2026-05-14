# BRIEF — Claudio PWA Contextos (Proyecto 007)

PWA móvil familiar instalable. **3 contextos isolated** (Casa, NosVers, Trabajo) con scope JWT estricto, identidades visuales diferenciadas, PTT hold-to-talk como interfaz principal. Es la cara móvil de Claudio.

## Por qué AHORA

Pre-requisitos cumplidos:
- 001 voice-assistant ✓ (Piper TTS español, faster-whisper, JWT auth)
- 002 cockpit ✓ (workers WS, broker)
- 005 Claudio Mayordomo Fase 1 ✓ (22 tools MCP + vault familiar)
- 006 Fase 2+3 ✓ (intent_router + endpoint /voz/api/dictado-procesar + 7 widgets cockpit)
- Decisión visual: rojo DI #D62828 para contexto Trabajo, cálido amber para Casa, emerald para NosVers
- Decisión scope: Trabajo aislado, NO compartido con África

## Arquitectura

### Subdomain
`https://claudio.72.61.160.108.nip.io` (PWA propia, NO se mezcla con tablero/cockpit existentes).

### Stack frontend
- Vite + React + TypeScript (mismo stack que tablero/web)
- Tailwind con 3 theme tokens distintos por contexto
- framer-motion (animaciones de fase PTT y transiciones de contexto)
- lucide-react (iconos)
- PWA: manifest.json + service worker (offline-first para gastos/lista del mes)
- Instalable como app Android desde Chrome (banner "Añadir a inicio")

### Stack backend (extensión, no nuevo proyecto)
- Endpoints existentes /voz/api/* y /tablero/api/v2/* son la base
- AÑADIR: endpoint `POST /voz/api/dictado-procesar` ya existe — solo necesita aceptar `context` en JWT o body
- AÑADIR: nuevo namespace `/tablero/api/v3/trabajo/*` para tools del contexto Trabajo
- Vault NUEVO: `public_html/knowledge_base/trabajo/` (aislado, solo accesible si JWT tiene context=trabajo)

### Identidad por contexto

| Contexto | Color principal | Acento | Tipografía | Tono Claudio |
|---|---|---|---|---|
| **Casa** | amber/stone/emerald | verde NosVers `#34d399` | serif titular + sans body | cariñoso, paciente |
| **NosVers** | verde tierra + ocres | emerald `#10b981` | mismo + monospace datos | sobrio, KPI |
| **Trabajo** | rojo DI `#D62828` + blanco + negro | rojo DI | sans condensada MAYÚSCULAS | preciso, francés técnico |

### JWT contextual
Token ampliado: `{sub: angel|africa, context: casa|nosvers|trabajo, exp, ...}`. Backend filtra:
- Tools MCP accesibles según contexto
- Vault paths accesibles según contexto
- Memorias `claudio/memorias/{autor}/{contexto}/` separadas

África NO recibe token con context=trabajo. Si lo intenta, 403.

## Pantallas

### Home (entry point)
- Saludo según hora ("Buenos días, Angel" / "Buenas tardes")
- **3 cards grandes verticales**, una por contexto:
  - Casa: gradient amber→orange + icono Home + resumen "2 cosas hoy"
  - NosVers: gradient emerald→lime + icono Sprout + resumen "387€ mes · 3 pedidos"
  - Trabajo: **DISEÑO BICROMÁTICO** mitad blanca con logo DI + mitad roja con estadística — homenaje a la furgoneta del usuario
- Footer: hint "o di 'claudio' desde el PC casa"

### Contexto Casa
5 tabs bottom: Hoy / Listas / Gastar / Recordar / Casa
Widget content reutiliza datos del cockpit Fase 3 vía mismo broker WS pero rediseñado mobile-first (cards grandes, no grid).

### Contexto NosVers
5 tabs: Hoy granja / Huerto / Tienda · Stripe / AAPPMA / Cockpit-mini
Reusa datos existentes nosvers/ + analytics/ + agentes/.

### Contexto Trabajo (estética DI)
4 tabs: Aujourd'hui / Chantiers / Équipe / Docs
**Estilo distintivo**:
- Header bicromático asimétrico (mitad blanca con logo DI + franja roja con "Cond. travaux")
- Cards con `border-2 border-black` (líneas negras gruesas)
- Headers de cards en negro o rojo DI con texto blanco MAYÚSCULAS
- Tipografía `font-black` peso 900 + `tracking-tighter`
- Servicios como chips negros con texto blanco: DÉSAMIANTAGE, DÉPLOMBAGE, etc.
- FAB micrófono ROJO DI con borde negro

### PTT (Push-to-Talk) overlay

Componente global accesible desde TODAS las tabs. Estados:
1. **Idle**: FAB color del contexto activo
2. **Recording**: hold-to-talk con waveform en vivo (Canvas + Web Audio AnalyserNode), timer, slide-up cancel
3. **Sending**: spinner sutil
4. **Thinking**: mini NeuralGraph (homenaje cockpit)
5. **Speaking**: ondas radiales + texto respuesta visible + audio Piper reproduciendo + quick replies

Gestos:
- Hold FAB = grabar mientras pulsas
- Tap simple = toggle (accesibilidad)
- Slide arriba mientras grabas = cancelar
- Doble tap = modo conversación 30s

### Backend que la PWA consume
- `POST /voz/api/dictado-procesar` (ya existe, retorna intent + voice_response + audio_url Piper)
- `GET /tablero/api/v2/timeline?context=casa|nosvers|trabajo`
- `GET /tablero/api/v2/recordatorios?context=...`
- `GET /tablero/api/v2/gastos?context=...&mes=YYYY-MM`
- `GET /tablero/api/v2/lista_compras` (solo casa)
- `GET /tablero/api/v3/trabajo/chantiers` (solo si context=trabajo)
- `GET /tablero/api/v3/trabajo/equipe` (solo si context=trabajo)
- `GET /tablero/api/v3/trabajo/documents` (solo si context=trabajo)
- WS `/tablero/api/v2/ws?token=&context=...` con canales filtrados según contexto

## Vault Trabajo (NUEVO, aislado)

`public_html/knowledge_base/trabajo/`:
```
chantiers/
├── INDEX.md (lista activos + archivados)
├── bordeaux-nord/
│   ├── INDEX.md (datos del chantier)
│   ├── ppsps.md
│   ├── plan-retrait.md
│   ├── devis.md
│   ├── equipe.yaml
│   └── journal/YYYY-MM-DD.md
└── ...
equipe/
├── operateurs.yaml (lista con cualificaciones)
└── formations/
documents/
├── ppsps/{chantier}.md
├── plans-retrait/
├── devis/
├── certificats/
└── diag-amiante/
clients/
├── INDEX.md
└── {nombre}/
materiel/
├── inventario.yaml
└── mantenimiento/
normes/  (normativa amianto Francia)
├── inrs-ed-6262.md
├── code-travail.md
└── proteccion-individual.md
formations/
└── {operario}/{año}.md
```

## Tools MCP nuevos (Trabajo)

Añadir al mcp_server.py, condicionados por context=trabajo en JWT:
- `chantier_listar(estado=null)` → activos / archivados / urgentes
- `chantier_crear(nombre, direccion, cliente, devis_eur, equipe_ids, fecha_inicio, fecha_fin_prev)`
- `chantier_evento(chantier_id, tipo, descripcion, autor)` → journal entry
- `chantier_estado(chantier_id)` → snapshot completo
- `equipe_listar()` → operateurs activos
- `equipe_anotar(operario, evento, fecha)` → formaciones, ausencias
- `devis_anotar(cliente, monto_eur, chantier_ref)`
- `ppsps_crear(chantier_id, version, observaciones)`
- `documento_trabajo_archivar(tipo, contenido, chantier_ref)`

**~10 tools nuevos** del dominio Trabajo, scope JWT estricto.

## Constraints

- NO romper NADA existente (PWA voz, tablero, cockpit, automatizaciones)
- Scope JWT: context=trabajo solo para Angel (verificación double-check en backend)
- Memorias trabajo NO accesibles desde otros contextos
- Service Worker offline-first para datos consultados, NO para escrituras (que requieren conectividad)
- Soberanía: cero dependencias cloud nuevas, todo self-hosted
- Tests: smoke E2E de los 3 contextos, JWT scope, PTT mockup integration test
- Bug telegram_enviar conocido: NO usar telegram_enviar intermedio
- Settings.json global ya tiene auto-approve

## Flujo Spec Kit

1. `/speckit-specify` desde este BRIEF
2. `/speckit-clarify` — solo si crítico
3. `/speckit-plan` — Vite project setup, theme tokens, JWT extension, scope filters
4. `/speckit-tasks` — agrupado por: PWA scaffold, home + 3 contexts, PTT component, backend extensions, vault trabajo, tools MCP trabajo
5. `/speckit-implement` — ejecuta sin parar

## Definition of Done

- PWA en `claudio.72.61.160.108.nip.io` (Caddy vhost añadido + cert)
- 3 contextos navegables con identidades visuales diferenciadas
- PTT hold-to-talk funcional (5 fases visuales)
- Endpoint /voz/api/dictado-procesar consumido correctamente con contexto
- Vault trabajo/ creado con README + estructura
- 10 tools MCP nuevos del dominio trabajo
- Token Angel emitido con multi-context (puede cambiar entre los 3)
- Token África emitido con solo {casa, nosvers}
- Frontend bundle compilado (< 2MB total)
- Service Worker registrado (offline lectura)
- Tests pasando
- Documentación claudio/PWA_CONTEXTOS.md

## Estimación

Humano: 3-4 semanas. Claude Code: 5-7h.

## Roadmap restante

- Fase 8 (futura): wake word móvil en background (Android nativo via TWA o Capacitor)
- Fase 9: integraciones externas (weather, Google Calendar OAuth, Stripe webhook real, Home Assistant)
- Fase 10: pro-actividad (Claudio toma iniciativas)

---
*BRIEF preparado por Claude Opus 4.7 (sesión móvil), 2026-05-14 ~13:10 UTC*
