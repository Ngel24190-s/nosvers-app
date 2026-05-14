# claudio/

Casa de Claudio: su identidad, su personalidad, sus memorias, sus logs.

## Archivos raíz

- `IDENTIDAD.md` — constitución. Lo edita solo Angel. Versión 1.0 vigente.
- `personalidad.md` — 5 modos (familia, negocio, técnico, salud, finanzas).

## Subcarpetas

- `memorias/angel/` — hechos personales de Angel, por mes (`YYYY-MM.md`).
- `memorias/africa/` — idem África.
- `memorias/compartido/` — hechos del núcleo familiar (anécdotas, decisiones
  compartidas, etc.).
- `conocimiento/` — fichas estables: `nucleo_familiar.md`, `bris.md`,
  `casa.md`, `coche.md`, `abuelos.md`. Léelas al cargar contexto.
- `logs/` — JSONL por día: cada llamada a tool con `{ts, tool, autor, args, ok}`.
  Ojo: contenido sensible NO se loguea (sólo metadatos).

## Tools MCP

- `claudio_recordar` — añade hecho a memorias del autor.
- `claudio_contexto` — recupera memorias relevantes para una query.

## Principio

Si Claudio desaparece mañana, esta carpeta queda. Es markdown legible. Es la
diferencia entre depender de un servicio y tener una memoria propia.
