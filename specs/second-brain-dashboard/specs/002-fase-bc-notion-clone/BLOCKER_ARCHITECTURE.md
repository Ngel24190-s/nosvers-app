# BLOCKER arquitectónico — descubrimiento durante /speckit-implement

**Fecha**: 2026-05-13
**Estado**: pendiente decisión Angel

## El mismatch

El `spec.md` y todos los contratos OpenAPI se escribieron asumiendo:

> "Cada nota es un archivo `.md` independiente bajo `knowledge_base/dia/`.
> El nombre incluye fecha + slug (`2026-05-13-lombrithé.md`). El frontmatter
> contiene autor, fecha, etiquetas, modified_at, etc."

Pero la **realidad de Fase A** es muy distinta:

> Cada día tiene **un único archivo** `dia/<fecha>.md` con N **entradas** dentro,
> cada entrada delimitada por su propio bloque `--- ... ---` frontmatter
> seguido del cuerpo. El timeline ya estaba pivotado por entradas
> (`path = "dia/2026-05-13.md#<ts>"`) en Fase A.

Ejemplo real de `dia/2026-05-13.md`:

```
# Diario — 2026-05-13

---
ts: '2026-05-13T05:40:39.288550+00:00'
autor: angel
etiqueta: otro
origen: otro
audio: null
clasificador_confianza: 0.85
clasificador_modelo: claude-haiku-4-5
---

Test post-restart desde revisión seguridad Opus móvil. Si esta nota aparece, todo el pipeline funciona.

---
ts: '...'
autor: africa
...
---

Otra entrada.
```

## Qué se ve afectado

| US | Estado |
|---|---|
| US1 captura | ✅ OK — `voz.capturar.dia_capturar_impl` ya añade entradas al archivo del día. Mi handler `tablero/v2/capturar.py` puede ser un wrapper fino. |
| US2 editar | ❌ Mismatch — editar una nota = reescribir una entrada dentro del archivo del día. No es PATCH a un archivo, es PATCH a un fragmento. |
| US3 archivar (soft delete) | ❌ Mismatch — no se puede "mover el archivo" porque el archivo tiene varias notas. Habría que extraer la entrada a `dia/archivo/<fecha>-<ts>.md` o añadir `archived_at` inline. |
| US4 vistas múltiples | ✅ OK — el timeline ya devuelve entradas-pivoteadas; las 5 vistas pivotan igual. |
| US5 Ctrl+K | ✅ OK — palette navega a `dia/<fecha>.md#<ts>`. |
| US6 kanban proyectos | ✅ OK (probablemente) — `knowledge_base/proyectos/*.md` se asume 1-archivo-por-proyecto y eso no entra en conflicto con `dia/`. Verificar al implementar. |
| US7 wiki-links | ❌ Mismatch — el "slug" de una nota no es un filename, es `<fecha>#<ts>` o un título. ¿Permitimos `[[2026-05-13#05:40]]`? ¿`[[título]]` resolviendo al primer match? |
| US8 sidebar vault tree | ⚠️ Parcial — el árbol del vault sigue siendo archivos, pero `dia/` solo muestra archivos-por-día. Eso es coherente. El drag-and-drop debería operar sobre archivos completos (días enteros), no entradas. |
| US9 stats | ✅ OK — agrega por autor/etiqueta a nivel entrada (ya pivotado por timeline). |
| US10 infra | ✅ OK — independiente del vault. |
| US11 agentes | ✅ OK — independiente. |
| US12 grafo | ❌ Mismatch — nodos = ¿entradas? ¿archivos? Si entradas, escalas a 10× más nodos. |
| US13 calendar | ✅ OK — independiente. |
| US14 gmail | ✅ OK — independiente. |

## Opciones para Angel

### Opción A — Migrar Fase A a "1 archivo por nota"

Una migración one-shot que parte cada `dia/<fecha>.md` actual en N archivos
`dia/<fecha>-<ts-slug>.md`. Cero pérdida de datos. Después, todo el spec
B+C se implementa como estaba diseñado.

**Pros**: spec fiel, simplicidad para US2/US3/US7/US12, vault más manejable a mano.
**Cons**: migración irreversible, romp toolings que consumen el formato actual (¿agt07_diario? ¿buscar.py?), ~½ día de trabajo de migración + verificación.

### Opción B — Conservar archivos-por-día, adaptar el modelo de B+C

Mantener Fase A intacta. Adaptar B+C para trabajar **a nivel de entrada**:
- US2 editar: PATCH a `dia/<fecha>.md` con `entry_ts` específico → reescribe ese fragmento dentro del archivo del día.
- US3 archivar: o (a) extraer entrada a `dia/archivo/<fecha>-<ts>.md`, o (b) añadir `archived_at` al frontmatter inline y filtrar.
- US7 wiki-links: sintaxis `[[fecha#ts]]` y/o `[[titulo]]` resolviendo a primera entrada que matchea.
- US12 grafo: nodos = entradas (no archivos).
- Concurrencia optimista: `modified_at` a nivel de entrada (inline frontmatter).

**Pros**: cero migración, Fase A funcionando intacta.
**Cons**: spec hay que reescribir las secciones afectadas; complejidad ↑ en helpers; wiki-links menos limpios.

### Opción C — Híbrido: nuevas notas en archivos propios, viejas en día

Nuevas capturas (US1) van a `dia/<fecha>-<ts-slug>.md`. Las viejas siguen
en `dia/<fecha>.md`. El timeline funde ambos. Migración lazy con el tiempo.

**Pros**: sin migración inmediata, spec fiel para las notas nuevas.
**Cons**: dualidad permanente; los wiki-links son inconsistentes (notas viejas vs nuevas); búsqueda tiene que mezclar dos formatos.

## Recomendación

**Opción B** es la más alineada con la Constitución III (vault as SoT — no introducir cambios masivos) y la Constitución V (no regresión). El spec se actualiza para reflejar el modelo entrada-dentro-del-día; el resto del trabajo B+C procede.

## Lo que SÍ se ha implementado (sirve para todas las opciones)

✅ `/speckit-specify`, `/speckit-clarify`, `/speckit-plan`, `/speckit-tasks` completos.
✅ Dependencias instaladas (httpx, google-auth backend; @dnd-kit, d3-force, cmdk, dompurify frontend).
✅ Scaffold `tablero/v2/` creado.
✅ **Foundations backend completas** y testeadas (43 tests verdes en Phase 2):
   - `atomic_write.py` (D-013)
   - `frontmatter.py` (con loader que preserva timestamps como string)
   - `slug_resolver.py` (D-002, D-012)
   - `concurrency.py` (D-003, `If-Match` + 409)
   - `wiki_index.py` (D-004, write-through in-memory)
✅ `conftest.py` arreglado con autouse `VOZ_JWT_SECRET` — los 25 tests Fase A pasan sin env var externo (mejora menor pero útil).

Las foundations sirven para **cualquiera** de las 3 opciones — son helpers genéricos.

## Próximos pasos sugeridos

1. Angel elige A/B/C.
2. Si **B** (recomendada): actualizar `spec.md` US2/US3/US7/US12 con el modelo
   entrada-dentro-del-día, ajustar contratos `nota_editar`, `nota_archivar`,
   `nota_restaurar`, `wiki_index` para usar `(fecha, ts)` como identificador
   compuesto en lugar de path. Re-arrancar `/speckit-implement`.
3. Si **A** o **C**: escribir el migrador o el switch dual antes de seguir.

---

*Identificado durante /speckit-implement Phase 3 (US1), 2026-05-13.*
*Foundations Phase 1 + Phase 2 quedan listas; el resto pausado.*
