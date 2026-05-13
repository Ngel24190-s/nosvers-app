# Research — Fase D Cockpit

## R-001 — WebSocket en Starlette + uvicorn (status: native)

Starlette expone `WebSocket` desde `starlette.websockets`. uvicorn 0.x soporta
`ws_protocol="auto"`. No requiere libs adicionales. El binding `Route` cambia a
`WebSocketRoute`. Lifecycle:

```python
from starlette.routing import WebSocketRoute
from starlette.websockets import WebSocket, WebSocketDisconnect

async def ws_handler(websocket: WebSocket):
    token = websocket.query_params.get("token")
    sub = validar_token(token)
    if not sub:
        await websocket.close(code=4401)
        return
    await websocket.accept()
    # broker.register(websocket, sub)
    try:
        while True:
            msg = await websocket.receive_json()
            ...
    except WebSocketDisconnect:
        # broker.unregister(websocket)
        pass

ROUTES.append(WebSocketRoute("/tablero/api/v2/ws", ws_handler))
```

## R-002 — psutil bloqueante en cpu_percent

`psutil.cpu_percent(interval=1)` bloquea 1s (necesita 2 muestras). Solución:
llamar `cpu_percent(interval=None)` dos veces separadas por `await asyncio.sleep(1)`.
Primera llamada retorna 0.0 (sin baseline); usar workaround del warm-up al startup.

```python
import psutil
# warm-up al startup
psutil.cpu_percent(interval=None)

# en el worker
async def health_tick():
    cpu = psutil.cpu_percent(interval=None)   # no bloquea
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    net = psutil.net_io_counters()
    load = os.getloadavg()
    return {
        "cpu_pct": cpu,
        "ram_pct": ram.percent,
        "ram_used_mb": ram.used // 1024 // 1024,
        "ram_total_mb": ram.total // 1024 // 1024,
        "disk_pct": disk.percent,
        "disk_used_gb": disk.used / 1e9,
        "disk_total_gb": disk.total / 1e9,
        "load_1": load[0], "load_5": load[1], "load_15": load[2],
        "net_in_kbps": net.bytes_recv,   # delta calculado luego
        "net_out_kbps": net.bytes_sent,
        "uptime_s": int(time.time() - psutil.boot_time()),
    }
```

## R-003 — Tremor 3.x + Tailwind dark mode

Tremor expone `<DonutChart />`, `<SparkAreaChart />`, `<BarList />`, `<Card />`,
`<Metric />`. Por defecto soporta `dark:` Tailwind. Theming: `colors={['emerald','orange','violet']}`.

Tamaño: ~80KB gzipped. Compatibility: Tailwind 3+ ✅ (tenemos 3.4).

## R-004 — react-grid-layout 1.5

API:
```jsx
<ResponsiveGridLayout
  className="cockpit-grid"
  layouts={{ lg: layout }}
  breakpoints={{ lg: 1200, md: 768, sm: 480 }}
  cols={{ lg: 12, md: 8, sm: 4 }}
  rowHeight={80}
  onLayoutChange={(curr, all) => persistLayout(all)}
>
  <div key="claude-status"><ClaudeStatusWidget /></div>
  ...
</ResponsiveGridLayout>
```

CSS: importar `react-grid-layout/css/styles.css` y `react-resizable/css/styles.css`.

## R-005 — framer-motion 11 con AnimatePresence

```jsx
<motion.div
  initial={{ opacity: 0, y: 20 }}
  animate={{ opacity: 1, y: 0 }}
  transition={{ duration: 0.4, delay: index * 0.05 }}
>
  <WidgetCard>...</WidgetCard>
</motion.div>
```

Stagger via `staggerChildren` en `motion.div` padre con `variants`.

## R-006 — Activity Stream via journalctl

`journalctl --follow -u nosvers-mcp -u nosvers-voice -u nosvers-bot --output=json --no-pager`
emite una línea JSON por evento. Subprocess `asyncio.create_subprocess_exec` + iterar
`process.stdout`. Cada línea: parse JSON, extraer `__REALTIME_TIMESTAMP`, `_SYSTEMD_UNIT`,
`MESSAGE`. Nivel inferido de `PRIORITY` (0-7 syslog).

## R-007 — Stripe SDK Python opcional

Si `STRIPE_SECRET_KEY` está en `.env`, usar `stripe` (`pip install stripe`).
`stripe.Charge.list(limit=10, created={"gte": today_ts})`. Computa total.

Si no está, worker retorna `{day_eur: 0, month_eur: 0, blocked: true}` y el
widget renderiza "BLOCKED_OAUTH_HUMAN".

## R-008 — Hot-reload del cockpit en dev

Vite dev server: `cd tablero/web && VITE_API_BASE=http://localhost:8765 npm run dev`.
WS: el cliente conecta a `ws://localhost:8765/tablero/api/v2/ws?token=...`.
CORS: `_allowed_origin()` ya considera `localhost:5173` cuando `TABLERO_DEV=1`.

## R-009 — Bundle size budget

Antes (Fase B+C): 684K minified. Después esperado:
- framer-motion: +50K
- @tremor/react: +80K (con tree-shake real, +120 sin)
- react-grid-layout: +50K
- cva: +1K
- tailwindcss-animate: +0K (sólo CSS)
- sonner: +6K

Total estimado: +187K → ~870K. Con codesplit lazy del cockpit, la ruta `/`
descarga sólo Fase B+C (684K) y `/cockpit` descarga delta de 187K + base 684K = 871K.

Target FR-014: ≤ 1.5MB. Cumple con margen 60%.
