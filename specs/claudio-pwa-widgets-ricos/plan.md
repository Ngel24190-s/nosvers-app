# Plan — Claudio PWA Widgets Ricos (009)

> /speckit-plan · 2026-05-14

## Estrategia

Ataque en 4 fases secuenciales. Backend primero (workers + tipos) → librería base → tabs. Sin breaking change al PTT/voz porque sólo añadimos archivos y reescribimos contenido interno de cada tab.

### Fase 0 · Inventario (hecho durante /specify)
- 14 tabs identificadas, todas en `tablero/web-claudio/src/components/{casa,nosvers,trabajo}/tabs/`
- Canales WS funcionando: recordatorios, gastos, compras, medicacion, coche, menu_dia, bris, revenue, trabajo, health, agentes
- Canales nuevos a crear: huerto_estado, pedidos_stripe, aappma_stock, clima_neuvic, chantiers_activos, chantiers_agenda, equipe, documentos_trabajo

### Fase 1 · Tipos + librería base widgets (frontend)
Archivos nuevos:
```
src/components/widgets/
  ├── Card.tsx        # auto-estilo por data-context, prop variant
  ├── Stat.tsx        # número grande + label + sublabel opcional
  ├── ListItem.tsx    # icono + texto + meta + onClick opcional
  ├── EmptyState.tsx  # icono + mensaje
  ├── Sparkbar.tsx    # barra progreso horizontal con valor/max
  └── index.ts        # barrel
```

Extender `src/lib/api-types.ts` con interfaces para los 8 canales nuevos + tipos refinados de canales existentes que aún no estaban tipados (medicacion, menu_dia, bris, coche, compras).

### Fase 2 · Workers backend
Crear 8 archivos en `tablero/v2/workers/`. Patrón estándar:
```python
async def <nombre>_tick() -> dict | None:
    try:
        # leer vault
        ...
        if vacío: return _mock()  # mock realista, no empty
        return real
    except Exception:
        return _mock()
```

Registrar todos en `__init__.py::register_all` con intervalos del spec §6.

### Fase 3 · Reescritura de las 14 tabs
Cada tab importa de `widgets/` + usa `useChannel<T>()`. Mantiene firma `export default function XxxTab()`. NO toca shells ni BottomTabs ni ContextSwitcher.

Estética por contexto:
- CASA → `<Card variant="casa">` o automático por `data-context="casa"`
- NOSVERS → `<Card variant="nosvers">` o automático
- TRABAJO → usa clases `di-card`, `di-title`, `di-chip` ya existentes

### Fase 4 · Tests + build + deploy
- Añadir/extender tests en `src/tests/` — render smoke por shell
- `npm run test`
- `npm run build` y comprobar `dist/assets/*.js.gz` < 200 KB
- commit + push
- Reiniciar dev_server VPS
- `curl -I https://claudio.72.61.160.108.nip.io/` → 200

## Decisiones de diseño

1. **Card auto-estilo via DOM**: leer `document.documentElement.dataset.context` en cliente al primer render. Evita prop drilling. Fallback: prop `variant`.
2. **Mock data sólo en workers**, nunca en componentes. Frontend siempre recibe `snapshot` con datos. Si vault falla → mock. Si todo falla → `{empty: true}` y `<EmptyState>` muestra placeholder.
3. **No persistencia escritura**: `WidgetQuickAdd` por ahora sólo POST a endpoint si existe; si no, hace `console.log` y muestra toast "TODO". Persistencia real fuera de scope.
4. **NeuralGraph mini** reusa el componente existente con prop nueva `size={200}`.
5. **clima_neuvic** usa open-meteo (gratis, sin key): `https://api.open-meteo.com/v1/forecast?latitude=45.10&longitude=0.46&current=temperature_2m,weather_code`. Si falla, mock.
6. **chantiers_activos** worker reusa lectura del vault `trabajo/chantiers/*/INDEX.md` (frontmatter ya soportado). Si vault no existe → mock con 3 chantiers (Bordeaux Nord, Limoges Centre, Périgueux Pavillon).

## Archivos a tocar / crear

Frontend nuevo (8 archivos):
- `src/components/widgets/{Card,Stat,ListItem,EmptyState,Sparkbar,index}.{tsx,ts}`
- (api-types.ts extendido)

Frontend modificado (14 tabs + 1 lib):
- 5 tabs casa, 5 tabs nosvers, 4 tabs trabajo
- `src/lib/api-types.ts`

Backend nuevo (8 workers):
- `tablero/v2/workers/{huerto_estado,pedidos_stripe,aappma_stock,clima_neuvic,chantiers_activos,chantiers_agenda,equipe_status,documentos_trabajo}.py`

Backend modificado (1):
- `tablero/v2/workers/__init__.py`

Tests:
- `src/tests/shells.test.tsx` (nuevo)

## Verificación final

```bash
# tests
cd /home/nosvers/tablero/web-claudio && npm run test

# build
npm run build
du -sk dist/assets/*.js | sort -n  # ver el chunk principal

# backend lint
cd /home/nosvers && python -c "from tablero.v2.workers import register_all; register_all()"

# deploy
systemctl restart nosvers-dev-server
curl -fsSI https://claudio.72.61.160.108.nip.io/ | head -1
```
