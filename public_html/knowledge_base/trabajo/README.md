---
nombre: vault-trabajo
contexto: trabajo
scope_jwt_requerido: trabajo
solo_autor: angel
creado: 2026-05-14
fase: 007-claudio-pwa-contextos
---

# Vault Trabajo — DI Environnement

Vault aislado del dominio profesional de Angel: désamiantage, déplombage,
décontamination, démolition.

## Reglas de acceso

- Cualquier escritura/lectura programática pasa por
  `voz.auth.check_context(payload, "trabajo")` ANTES de tocar disco.
- JWT debe llevar `available_contexts` que incluya `trabajo`.
- Solo `sub=angel` puede recibir un token con `trabajo`.
- África NO ve este vault. Si su PWA o bot intentara `?context=trabajo`
  → 403.

## Jerarquía

```
trabajo/
├── chantiers/
│   ├── INDEX.md                       ← lista activos / archivados
│   └── {slug}/
│       ├── INDEX.md                   ← datos del chantier
│       ├── ppsps.md
│       ├── plan-retrait.md
│       ├── devis.md
│       ├── equipe.yaml
│       └── journal/YYYY-MM-DD.md
├── equipe/
│   ├── operateurs.yaml                ← lista operadores + cualifs
│   └── formations/{operario}/{año}.md
├── documents/
│   ├── ppsps/
│   ├── plans-retrait/
│   ├── devis/
│   ├── certificats/
│   └── diag-amiante/
├── clients/
│   ├── INDEX.md
│   └── {nombre}/
├── materiel/
│   ├── inventario.yaml
│   └── mantenimiento/
├── normes/                            ← normativa amianto Francia
│   ├── inrs-ed-6262.md
│   ├── code-travail.md
│   └── proteccion-individual.md
└── formations/
    └── {operario}/{año}.md
```

## Tools MCP asociados (007 §FR-D)

- `chantier_listar(estado)` — activos / archivados / urgentes / todos
- `chantier_crear(...)` — crea slug, INDEX, journal vacío
- `chantier_evento(chantier_id, tipo, descripcion, autor)` — append journal
- `chantier_estado(chantier_id)` — snapshot del chantier
- `chantier_documento_listar(chantier_id, tipo)`
- `equipe_listar()`
- `equipe_anotar(operario, evento, fecha)`
- `devis_anotar(cliente, monto_eur, chantier_ref)`
- `ppsps_crear(chantier_id, version, observaciones)`
- `documento_trabajo_archivar(tipo, contenido, chantier_ref)`

Todos validan `context=trabajo` en wrapper antes de ejecutar.

## Memorias del autor en este contexto

Se guardan separadas en
`knowledge_base/claudio/memorias/angel/trabajo/`. NO se mezclan con
`casa/` ni `nosvers/`.

## Endpoints REST asociados

- `GET /tablero/api/v3/trabajo/chantiers?estado=activos`
- `GET /tablero/api/v3/trabajo/chantier/{slug}`
- `GET /tablero/api/v3/trabajo/equipe`
- `GET /tablero/api/v3/trabajo/documents?tipo=ppsps`
- WS canal `trabajo` con snapshot 60s.

## Ejemplo: PTT desde la PWA

Angel está en contexto Trabajo, tab "Chantiers", abre Bordeaux Nord.
Mantiene pulsado el FAB:

> "Hoy hemos acabado la zona dos del primer piso."

→ router decide `chantier_evento("bordeaux-nord", "avance", "acabada
zona 2 primer piso", "angel")` → `chantiers/bordeaux-nord/journal/
2026-05-14.md` recibe append.

→ TTS responde: "Noté dans Bordeaux Nord."
