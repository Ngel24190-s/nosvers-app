# Quickstart — Second Brain Dashboard Fase A

**Date**: 2026-05-13

How to bring up the dashboard locally, smoke-test it against the real vault, and ship it to the VPS without breaking the existing services.

---

## 1 · Local dev — backend

The backend lives inside the running `nosvers-mcp` process. For dev, you can either:

**Option A — extend the running service** (safe while testing changes):

```bash
# On the VPS
cd /home/nosvers
# Pull in the new tablero/ module + the 3-line mcp_server.py edit, then:
systemctl reload nosvers-mcp || systemctl restart nosvers-mcp
journalctl -u nosvers-mcp -f
# In another shell, smoke:
curl -s http://localhost:8765/tablero/api/health | jq .
```

**Option B — run a dev uvicorn alongside the production one** (recommended while iterating):

```bash
cd /home/nosvers
# Run on a separate port; production keeps :8765.
TABLERO_DEV=1 python3 -c "
from voz.rest import ROUTES as voz_routes
from tablero.rest import ROUTES as tablero_routes
from fastmcp import FastMCP
import uvicorn
mcp = FastMCP('NosVers-dev')
app = mcp.http_app()
for r in voz_routes + tablero_routes:
    app.router.routes.append(r)
uvicorn.run(app, host='127.0.0.1', port=8766, log_level='info')
"
curl -s http://127.0.0.1:8766/tablero/api/health
```

## 2 · Local dev — frontend

```bash
cd /home/nosvers/tablero/web
npm install            # only on first checkout / when package.json changes
npm run dev            # vite on :5173 by default
# Open http://localhost:5173
```

In `tablero/web/.env.development`:

```ini
VITE_API_BASE=http://127.0.0.1:8766
```

The dev vite server proxies `/tablero/api/*` to `VITE_API_BASE` so cookies + JWT work without CORS surprises during dev.

## 3 · Get a JWT for dev

```bash
# On the VPS (or wherever VOZ_JWT_SECRET is set):
python3 -c "
from voz.auth import emitir_token
print(emitir_token('dev-laptop', ttl_days=7, autor='angel')['jwt'])
"
# Paste into the dashboard's login screen.
```

The same flow works for África — swap `autor='africa'`.

## 4 · Smoke-test the backend against the real vault

```bash
TOKEN=$(python3 -c "from voz.auth import emitir_token; print(emitir_token('dev', autor='angel')['jwt'])")

# Health (no auth)
curl -s http://localhost:8765/tablero/api/health | jq .

# Whoami
curl -sH "Authorization: Bearer $TOKEN" http://localhost:8765/tablero/api/whoami | jq .

# Timeline default (last 30 days, both authors)
curl -sH "Authorization: Bearer $TOKEN" \
  http://localhost:8765/tablero/api/timeline | jq '.entradas | length'

# Search
curl -sH "Authorization: Bearer $TOKEN" \
  "http://localhost:8765/tablero/api/buscar?q=lombrith%C3%A9" | jq '.total, .resultados[0]'

# Note detail (use one path from the timeline call above)
curl -sH "Authorization: Bearer $TOKEN" \
  "http://localhost:8765/tablero/api/nota?path=dia/2026-05-13.md%23<urlencoded_ts>" | jq '.nota.body_markdown'
```

If any of these return `{"ok": false}` with a useful `error`, fix the input. If they return 500, check `journalctl -u nosvers-mcp` — the structured logger prints the request id and the exception with stack trace.

## 5 · Smoke against the constitution (Principle V — no regression)

Run before declaring Fase A done:

```bash
# VOZ PWA still works
curl -sH "Authorization: Bearer $TOKEN" http://localhost:8765/voz/api/health | jq .ok

# agt07_diario cron still healthy (latest run today)
ls -lt /home/nosvers/logs/agt07_diario*.log | head -1
tail -20 $(ls -t /home/nosvers/logs/agt07_diario*.log | head -1)

# Telegram bot responding
systemctl is-active nosvers-bot

# WordPress reachable
curl -sI https://nosvers.com/ | head -1
```

All four should pass exactly as before the dashboard deploy.

## 6 · Build the frontend

```bash
cd /home/nosvers/tablero/web
npm run build
# Output → /home/nosvers/tablero/web/dist/
ls -la dist/
```

## 7 · Nginx vhost — tablero.nosvers.com

New file `/etc/nginx/sites-available/tablero.nosvers.com`:

```nginx
# Rate-limit zone, declared once at http{} level — add to nginx.conf if not present:
# limit_req_zone $binary_remote_addr zone=tablero_api:10m rate=20r/s;

server {
    listen 443 ssl http2;
    server_name tablero.nosvers.com;

    ssl_certificate     /etc/letsencrypt/live/tablero.nosvers.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/tablero.nosvers.com/privkey.pem;
    add_header Strict-Transport-Security "max-age=63072000" always;
    add_header X-Content-Type-Options nosniff always;

    root /home/nosvers/tablero/web/dist;
    index index.html;

    # SPA: any unknown route serves index.html, lets React handle it.
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API: proxy to the existing nosvers-mcp uvicorn on :8765.
    location /tablero/api/ {
        limit_req zone=tablero_api burst=10 nodelay;
        proxy_pass         http://127.0.0.1:8765;
        proxy_http_version 1.1;
        proxy_set_header   Host              $host;
        proxy_set_header   X-Real-IP         $remote_addr;
        proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
        proxy_read_timeout 30s;
    }

    # Static attachments (markdown image refs).
    location /attachments/ {
        alias /home/nosvers/public_html/knowledge_base/dia/audio/;
        autoindex off;
        add_header Cache-Control "private, max-age=3600";
    }
}

server {
    listen 80;
    server_name tablero.nosvers.com;
    return 301 https://$host$request_uri;
}
```

Enable + reload:

```bash
ln -s /etc/nginx/sites-available/tablero.nosvers.com /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx
```

## 8 · TLS certificate

```bash
certbot --nginx -d tablero.nosvers.com --non-interactive --agree-tos -m angelvtebaeza@gmail.com
```

(Requires `tablero.nosvers.com` DNS A record pointing to the VPS first.)

## 9 · "Fase A done" checklist

Before notifying the CEO via Telegram:

- [ ] `curl https://tablero.nosvers.com/tablero/api/health` returns 200 `{ok:true}`.
- [ ] Logging in with Angel's token and África's token both produce a non-empty merged timeline.
- [ ] Lighthouse run on the timeline page, Slow-4G profile, TTI ≤ 2 s (SC-001).
- [ ] Section 5 smoke checks all pass (Principle V).
- [ ] No `POST|PUT|PATCH|DELETE` lines exist in `tablero/rest.py` (`grep -E '"(POST|PUT|PATCH|DELETE)"' tablero/rest.py` → empty).
- [ ] An unauthenticated `curl` to `/tablero/api/timeline` returns 401 in under 50 ms (SC-006).

If all green: notify Angel via Telegram (see "Notify CEO" task — and respect the `telegram_enviar` stall workaround: 30 s timeout, 1 retry, then mark `MCP_STALL_FASE_A` and continue).
