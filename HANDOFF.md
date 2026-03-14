# HANDOFF.md — Estado de sesión Claude Code
> Lee este archivo AL INICIO de cada sesión antes de hacer cualquier cosa.
> Actualízalo AL FINAL de cada tarea o cuando la sesión se corte.

---

## 🔴 ÚLTIMA SESIÓN CORTADA

**Qué estaba haciendo:** Configurando redirección Nginx para el MCP server
**Dónde se quedó:** mcp_server.py instalado, faltaba location /mcp en Nginx
**Próximo paso exacto:** Ver sección TAREA INMEDIATA abajo

---

## 🔧 TAREA INMEDIATA AL ARRANCAR

### Terminar MCP server (sesión cortada aquí)

```bash
# 1. Verificar que mcp_server.py está en el VPS
find /home/nosvers -name "mcp_server.py" 2>/dev/null

# 2. Si no está, hacer git pull
cd $(find /home /var/www -name ".git" -maxdepth 5 2>/dev/null | head -1 | xargs dirname) && git pull origin main

# 3. Instalar dependencias
pip3 install fastmcp uvicorn python-dotenv requests --break-system-packages -q

# 4. Añadir MCP_TOKEN al .env si no está
grep -q MCP_TOKEN /home/nosvers/.env || echo "MCP_TOKEN=nosvers-mcp-2026" >> /home/nosvers/.env

# 5. Arrancar el servidor (genera el .service automáticamente)
python3 /home/nosvers/mcp_server.py &
sleep 3

# 6. Instalar como servicio systemd
cp /home/nosvers/nosvers-mcp.service /etc/systemd/system/ 2>/dev/null && \
  systemctl daemon-reload && \
  systemctl enable nosvers-mcp && \
  systemctl restart nosvers-mcp

# 7. Encontrar config Nginx de nosvers.com
NGINX_CONF=$(grep -rl "nosvers.com" /etc/nginx/sites-enabled/ /etc/nginx/conf.d/ 2>/dev/null | head -1)
echo "Config: $NGINX_CONF"

# 8. Añadir proxy /mcp antes del cierre del server block
# Insertar justo antes del último "}" del server block:
#
# location /mcp {
#     proxy_pass http://127.0.0.1:8765;
#     proxy_http_version 1.1;
#     proxy_set_header Host $host;
#     proxy_set_header X-Real-IP $remote_addr;
#     proxy_read_timeout 300;
# }

# 9. Verificar y recargar nginx
nginx -t && systemctl reload nginx

# 10. Test final
curl -s https://nosvers.com/mcp | head -5

# 11. Notificar a Angel
python3 -c "
import requests, os
from dotenv import load_dotenv
load_dotenv('/home/nosvers/.env')
tok = os.getenv('TELEGRAM_TOKEN','')
if tok:
    requests.post(f'https://api.telegram.org/bot{tok}/sendMessage',
        json={'chat_id':'5752097691','text':'MCP Server activo. Claude.ai conectado al VPS.\n\nAnadir en Claude.ai Settings -> Integrations:\nURL: https://nosvers.com/mcp\nToken: nosvers-mcp-2026'})
    print('Telegram enviado')
"
```

---

## 🌺 GUARDAR RESPUESTAS DE AFRICA EN VAULT

África respondió las 5 preguntas el 13/03/2026. Guardar en vault:

Categoría: agentes/agt05_africa
Archivo: _memoria
Contenido:
```
Respuestas de África recibidas 2026-03-13

P1 - Primer vistazo al suelo:
Mira la variedad de plantas que hay. Se fija en el suelo, coge tierra y la huele. Observa si hay vida minúscula.

P2 - 5 cosas que observa:
El color, el olor. Si se desgrana fácilmente, si tiene vida. Cómo absorbe el agua.

P3 - Señal de suelo en mal estado (ejemplo real):
Bancal con tierra compactada (se ve musgo), drena mal, llena de piedras. Crecen adventicias con más fuerza que lo cultivado. La tierra se compacta con cuatro gotas que caen.

P4 - Señal de suelo mejorando:
Ese mismo bancal ahora: suelo granulado, tono café, no cuesta plantar nada y todo crece. Está lleno de lombrices.

P5 - Consejo para quien nunca miró su suelo:
"Que pare un instante y observe su suelo. Si no ve nada, que lo cubra (cartón, paja, heno...), que lo riegue y que deje que opere la magia. Que lo destape pasado un rato y vea la vida que hay. Ellos serán los que acojan sus siembras y nutran sus plantas."

ESTADO: PDF #1 listo para generar con este contenido
```

---

## ✅ COMPLETADO (no repetir)

- api.php con vault_write/read/list
- chat.html — chat Angel + África con soporte fotos
- hq.html — centro de operaciones con vista agentes
- mcp_server.py — MCP server puerto 8765
- agents/ — orchestrator + agt01 al agt06
- bot/bot.py + nosvers-bot.service
- scripts/deploy.sh
- .claude/settings.json — permisos sin preguntar
- vault/ — 16 archivos contexto/memoria por agente
- NOSVERS_CONTEXT_COMPLETO.md
- HANDOFF.md (este archivo)

---

## 📋 PENDIENTE (en orden)

1. MCP server — terminar Nginx ← AQUÍ SE CORTÓ
2. Bot Telegram — verificar running
3. Vault en VPS — verificar 16 archivos en knowledge_base/
4. Cron jobs — verificar instalados
5. PDF #1 África — generar con sus respuestas

---

## 🔐 CREDENCIALES

```
VPS: root@72.61.160.108 / Hm#3cl#p&NWD@HcbdY4c
WordPress user: claude_nosvers
WordPress pass: fkLzcfDHAE8i6WZQEUCVCvY3
GitHub repo: Ngel24190-s/nosvers-app
Angel Telegram ID: 5752097691
App URL: https://nosvers.com/granja/api.php
MCP Token: nosvers-mcp-2026
```

---

## 📁 ESTRUCTURA VPS OBJETIVO

```
/home/nosvers/
├── public_html/
│   ├── api.php
│   ├── chat.html
│   ├── hq.html
│   └── knowledge_base/     (16 archivos .md)
├── agents/                 (7 archivos .py)
├── bot/bot.py
├── mcp_server.py           (puerto 8765)
├── venv/
└── .env
```

---

## 🔄 PROTOCOLO HANDOFF — SEGUIR SIEMPRE

**Al arrancar:**
1. Leer este archivo primero
2. `systemctl status nosvers-bot nosvers-mcp 2>/dev/null`
3. Retomar desde TAREA INMEDIATA

**Al terminar una tarea:**
1. Mover tarea de PENDIENTE a COMPLETADO
2. Actualizar TAREA INMEDIATA
3. `git add HANDOFF.md && git commit -m "handoff: actualizar estado" && git push`

**Si la sesión se va a cortar:**
1. Escribir exactamente en qué línea del script está
2. `git push` inmediatamente

---

*NosVers Director Ejecutivo · Actualizado: 2026-03-14*
