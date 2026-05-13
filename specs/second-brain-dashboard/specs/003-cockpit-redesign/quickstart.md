# Quickstart — Cockpit (Fase D)

## Local dev

```bash
# Backend (instala psutil en venv del MCP)
pip install psutil

# Levantar backend (ya corre como service)
systemctl restart nosvers-mcp

# Frontend dev (Vite)
cd /home/nosvers/tablero/web
npm install
TABLERO_DEV=1 VITE_API_BASE=http://localhost:8765 npm run dev
# abrir http://localhost:5173/cockpit
```

## Producción

```bash
# Build
cd /home/nosvers/tablero/web && npm run build

# Despliegue: nginx ya sirve dist/. Forzar refresh con cache-bust
ssh root@srv1313138.hstgr.cloud "systemctl restart nosvers-mcp"

# Verificar
curl https://tablero.72.61.160.108.nip.io/tablero/api/v2/health | jq
```

## Smoke test del WS

```bash
# Obtener token (re-usa el flujo de PWA voz; el JWT vale para cockpit también)
TOKEN=$(curl -s -X POST https://nosvers.com/voz/api/login \
  -d '{"user":"angel","pass":"..."}' | jq -r .access_token)

# wscat ya instalado en el VPS si está; si no:
npm install -g wscat

wscat -c "wss://tablero.72.61.160.108.nip.io/tablero/api/v2/ws?token=$TOKEN"
> {"type":"subscribe","channel":"health"}
# Debe recibir {"type":"snapshot","channel":"health","payload":{...}} en <2s
```

## Definition of done

- [ ] `/tablero/api/v2/health` retorna 200 con datos psutil reales
- [ ] WS handshake exitoso con JWT válido; close 4401 sin token
- [ ] 12 widgets renderizan; Tier 1+2 con datos reales, Tier 3 con placeholder ok
- [ ] Drag-to-rearrange persiste por sub en localStorage
- [ ] Reconexión WS automática verificada (`systemctl restart nosvers-mcp`)
- [ ] Bundle gz total ≤ 1.5MB
- [ ] 0 regresiones en endpoints `/tablero/api/v2/*` originales

## Rollback

Si el deploy rompe Fase B+C:
```bash
cd /home/nosvers && git revert HEAD~5..HEAD --no-edit && systemctl restart nosvers-mcp
```

El Dashboard B+C es `/` y se sirve del bundle base; el cockpit es `/cockpit`
codesplit, así que un fallo del cockpit no debería tirar `/`.
