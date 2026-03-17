# HANDOFF — NosVers · 2026-03-14

## Estado actual

### Infraestructura
- VPS 72.61.160.108: activo, 13 agentes desplegados, 10 crontabs
- Hostinger shared: nosvers.com, autodeploy desde GitHub
- Bot Telegram: @nosvers_hq_bot activo
- Syncthing: vault sincronizada
- SSH Hostinger: u859094205@nosvers.com:65002

### Frontend (index.html)
- Vista Angel: HQ oscuro con 6 tarjetas de agentes, panel lateral chat, tabs HQ/Chat/Vault/Logs + secciones existentes
- Vista África: tema claro violeta, chat francés, botones Foto + PDF
- Login routing: angel→HQ, africa→vista simplificada
- Endpoint upload_photo en api.php

### Agentes Python (13 total)
| Agente | Archivo | Cron | Personalidad |
|--------|---------|------|-------------|
| Orchestrator | orchestrator.py | Cada hora | El Sargento |
| AGT-00 Intelligence | agt00_intelligence.py | Diario 6h | — |
| AGT-01 Visual | agt01_visual.py | Manual | El Ojo |
| AGT-02 Instagram | agt02_instagram.py | Domingos 10h | La Voz |
| AGT-04 SEO | agt04_seo.py | Lunes 7h | El Investigador |
| AGT-05 África | agt05_africa.py | Cada 6h | La Traductora |
| AGT-06 Infoproduct | agt06_infoproduct.py | Manual | El Arquitecto |
| AGT-07 YouTube | agt07_youtube.py | Martes 10h | — |
| AGT-08 Facebook | agt08_facebook.py | Diario 11h | — |
| AGT-09 Content Director | agt09_content_director.py | Domingos 9h | — |
| AGT-10 Community | agt10_community.py | Cada 4h | — |
| AGT-11 Analytics | agt11_analytics.py | Viernes 18h | — |

### Vault: 26 archivos en 9+ categorías

### Pendiente de Angel
- [ ] Crear grupos Telegram (HQ + Club) + obtener IDs
- [ ] Conectar Obsidian móvil a Syncthing
- [ ] @nosvers en Instagram
- [ ] África: 5 preguntas para PDF + 7 fotos para AGT-01
- [ ] Configurar credenciales Google Drive OAuth2

### Deploy
- Push a GitHub → autodeploy Hostinger
- Agentes: ya en VPS /home/nosvers/agents/
- Ruta Hostinger real: ~/domains/nosvers.com/public_html/granja/
- SSH backup: sshpass -p "$HOSTINGER_PASS" scp -P 65002 [file] u859094205@nosvers.com:domains/nosvers.com/public_html/granja/

## Completado hoy (2026-03-14)
- [x] BLOQUE 1: UI HQ + Vista África (index.html completo)
- [x] BLOQUE 2: 6 nuevos agentes Python creados
- [x] BLOQUE 3: Crontabs configurados para todos
- [x] BLOQUE 4: feedparser instalado
- [x] Personalidades integradas en 6 agentes originales
- [x] endpoint upload_photo en api.php
- [x] WP_URL/WP_USER/WP_PASS en agent_base.py
