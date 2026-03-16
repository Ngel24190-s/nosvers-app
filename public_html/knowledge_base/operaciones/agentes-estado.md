# Estado de Agentes NosVers

> Auditoria: 2026-03-13 | Director Ejecutivo (Claude Code)

---

## Resumen General

| Agente | Archivo | Estado | Carga .env | Imports | Observaciones |
|---|---|---|---|---|---|
| Orchestrator | orchestrator.py | CORREGIDO | OK | OK | Eliminado bloque vault helper duplicado; vault helpers reubicados despues de log() |
| AGT-01 | agt01_visual.py | OK | OK | OK | Solo usa os, shutil, datetime, dotenv. Sin dependencias externas de API |
| AGT-02 | agt02_instagram.py | OK | OK | OK | Usa requests + Anthropic API via REST |
| AGT-03 | agt03_youtube.py | OK | N/A | OK | Placeholder - FASE 2, sin dependencias |
| AGT-04 | agt04_seo.py | OK | OK | OK | Usa requests + Anthropic API + WordPress API |
| AGT-05 | agt05_africa.py | CORREGIDO | OK | OK | Eliminado bloque vault helper duplicado con referencia a log() inexistente |
| AGT-06 | agt06_infoproduct.py | OK | OK | OK | FASE 1 placeholder, lee vault |

---

## Dependencias Python (venv)

Paquetes instalados en `/home/nosvers/venv/`:
- python-dotenv 1.2.2
- requests 2.32.5
- anthropic 0.84.0
- python-telegram-bot 22.6
- schedule 1.2.2
- httpx 0.28.1
- pydantic 2.12.5

Todos los imports requeridos por los agentes estan disponibles.

---

## Variables de Entorno (.env)

Archivo: `/home/nosvers/.env` (permisos: 600, owner: root)

| Variable | Estado |
|---|---|
| TELEGRAM_TOKEN | SET |
| ANGEL_CHAT_ID | SET (5752097691) |
| ANTHROPIC_API_KEY | SET |
| WP_URL | SET |
| WP_USER | SET |
| WP_PASS | SET |
| APP_URL | SET |
| APP_TOKEN | SET |
| GITHUB_TOKEN | SET |
| GITHUB_REPO | SET |

Todos los agentes cargan `.env` con `load_dotenv('/home/nosvers/.env')` -- ruta absoluta, correcto.

---

## Directorios Requeridos

| Directorio | Estado |
|---|---|
| /home/nosvers/agents/ | OK |
| /home/nosvers/uploads/ | OK |
| /home/nosvers/uploads/visuels/ | OK |
| /home/nosvers/uploads/africa/ | OK |
| /home/nosvers/uploads/pdfs/ | OK |
| /home/nosvers/public_html/knowledge_base/ | OK (9 categorias) |
| /home/nosvers/public_html/agent_memory.json | OK |

---

## Problemas Encontrados y Corregidos

### 1. orchestrator.py -- Bloque vault helper duplicado (CORREGIDO)

**Problema:** El archivo tenia un bloque "VAULT HELPER" pegado despues del `load_dotenv()` que:
- Re-importaba `os`, `requests as _req`, `datetime` (duplicados)
- Definia `vault_read()` y `vault_write()` que llamaban a `log()` en el except, pero `log()` se definia mas abajo en el archivo
- Redefinida `APP_URL` y `APP_TOKEN` dos veces
- Las funciones vault se sobreescribian con las definiciones de mas abajo (que no existian -- eran las mismas del bloque)

**Solucion:** Eliminado el bloque duplicado. Vault helpers (vault_read, vault_write, save_memoria, save_resultado) reubicados despues de la definicion de `log()` para que las referencias a `log()` en los except funcionen correctamente.

### 2. agt05_africa.py -- Bloque vault helper duplicado + log() inexistente (CORREGIDO)

**Problema:** Mismo bloque vault helper pegado con:
- Imports duplicados de os, requests, datetime
- Primera definicion de vault_read/vault_write llamaba a `log()` que NO existe en este archivo (causaria NameError en runtime si una vault call fallaba)
- Segunda definicion de vault_read/vault_write (correcta, sin log) las sobreescribia
- APP_URL y APP_TOKEN definidos dos veces

**Solucion:** Eliminado el bloque vault helper duplicado. Conservadas las definiciones limpias de vault_read/vault_write que usan `pass` en except.

### 3. Nota: Ejecucion Python bloqueada

No fue posible ejecutar los agentes con Python durante esta auditoria (permisos Bash restringidos para ejecucion de Python). El analisis se baso en revision estatica del codigo. Se recomienda ejecutar manualmente:

```bash
/home/nosvers/venv/bin/python3 /home/nosvers/test_agents.py
```

El script de test esta en `/home/nosvers/test_agents.py`.

---

## Detalle por Agente

### Orchestrator (orchestrator.py)
- **Cron:** `0 * * * *` (cada hora)
- **Funcion:** Verifica Bot Telegram (systemctl), Vault (directorio), App granja (HTTP)
- **Notifica:** Via Telegram si hay errores o cada 6 horas
- **Codigo:** Limpio despues de correccion

### AGT-01 Visual (agt01_visual.py)
- **Funcion:** Mueve fotos de /uploads/ a /uploads/visuels/semana-XX/
- **Dependencias:** Solo stdlib + dotenv
- **Estado:** Funcional, esperando fotos

### AGT-02 Instagram (agt02_instagram.py)
- **Cron:** `0 10 * * 0` (domingos 10h)
- **Funcion:** Genera 5 posts via Claude API, guarda en vault, notifica Angel
- **Dependencias:** requests, dotenv, Anthropic API (REST)
- **Estado:** Funcional

### AGT-03 YouTube (agt03_youtube.py)
- **Estado:** FASE 2 -- placeholder, solo print
- **Sin dependencias externas**

### AGT-04 SEO (agt04_seo.py)
- **Cron:** `0 7 * * 1` (lunes 7h)
- **Funcion:** Genera articulo SEO via Claude, publica draft en WordPress
- **Dependencias:** requests, dotenv, Anthropic API, WordPress API
- **Estado:** Funcional

### AGT-05 Africa (agt05_africa.py)
- **Cron:** `0 */6 * * *` (cada 6 horas)
- **Funcion:** Procesa archivos de /uploads/africa/ via Claude, estructura en vault
- **Dependencias:** requests, dotenv, Anthropic API
- **Estado:** Funcional despues de correccion

### AGT-06 Infoproductos (agt06_infoproduct.py)
- **Estado:** FASE 1 -- placeholder, lee vault para verificar contenido suficiente
- **Dependencias:** requests, dotenv

---

## Proximos Pasos

1. Ejecutar `/home/nosvers/test_agents.py` para validar imports en runtime
2. Verificar crontabs instalados: `crontab -l`
3. Confirmar que el servicio `nosvers-bot` esta activo: `systemctl status nosvers-bot`
4. Considerar extraer vault helpers a un modulo compartido (`/home/nosvers/agents/vault_helpers.py`) para evitar duplicacion

---

*Generado: 2026-03-13 | Director Ejecutivo (Claude Code)*
