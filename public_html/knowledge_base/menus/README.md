# menus/

Recetas, menús de la semana, favoritos.

## Subcarpetas

- `recetas/` — un `.md` por receta con frontmatter `{ingredientes, tiempo,
  dificultad}` + cuerpo con pasos.

## Archivos raíz

- `semana_actual.md` — plan semanal (L-D, comida + cena).
- `favoritos.md` — recetas que la familia siempre quiere repetir.

## Formato receta

```markdown
---
nombre: Tortilla de patatas
ingredientes: [patata, huevo, cebolla, aceite, sal]
tiempo_min: 35
dificultad: facil
fuente: tradicion
---

1. ...
2. ...
```

## Tools MCP

- `menu_sugerir`, `receta_guardar`

## Filtrado

`menu_sugerir` puede filtrar por ingredientes disponibles (cruce con
`compras/despensa.yaml` cuando esté cargada — Fase 2+).
