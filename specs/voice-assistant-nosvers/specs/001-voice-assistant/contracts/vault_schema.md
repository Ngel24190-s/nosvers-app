# Vault Schema Contract — `knowledge_base/` (pool común multi-usuario)

**Feature**: 001-voice-assistant
**Date**: 2026-05-12 (actualizado 2026-05-13 por addendum BRIEF §14)

Esquema canónico de los archivos markdown del asistente. Cualquier
herramienta (PWA, Linux client, agt07_diario, scripts ad-hoc) que
escriba o lea estos archivos MUST respetar este contrato.

Para el detalle de campos, ver `../data-model.md`. Este documento es la
referencia rápida del formato físico.

> **⚠ Addendum multi-usuario (BRIEF §14, 2026-05-13)**
> - El layout pasa de `knowledge_base/angel/...` (segmentado por usuario) a
>   `knowledge_base/...` (pool común). Angel y África comparten diario.
> - Cada nota gana campo `autor` en el frontmatter YAML.
> - El audio incorpora el autor en el sufijo: `HH-MM-SS_{autor}.opus`.
> - Nuevo subárbol `system/speakers/` con embeddings de enrollment para
>   speaker ID (NumPy `.npy`).

---

## Layout

```
knowledge_base/
├── dia/
│   ├── 2026-05-12.md           ← Archivo del día (pool común Angel+África)
│   ├── 2026-05-13.md
│   ├── ...
│   ├── audio/
│   │   ├── 2026-05-12/
│   │   │   ├── 09-23-45_angel.opus
│   │   │   ├── 14-10-02_africa.opus
│   │   │   └── ...
│   │   └── 2026-05-13/
│   └── resumenes/
│       ├── 2026-05-12.md       ← Resumen diario (agrupa por autor)
│       ├── 2026-W19.md         ← Resumen semanal ISO
│       └── ...
├── prompts/
│   ├── clasificar_nota.md
│   ├── resumen_dia.md          ← Usado por agt07_diario
│   └── resumen_semana.md       ← Usado por agt07_diario
└── system/
    └── speakers/               ← Embeddings de enrollment (BRIEF §14.5)
        ├── angel.npy           ← Vector 256-d Resemblyzer
        └── africa.npy
```

---

## Convenciones

- **Encoding**: UTF-8 sin BOM. LF line endings.
- **Frontmatter**: YAML entre vallas `---`. Sin TOML, sin JSON. Compatible
  Obsidian.
- **Fechas**: ISO 8601 con tz `Europe/Paris` (`+02:00` en verano, `+01:00`
  en invierno).
- **Slug de archivo**:
  - Día: `YYYY-MM-DD.md`
  - Audio: `HH-MM-SS_{autor}.opus`  (autor: `angel` | `africa`)
- **Campo `autor` en frontmatter**: requerido en notas nuevas. Las notas
  legacy (sin campo) se normalizan a `autor: angel` al parsearse.
  - Semana: `YYYY-Www.md` (ISO week)
- **Permisos**: archivos `0644`, directorios `0755`. Owner `nosvers:nosvers`.

---

## Lectura/escritura concurrente

Múltiples procesos pueden escribir simultáneamente al mismo archivo
del día (PWA syncing + Linux client + agt07_diario re-leyendo). Reglas:

1. Lock por archivo usando `fcntl.flock(LOCK_EX)` con timeout 5s.
2. Si el lock no se obtiene en 5s, reintento con backoff (1s, 2s, 4s).
3. Tras 3 reintentos fallidos → devolver error `vault_locked` al caller.
4. Lectura usa `LOCK_SH` (compartido) — no bloquea entre lectores.

`voz/vault_io.py` implementa este patrón y es la **única** ruta legítima
de escritura en estos archivos desde código nuevo del asistente.

---

## Validación al escribir (server-side)

Antes de persistir cualquier nota, `voz/vault_io.py` valida:

| Check | Acción si falla |
|---|---|
| `ts` es ISO 8601 válido con tz | Rechazar con `parametro_invalido`. |
| `etiqueta` ∈ enum válido | Normalizar a `otro` y warning en log. |
| `origen` ∈ enum válido | Normalizar a `otro`. |
| `audio` apunta a path existente o `null` | Normalizar a `null` con log. |
| `texto` no vacío tras strip | Rechazar con `input_vacio`. |
| `texto` < 10.000 caracteres | Truncar con `…[truncado]` y warning. |

---

## Inmutabilidad

- Los archivos del día son **append-only** desde el punto de vista lógico,
  salvo el caso de "reordenar por `ts`" al insertar una nota retrasada
  (sync diferido de la PWA). El reorden NO modifica contenido de notas
  existentes, sólo su posición en el archivo.
- Los resúmenes generados por `agt07_diario` son **regenerables**: si el
  agente se vuelve a ejecutar para el mismo día, sobrescribe el archivo
  de resumen completo.

---

## Migración / compatibilidad

- **v1 (esta versión)**: campos del frontmatter listados en data-model §1.
- Si una versión futura añade campos al frontmatter, los lectores antiguos
  deben ignorar campos desconocidos y NO fallar.
- Si una versión futura cambia el formato de manera breaking, se asigna
  versión nueva en cabecera del archivo del día: `# Diario v2 — YYYY-MM-DD`
  y se migra con script idempotente.
