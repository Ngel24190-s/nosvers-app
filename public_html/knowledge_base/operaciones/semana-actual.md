# Semana Actual — Mars 2026

## Completado (13-14/03/2026)

### Infraestructura
- [x] Token Telegram regenerado
- [x] Bot Telegram operativo — /statut /pendiente /vault /agentes /run /ask /logs
- [x] Syncthing instalado (GUI: http://72.61.160.108:8384)
- [x] Nginx + PHP-FPM + Caddy en VPS
- [x] ANTHROPIC_API_KEY + APP_TOKEN configurados
- [x] GitHub main actualizado
- [x] Archivos desplegados en Hostinger shared hosting
- [x] chat.html LIVE en nosvers.com/granja/chat.html
- [x] API Claude pública (sin token para chat)

### Agentes
- [x] 7 agentes desplegados + 4 crontabs activos
- [x] Fix bugs en orchestrator.py y agt05_africa.py (vault helpers duplicados)
- [x] 7/7 agentes pasan tests de importación
- [x] test_agents.py creado para validación

### Vault (12 archivos, 9 categorías)
- [x] contexto/nosvers-identidad.md
- [x] contexto/angel-filosofia.md
- [x] operaciones/semana-actual.md
- [x] operaciones/agentes-estado.md
- [x] operaciones/studio-workflow.md
- [x] vers/guia-lombriz-roja.md
- [x] compost/proceso-lombricompostaje.md
- [x] animaux/registro-template.md
- [x] huerto/calendario-dordogne.md
- [x] estudios/soil-food-web.md
- [x] club/club-sol-vivant-info.md
- [x] agentes/plantilla-agentes.md

### Studio V2 → WordPress
- [x] 6 páginas convertidas (Accueil, Extrait, Engrais, Atelier, La Ferme, Contact)
- [x] Templates Bricks Builder (.bricks.php + .bricks.json)
- [x] Templates Gutenberg (.gutenberg.html)
- [x] Script fix para JS template literals
- [x] Documentación en studio-workflow.md

## Pendiente (necesita Angel)

- [ ] Crear grupos Telegram (HQ + Club) + obtener IDs con @getidsbot
- [ ] Conectar Obsidian móvil a Syncthing (Device ID: RNNUSTC-HTY47CV-JOKWFV4-OUIW7CB-4NTEVKD-3A7HJMI-EZ3KNYP-FKAD6QJ)
- [ ] Contraseña DB Hostinger → actualizar config.php en granja/
- [ ] @nosvers creado en Instagram
- [ ] Página lista espera Club en nosvers.com
- [ ] Revisar templates Studio V2 → importar en Bricks Builder

## Pendiente (Angel + África)

- [ ] África responde 5 preguntas → PDF #1 Club
- [ ] África envía 7 fotos → AGT-01 → visuels S1

## Bloqueadores

- DB MySQL no disponible en VPS — acciones de granja solo en nosvers.com
- Mensajes proactivos Telegram bloqueados (proxy bot) — workaround: cola de notificaciones

## URLs operativas

- Chat: https://nosvers.com/granja/chat.html
- Chat VPS: http://72.61.160.108:8080/chat.html
- Syncthing: http://72.61.160.108:8384 (nosvers / NosVers2026!)
- Bot: @nosvers_hq_bot

## Productos disponibles

- Pack Engrais Vert: ~13 sachets (lote test)
- Extrait Vivant kit: listo para venta

## KPIs

- M3: 600€/mes · M6: 2.000€/mes
- Club: M1→20 · M6→100 membres
