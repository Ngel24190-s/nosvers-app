# Data Model — Fase D Cockpit

> Sin storage nuevo. Entidades en memoria + payloads WS.

## Entidades en memoria (backend)

### Connection
```python
@dataclass
class Connection:
    websocket: WebSocket
    sub: str                  # "angel" | "africa"
    connected_at: float
    subscribed: set[str]      # channels
```

### Broker
```python
class Broker:
    channels: dict[str, set[Connection]]
    connections: set[Connection]

    async def register(conn) -> None
    async def unregister(conn) -> None
    async def subscribe(conn, channel) -> None
    async def unsubscribe(conn, channel) -> None
    async def broadcast(channel, payload: dict) -> None
```

### Worker
```python
class Worker:
    name: str               # "health" | "claude" | ...
    interval_s: float
    last_snapshot: dict | None
    async def tick() -> dict
    async def loop(broker) -> None  # while True: snapshot, diff, broadcast
```

## Mensajes WS — cliente → servidor

```json
{"type": "subscribe", "channel": "health"}
{"type": "unsubscribe", "channel": "health"}
{"type": "ping"}
```

## Mensajes WS — servidor → cliente

### snapshot inicial (al subscribe)
```json
{"type": "snapshot", "channel": "health", "payload": {...}, "ts": 1715607600}
```

### delta (cuando cambia)
```json
{"type": "update", "channel": "health", "payload": {...}, "ts": 1715607602}
```

### pong
```json
{"type": "pong", "ts": 1715607605}
```

### error
```json
{"type": "error", "code": "unknown_channel", "channel": "foo"}
```

## Payloads por canal

### `health`
```json
{
  "cpu_pct": 12.4,
  "ram_pct": 67.1,
  "ram_used_mb": 5388,
  "ram_total_mb": 8023,
  "disk_pct": 73.2,
  "disk_used_gb": 36.5,
  "disk_total_gb": 49.9,
  "load_1": 0.34, "load_5": 0.41, "load_15": 0.39,
  "net_in_kbps": 12.3,
  "net_out_kbps": 8.7,
  "uptime_s": 1843200,
  "cpu_history": [10, 12, 14, 11, 12]  // últimos 30 valores (1 min con paso 2s)
}
```

### `claude`
```json
{
  "state": "online" | "listening" | "offline",
  "service_active": true,
  "last_interaction_ts": 1715607550,
  "tokens_today": 12450,
  "tokens_history": [...]   // últimas 24h, paso 1h, 24 valores
}
```

### `activity`
```json
{
  "lines": [
    {"ts": 1715607600, "unit": "nosvers-mcp", "level": "INFO", "msg": "MCP call dia_capturar"},
    ...
  ]   // ring buffer últimas 50 líneas; deltas envían sólo nuevas
}
```

### `agentes`
```json
{
  "agentes": [
    {"id": "agt01_visual", "state": "idle", "last_run_ts": 1715600000, "last_status": "OK"},
    {"id": "agt02_instagram", "state": "running", "last_run_ts": 1715607580, "last_status": null},
    {"id": "agt04_seo", "state": "error", "last_run_ts": 1715570000, "last_status": "missing_env"},
    ...
  ]
}
```

### `revenue`
```json
{
  "day_eur": 67.50,
  "month_eur": 145.20,
  "target_eur": 600,
  "blocked": false,
  "last_payment": {"amount_eur": 45.00, "desc": "Extrait Vivant", "ts": 1715607000}
}
```

### `aegis`
```json
{
  "last_briefing": {
    "path": "knowledge_base/aegis/briefing_2026-05-13.md",
    "ts": 1715593200,
    "level": "info" | "warn" | "critical",
    "summary": "Resumen primera línea del .md"
  },
  "alerts_active": [
    {"id": "...", "level": "critical", "msg": "..."}
  ]
}
```

### `wake`
```json
{
  "state": "idle" | "listening" | "processing",
  "last_wake_ts": 1715607400,
  "voice_service_active": true
}
```

## Cliente — estado React (Cockpit.tsx)

```ts
interface CockpitState {
  ws: WebSocket | null;
  wsStatus: 'connecting' | 'connected' | 'reconnecting' | 'failed';
  layouts: Layout[];   // react-grid-layout layouts
  health: HealthSnapshot | null;
  claude: ClaudeSnapshot | null;
  activity: ActivityLine[];
  agentes: AgentNode[];
  revenue: RevenueSnapshot | null;
  aegis: AegisSnapshot | null;
  wake: WakeSnapshot | null;
  vaultStats: VaultStatsSnapshot | null;   // viene del REST sync /v2/stats (B+C)
}
```

## Storage cliente

`localStorage["cockpit_layout_<sub>"]` = JSON `Layout[]`
`localStorage["cockpit_sound"]` = `"on" | "off"`
