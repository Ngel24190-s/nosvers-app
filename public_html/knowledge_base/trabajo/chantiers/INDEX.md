---
nombre: chantiers-index
contexto: trabajo
actualizado: 2026-05-14
---

# Chantiers — DI Environnement

Lista maestra de chantiers. Mantenido por `chantier_crear`,
`chantier_evento` y `chantier_listar`.

## Activos

_(ninguno aún — primer chantier real lo creará Angel desde la PWA)_

## Archivados

_(vacío)_

## Urgentes

_(vacío)_

---

**Plantilla por chantier**: `chantiers/{slug}/INDEX.md` con frontmatter:

```yaml
---
slug: bordeaux-nord
nombre: Bordeaux Nord — Réhabilitation
direccion: 12 rue de la République, 33000 Bordeaux
cliente: Mairie Bordeaux
devis_eur: 84500
equipe_ids: [angel, jose, miguel]
fecha_inicio: 2026-05-20
fecha_fin_prev: 2026-08-15
estado: activo  # activo | archivado | urgente | pausado
servicios: [desamiantage, deplombage]
creado: 2026-05-14
---
```
