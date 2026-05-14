# coche/

El coche de la familia: matrícula, ITV, seguro, mantenimiento, gastos.

## Subcarpetas

- `mantenimiento/` — un `.md` por intervención (taller, fecha, qué se hizo).
- `gastos/` — gastos del coche por mes: `YYYY-MM.md`. Append-only.

## Archivos raíz

- `INDEX.md` — estado vivo del coche en frontmatter:
  ```yaml
  ---
  matricula: ...
  modelo: ...
  kilometros: <int>
  itv_proxima: YYYY-MM-DD
  seguro_renovacion: YYYY-MM-DD
  ultimo_mantenimiento: YYYY-MM-DD
  ---
  ```

## Tools MCP

- `coche_estado`, `coche_evento`

## Automatización relacionada

`automatizaciones/itv_coche_3_meses.yaml` avisa cuando ITV está a < 90 días.
