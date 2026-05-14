# compras/

Lista activa, histórico mensual, despensa.

## Subcarpetas

- `historico/` — un archivo por mes: `YYYY-MM.md` con todo lo comprado.

## Archivos raíz

- `lista_actual.md` — la lista viva. Checkbox por línea. Se vacía al cierre del
  día/semana via `lista_compras_completar`.
- `despensa.yaml` — qué hay en casa (granel, conservas, congelados) — Fase 2+
  para sugerir menús.

## Formato lista_actual.md

```markdown
# Lista de la compra

- [ ] leche · angel · 2026-05-14
- [ ] tomates 1kg · africa · 2026-05-14
```

## Tools MCP

- `lista_compras_añadir`, `lista_compras_ver`, `lista_compras_completar`,
  `despensa_estado`

## Atajos Telegram

`/compra <item>` → añade directamente.
