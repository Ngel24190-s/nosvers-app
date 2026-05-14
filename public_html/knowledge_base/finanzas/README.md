# finanzas/

Gastos, ingresos, cargos recurrentes, presupuesto y alertas.

## Subcarpetas

- `gastos/` — un archivo por mes: `YYYY-MM.md`. Append-only.
- `ingresos/` — un archivo por mes (no usado en Fase 1).

## Archivos raíz

- `recurrentes.yaml` — cargos automáticos (Netflix, seguros, internet…). Alimenta
  `recurrente_alertar()`.
- `presupuesto-mes.md` — presupuesto mensual por categoría.
- `alertas.md` — alertas activas que Claudio quiere mantener visibles.

## Formato gastos

Cada línea:
```
- YYYY-MM-DD HH:MM · MM.NN€ · concepto · categoria · autor
```

Categorías sugeridas: `alimentacion`, `transporte`, `hogar`, `ocio`, `salud`,
`coche`, `nosvers`, `otros`.

## Tools MCP

- `gasto_anotar`, `gastos_resumen`, `recurrente_alertar`

## Privacidad

Información financiera. Tools requieren `autor` explícito.
