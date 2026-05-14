#!/usr/bin/env python3
"""
NosVers · MCP Server
Conecta Claude.ai directamente al VPS sin copiar nada.

Instalar en el VPS:
  pip3 install fastmcp uvicorn python-dotenv requests --break-system-packages

Arrancar:
  python3 /home/nosvers/mcp_server.py

Añadir en Claude.ai → Settings → Profile → Integrations → Add MCP Server:
  URL: https://nosvers.com/mcp
  Token: valor de MCP_TOKEN en tu .env
"""

import os, json, subprocess, logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import requests as req

load_dotenv('/home/nosvers/.env')

# ── CONFIG ────────────────────────────────────────────────
MCP_TOKEN      = os.getenv('MCP_TOKEN', 'nosvers-mcp-2026')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN', '')
ANGEL_CHAT_ID  = os.getenv('ANGEL_CHAT_ID', '-1003801137875')
APP_URL        = os.getenv('APP_URL', 'https://nosvers.com/granja/api.php')
APP_TOKEN      = os.getenv('APP_TOKEN', '')
WP_URL         = os.getenv('WP_URL', 'https://nosvers.com/wp-json/wp/v2/')
WP_USER        = os.getenv('WP_USER', 'claude_nosvers')
WP_PASS        = os.getenv('WP_PASS', '')
VAULT_PATH     = Path('/home/nosvers/public_html/knowledge_base')
HOSTINGER_USER = os.getenv('HOSTINGER_USER', 'u859094205')
HOSTINGER_PASS = os.getenv('HOSTINGER_PASS', '')
HOSTINGER_PORT = os.getenv('HOSTINGER_PORT', '65002')
HOSTINGER_HOST = os.getenv('HOSTINGER_HOST', 'nosvers.com')
AGENTS_PATH    = Path('/home/nosvers/agents')
LOG_PATH       = Path('/home/nosvers/logs')
LOG_PATH.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [MCP] %(message)s',
    handlers=[
        logging.FileHandler('/home/nosvers/logs/mcp.log'),
        logging.StreamHandler()
    ]
)
log = logging.getLogger('mcp')

try:
    from fastmcp import FastMCP
except ImportError:
    subprocess.run(["pip3","install","fastmcp","uvicorn","--break-system-packages","-q"])
    from fastmcp import FastMCP

# ── SERVIDOR ──────────────────────────────────────────────
mcp = FastMCP(
    "NosVers",
    instructions="""Eres el Director Ejecutivo de NosVers, ferme lombricole en Dordogne, Francia.
Angel es el CEO. Responde siempre en español, directo y concreto.
Tienes acceso completo al VPS, vault, agentes, WordPress y Telegram.
Ejecuta tareas en el VPS sin que Angel tenga que copiar nada.
Cuando termines algo importante, notifica via Telegram."""
)

# ── HELPERS ───────────────────────────────────────────────
def notify(msg):
    if not TELEGRAM_TOKEN: return False
    try:
        # Try Markdown first
        r = req.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                 json={"chat_id": ANGEL_CHAT_ID, "text": msg, "parse_mode": "Markdown"},
                 timeout=10)
        if r.status_code == 200:
            return True
        # Markdown failed — retry without parse_mode
        log.warning(f"Telegram Markdown failed ({r.status_code}), retrying plain text")
        r2 = req.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                 json={"chat_id": ANGEL_CHAT_ID, "text": msg},
                 timeout=10)
        return r2.status_code == 200
    except Exception as e:
        log.error(f"Telegram: {e}")
        return False

def sh(cmd, timeout=60):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return {"out": r.stdout[:3000], "err": r.stderr[:500], "ok": r.returncode == 0}
    except subprocess.TimeoutExpired:
        return {"out": "", "err": f"Timeout {timeout}s", "ok": False}
    except Exception as e:
        return {"out": "", "err": str(e), "ok": False}

# ══════════════════════════════════════════════════════════
#  HERRAMIENTAS
# ══════════════════════════════════════════════════════════

@mcp.tool()
def sistema_estado() -> str:
    """Estado completo del sistema: VPS, servicios, agentes, vault."""
    disco  = sh("df -h / | tail -1 | awk '{print $3\"/\"$2\" (\"$5\")'")
    ram    = sh("free -h | grep Mem | awk '{print $3\"/\"$2}'")
    uptime = sh("uptime -p")
    bot    = sh("systemctl is-active nosvers-bot 2>/dev/null || echo 'no instalado'")
    mcp_s  = sh("systemctl is-active nosvers-mcp 2>/dev/null || echo 'no instalado'")
    vault_n = len(list(VAULT_PATH.rglob("*.md"))) if VAULT_PATH.exists() else 0
    agents_n = len(list(AGENTS_PATH.glob("*.py"))) if AGENTS_PATH.exists() else 0
    crons  = sh("crontab -l 2>/dev/null | grep -c nosvers || echo 0")

    return f"""🌿 **NosVers · Estado**
📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}

**VPS**
• Disco: {disco['out'].strip() or '—'}
• RAM: {ram['out'].strip() or '—'}
• Uptime: {uptime['out'].strip() or '—'}

**Servicios**
• Bot Telegram: {bot['out'].strip()}
• MCP Server: {mcp_s['out'].strip()}
• Cron jobs: {crons['out'].strip()} tareas

**Recursos**
• Agentes: {agents_n} instalados
• Vault: {vault_n} archivos .md
"""

@mcp.tool()
def ejecutar_comando(comando: str, notificar_angel: bool = False) -> str:
    """
    Ejecutar comando bash en el VPS.
    
    Args:
        comando: Comando a ejecutar
        notificar_angel: Si True, envía resultado por Telegram
    """
    log.info(f"CMD: {comando[:80]}")
    r = sh(comando, timeout=60)
    out = r['out'] or r['err'] or '(sin output)'
    ico = "✅" if r['ok'] else "❌"

    if notificar_angel:
        notify(f"{ico} `{comando[:60]}`\n\n{out[:300]}")

    return f"{ico} **Ejecutado:** `{comando[:80]}`\n\n```\n{out[:1500]}\n```"

@mcp.tool()
def vault_leer(categoria: str, archivo: str) -> str:
    """
    Leer archivo de la vault.
    
    Args:
        categoria: contexto | agentes | operaciones | vers | compost | estudios | club
        archivo: nombre sin .md (ej: nosvers-identidad, semana-actual)
    """
    fp = VAULT_PATH / categoria / f"{archivo}.md"
    if fp.exists():
        return f"📄 **{categoria}/{archivo}.md**\n\n{fp.read_text(encoding='utf-8')}"
    try:
        r = req.get(f"{APP_URL}?action=vault_read&category={categoria}&filename={archivo}",
                    headers={'X-App-Token': APP_TOKEN}, timeout=10)
        d = r.json()
        if d.get('content'):
            return f"📄 **{categoria}/{archivo}.md**\n\n{d['content']}"
    except: pass
    return f"❌ No encontrado: {categoria}/{archivo}.md"

@mcp.tool()
def vault_escribir(categoria: str, archivo: str, contenido: str, modo: str = "append") -> str:
    """
    Escribir en la vault.
    
    Args:
        categoria: Categoría del archivo
        archivo: Nombre sin .md
        contenido: Texto a escribir
        modo: append (añadir) | overwrite (reemplazar)
    """
    fp = VAULT_PATH / categoria / f"{archivo}.md"
    fp.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime('%Y-%m-%d %H:%M')

    if modo == 'overwrite' or not fp.exists():
        fp.write_text(f"# {archivo}\n*{ts}*\n\n{contenido}", encoding='utf-8')
    else:
        with open(fp, 'a', encoding='utf-8') as f:
            f.write(f"\n\n---\n*{ts}*\n\n{contenido}")

    return f"✅ Guardado: **{categoria}/{archivo}.md** ({modo})"

@mcp.tool()
def vault_listar(categoria: str = "") -> str:
    """
    Listar archivos de la vault.
    
    Args:
        categoria: Filtrar por categoría (vacío = todas)
    """
    if not VAULT_PATH.exists():
        return "❌ Vault no encontrada en el VPS. Ejecutar: git pull + bash scripts/deploy.sh"

    base = VAULT_PATH / categoria if categoria else VAULT_PATH
    archivos = sorted(base.rglob("*.md")) if base.exists() else []
    if not archivos:
        return f"📂 Vault vacía: {base}"

    lines = [f"📂 **Vault** ({len(archivos)} archivos)\n"]
    cat_act = ""
    for f in archivos:
        cat = f.parent.name
        if cat != cat_act:
            lines.append(f"\n**{cat}/**")
            cat_act = cat
        lines.append(f"  • {f.stem} ({f.stat().st_size}B)")
    return '\n'.join(lines)

@mcp.tool()
def agentes_estado() -> str:
    """Ver estado de todos los agentes: instalados, último log, próximo cron."""
    agentes = ['orchestrator','agt01_visual','agt02_instagram',
               'agt04_seo','agt05_africa','agt06_infoproduct']
    lines = ["🤖 **Estado de Agentes**\n"]
    for ag in agentes:
        instalado = "✅" if (AGENTS_PATH / f"{ag}.py").exists() else "❌"
        logf = LOG_PATH / f"{ag}.log"
        ultimo = "—"
        if logf.exists():
            r = sh(f"tail -1 {logf}")
            ultimo = r['out'].strip()[:60] or "—"
        lines.append(f"**{ag}** {instalado}")
        lines.append(f"  Último: {ultimo}")
    crons = sh("crontab -l 2>/dev/null | grep -E 'agt|orchestrator'")
    lines.append(f"\n**Crons:**\n```\n{crons['out'] or '(ninguno)'}\n```")
    return '\n'.join(lines)

@mcp.tool()
def agente_ejecutar(nombre: str, notificar_angel: bool = True) -> str:
    """
    Ejecutar un agente manualmente.
    
    Args:
        nombre: orchestrator | agt01_visual | agt02_instagram | agt04_seo | agt05_africa | agt06_infoproduct
        notificar_angel: Si True, notifica cuando termine
    """
    validos = ['orchestrator','agt01_visual','agt02_instagram',
               'agt04_seo','agt05_africa','agt06_infoproduct']
    if nombre not in validos:
        return f"❌ Agente desconocido. Disponibles: {', '.join(validos)}"

    venv = "/home/nosvers/venv/bin/python3"
    py = venv if Path(venv).exists() else "python3"
    agent_py = AGENTS_PATH / f"{nombre}.py"

    if not agent_py.exists():
        return f"❌ No instalado: {agent_py}\nEjecutar: bash scripts/deploy.sh"

    log.info(f"Lanzando agente: {nombre}")
    r = sh(f"{py} {agent_py}", timeout=120)
    out = (r['out'] or r['err'] or '(sin output)')[:500]
    ico = "✅" if r['ok'] else "❌"

    if notificar_angel:
        notify(f"{ico} Agente **{nombre}**\n\n{out[:300]}")

    return f"{ico} **{nombre}** ejecutado\n\n```\n{out}\n```"

@mcp.tool()
def agente_logs(nombre: str, lineas: int = 30) -> str:
    """
    Ver logs de un agente.
    
    Args:
        nombre: Nombre del agente
        lineas: Cuántas líneas mostrar
    """
    for logf in [LOG_PATH / f"{nombre}.log", AGENTS_PATH / f"{nombre}.log"]:
        if logf.exists():
            r = sh(f"tail -{lineas} {logf}")
            return f"📋 **{nombre} logs**\n\n```\n{r['out']}\n```"
    return f"❌ Sin logs para: {nombre}"

@mcp.tool()
def wp_crear_post(titulo: str, contenido: str, estado: str = "draft") -> str:
    """
    Crear post en WordPress nosvers.com.
    
    Args:
        titulo: Título del post
        contenido: Contenido (texto plano o HTML)
        estado: draft (para aprobación) | publish
    """
    bloques = "\n\n".join([
        f"<!-- wp:paragraph --><p>{p}</p><!-- /wp:paragraph -->"
        for p in contenido.split('\n\n') if p.strip()
    ]) if '<!-- wp:' not in contenido else contenido

    try:
        r = req.post(f"{WP_URL}posts",
                     auth=(WP_USER, WP_PASS),
                     json={"title": titulo, "content": bloques, "status": estado},
                     timeout=15)
        d = r.json()
        if r.status_code in [200, 201]:
            pid, url = d.get('id',''), d.get('link','')
            if estado == 'draft':
                notify(f"📝 Borrador creado: **{titulo}**\nID: {pid}\n{url}")
            return f"✅ Post {'publicado' if estado=='publish' else 'guardado como borrador'}\n• ID: {pid}\n• URL: {url}"
        return f"❌ WordPress: {d.get('message', str(d))[:200]}"
    except Exception as e:
        return f"❌ Error: {e}"

@mcp.tool()
def git_pull_vps() -> str:
    """Hacer git pull del repo NosVers en el VPS."""
    find = sh("find /home /var/www -name '.git' -maxdepth 5 2>/dev/null | head -3")
    repos = [str(Path(p).parent) for p in find['out'].strip().split('\n') if p.strip()]
    if not repos:
        return "❌ No hay repo git en el VPS"
    results = []
    for repo in repos:
        r = sh(f"cd {repo} && git pull origin main 2>&1")
        results.append(f"📁 `{repo}`\n```\n{r['out'][:300]}\n```")
    return '\n\n'.join(results)

@mcp.tool()
def deploy_vps(notificar_angel: bool = True) -> str:
    """Deploy completo: git pull + instalar dependencias + reiniciar servicios."""
    log.info("Deploy iniciado")
    find = sh("find /home /var/www -name 'deploy.sh' -maxdepth 6 2>/dev/null | head -1")
    deploy_sh = find['out'].strip()

    if deploy_sh:
        r = sh(f"bash {deploy_sh}", timeout=180)
        resultado = r['out'][-800:] or r['err'][:300]
        ico = "✅" if r['ok'] else "❌"
    else:
        r = git_pull_vps()
        resultado = r
        ico = "✅"

    if notificar_angel:
        notify(f"🚀 Deploy NosVers {ico}\n\n{resultado[:400]}")

    return f"🚀 **Deploy {ico}**\n\n```\n{resultado}\n```"

@mcp.tool()
def telegram_enviar(mensaje: str) -> str:
    """Enviar mensaje a Angel via Telegram."""
    ok = notify(mensaje)
    return "✅ Enviado por Telegram" if ok else "❌ Error — verificar TELEGRAM_TOKEN"

# ── HERRAMIENTAS VOZ (asistente personal Angel) ───────────
# feature/001-voice-assistant — añade dia_capturar / dia_contexto / dia_buscar
# Implementación en /home/nosvers/voz/

import json as _voz_json
from voz.capturar import dia_capturar_impl as _voz_capturar_impl
from voz.contexto import dia_contexto_impl as _voz_contexto_impl
from voz.buscar import dia_buscar_impl as _voz_buscar_impl


@mcp.tool()
def dia_capturar(
    texto: str = "",
    audio_b64: str = "",
    ts_iso: str = "",
    etiqueta: str = "auto",
    origen: str = "otro",
    autor: str = "angel",
    device_label: str = "mcp_directo",
    client_uuid: str = "",
) -> str:
    """Captura una nota del día en el vault común (Angel + África) con
    clasificación automática.

    Args:
        texto: texto ya transcrito. Si vacío y audio_b64 viene, se transcribe.
        audio_b64: audio Opus en base64 (alternativa a texto).
        ts_iso: timestamp ISO 8601 del momento de dictado. Vacío = ahora().
        etiqueta: 'auto' (Haiku decide) o una de
                  trabajo|nosvers|familia|mental|idea|otro.
        origen: voz_movil | voz_linux | texto_directo | otro.
        autor: angel | africa (BRIEF §14). Default angel.
        device_label: identificador del dispositivo origen.
        client_uuid: UUID del cliente para idempotencia (opcional).

    Returns:
        JSON string con archivo, ts, autor, etiqueta_aplicada, confianza, etc.
    """
    res = _voz_capturar_impl(
        texto=texto, audio_b64=audio_b64, ts_iso=ts_iso, etiqueta=etiqueta,
        origen=origen, autor=autor, device_label=device_label, client_uuid=client_uuid,
    )
    return _voz_json.dumps(res, ensure_ascii=False)


@mcp.tool()
def dia_contexto(
    rango_dias: int = 7,
    incluir_calendario: bool = True,
    incluir_estado_agentes: bool = True,
    etiquetas_filtro: str = "",
    autor: str = "",
) -> str:
    """Devuelve síntesis del contexto reciente desde el vault común.

    Args:
        rango_dias: 1..30 días hacia atrás (default 7).
        incluir_calendario: si True, intenta leer eventos próximos.
        incluir_estado_agentes: si True, incluye resumen de agentes activos.
        etiquetas_filtro: CSV de etiquetas para filtrar (vacío = todas).
        autor: filtra por autor ("angel"|"africa"). Vacío = ambos (BRIEF §14).

    Returns:
        JSON string con sintesis (markdown), calendario, agentes.
    """
    res = _voz_contexto_impl(
        rango_dias=rango_dias, incluir_calendario=incluir_calendario,
        incluir_estado_agentes=incluir_estado_agentes,
        etiquetas_filtro=etiquetas_filtro, autor=autor,
    )
    return _voz_json.dumps(res, ensure_ascii=False)


@mcp.tool()
def dia_buscar(
    query: str,
    desde: str = "",
    hasta: str = "",
    limite: int = 20,
    etiqueta: str = "",
    autor: str = "",
) -> str:
    """Busca un término en las notas del diario común.

    Args:
        query: término o frase (case-insensitive, ignora diacríticos).
        desde: fecha ISO YYYY-MM-DD inclusive (vacío = sin límite).
        hasta: fecha ISO YYYY-MM-DD inclusive (vacío = hoy).
        limite: máximo de resultados (1-100, default 20).
        etiqueta: filtrar por una etiqueta concreta.
        autor: filtra por autor ("angel"|"africa"). Vacío = ambos (BRIEF §14).

    Returns:
        JSON string con resultados ordenados por ts descendente.
    """
    res = _voz_buscar_impl(
        query=query, desde=desde, hasta=hasta, limite=limite,
        etiqueta=etiqueta, autor=autor,
    )
    return _voz_json.dumps(res, ensure_ascii=False)


# ── SYSTEMD SERVICE ───────────────────────────────────────
SERVICE = """[Unit]
Description=NosVers MCP Server
After=network.target

[Service]
User=root
WorkingDirectory=/home/nosvers
ExecStart=/home/nosvers/venv/bin/python3 /home/nosvers/mcp_server.py
Restart=always
RestartSec=5
EnvironmentFile=/home/nosvers/.env

[Install]
WantedBy=multi-user.target
"""

# ── NGINX CONFIG ──────────────────────────────────────────
NGINX_CONF = """# Añadir dentro del server block de nosvers.com
location /mcp {
    proxy_pass http://localhost:8765;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection 'upgrade';
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_cache_bypass $http_upgrade;
}
"""

if __name__ == "__main__":
    import uvicorn

    # Guardar archivos de configuración
    Path('/home/nosvers/nosvers-mcp.service').write_text(SERVICE)
    Path('/home/nosvers/nginx-mcp.conf').write_text(NGINX_CONF)

    instrucciones = f"""
=== NosVers MCP Server ===

Para instalar el servicio systemd:
  cp /home/nosvers/nosvers-mcp.service /etc/systemd/system/
  systemctl daemon-reload
  systemctl enable nosvers-mcp
  systemctl start nosvers-mcp

Para añadir la ruta /mcp en Nginx:
  Ver /home/nosvers/nginx-mcp.conf

Para conectar en Claude.ai:
  Settings → Profile → Integrations → Add MCP Server
  URL: https://nosvers.com/mcp
  Token: {MCP_TOKEN}

Herramientas disponibles:
  sistema_estado       → estado VPS completo
  ejecutar_comando     → bash en el VPS
  vault_leer/escribir/listar → gestión vault
  agentes_estado       → estado de todos los agentes
  agente_ejecutar      → lanzar agente manualmente
  agente_logs          → ver logs de agente
  wp_crear_post        → crear post WordPress
  git_pull_vps         → git pull del repo
  deploy_vps           → deploy completo
  telegram_enviar      → notificar a Angel
"""
    Path('/home/nosvers/MCP_INSTRUCCIONES.txt').write_text(instrucciones)
    log.info("🌿 NosVers MCP Server")
    log.info("   Puerto: 8765")
    log.info("   URL Claude.ai: https://nosvers.com/mcp")
    log.info(f"   Token: {MCP_TOKEN}")
    log.info("   Instrucciones: /home/nosvers/MCP_INSTRUCCIONES.txt")

    app = mcp.http_app()
    # Monta endpoints REST de la PWA de voz (mismo binario, comparte auth)
    try:
        from voz.rest import ROUTES as _voz_routes
        for _r in _voz_routes:
            app.router.routes.append(_r)
        log.info(f"voz/REST: {len(_voz_routes)} rutas montadas bajo /voz/api/")
    except Exception as _e:
        log.warning(f"voz/REST no montado: {_e}")
    # Monta endpoints REST del Second Brain Dashboard (proyecto 002, Fase A read-only)
    try:
        from tablero.rest import ROUTES as _tablero_routes
        for _r in _tablero_routes:
            app.router.routes.append(_r)
        log.info(f"tablero/REST: {len(_tablero_routes)} rutas montadas bajo /tablero/api/")
    except Exception as _e:
        log.warning(f"tablero/REST no montado: {_e}")
    uvicorn.run(app, host="0.0.0.0", port=8765, log_level="warning")

# ── NUEVAS HERRAMIENTAS — EVOLVE 2026-03-15 ──────────────

@mcp.tool()
def drive_listar(carpeta: str = "root") -> str:
    """Listar imágenes en carpetas Google Drive de NosVers.
    
    Args:
        carpeta: root | instagram | vers | huerto | general | jardin | produits | gusanos | cultures | contexto_ia | biodiversite | animaux | africa | neuvic
    """
    api_key = os.getenv('GOOGLE_API_KEY', '')
    if not api_key:
        return "❌ GOOGLE_API_KEY no configurada"
    
    # Map folder names to IDs
    folders = {}
    for key, val in os.environ.items():
        if key.startswith('DRIVE_FOLDER_') or key.startswith('DRIVE_LEGACY_'):
            name = key.replace('DRIVE_FOLDER_', '').replace('DRIVE_LEGACY_', '').lower()
            if name != 'id':  # skip DRIVE_FOLDER_ID
                folders[name] = val
    folders['root'] = os.getenv('DRIVE_FOLDER_ID', os.getenv('DRIVE_LEGACY_ROOT', ''))
    
    folder_id = folders.get(carpeta, '')
    if not folder_id:
        return f"❌ Carpeta '{carpeta}' no encontrada. Disponibles: {', '.join(sorted(folders.keys()))}"
    
    try:
        url = f"https://www.googleapis.com/drive/v3/files?q='{folder_id}'+in+parents&key={api_key}&fields=files(id,name,mimeType)&pageSize=50"
        r = req.get(url, timeout=15)
        data = r.json()
        files = data.get('files', [])
        if not files:
            return f"📁 {carpeta}: vacía"
        
        result = f"📁 **{carpeta}** — {len(files)} archivos\n\n"
        for f in files:
            icon = "📁" if "folder" in f.get('mimeType', '') else "🖼️"
            result += f"{icon} {f['name']} (`{f['id']}`)\n"
        return result
    except Exception as e:
        return f"❌ Error: {e}"


@mcp.tool()
def drive_descargar(file_id: str, nombre: str = "") -> str:
    """Descargar imagen de Google Drive al VPS.
    
    Args:
        file_id: ID del archivo en Drive
        nombre: nombre para guardar (opcional)
    """
    try:
        dest = f"/home/nosvers/uploads/{nombre or file_id + '.jpg'}"
        r = req.get(f"https://drive.google.com/uc?id={file_id}&export=download", timeout=30)
        if r.status_code != 200:
            return f"❌ Error descargando: HTTP {r.status_code}"
        Path(dest).parent.mkdir(parents=True, exist_ok=True)
        with open(dest, 'wb') as f:
            f.write(r.content)
        return f"✅ Descargado: {dest} ({len(r.content)} bytes)"
    except Exception as e:
        return f"❌ Error: {e}"


@mcp.tool()
def deploy_hostinger(archivo_local: str, destino: str) -> str:
    """Deploy archivo del VPS a Hostinger via SCP.
    
    Args:
        archivo_local: ruta en el VPS (ej: /home/nosvers/index.html)
        destino: ruta en Hostinger relativa a public_html (ej: granja/index.html o wp-content/themes/nosvers-v2/style.css)
    """
    import subprocess
    dest_full = f"domains/nosvers.com/public_html/{destino}"
    if not HOSTINGER_PASS:
        return "❌ HOSTINGER_PASS no configurada en .env"
    cmd = f"sshpass -p '{HOSTINGER_PASS}' scp -o StrictHostKeyChecking=no -o PreferredAuthentications=password -o PubkeyAuthentication=no -P {HOSTINGER_PORT} {archivo_local} {HOSTINGER_USER}@{HOSTINGER_HOST}:{dest_full}"
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
        if r.returncode == 0:
            return f"✅ Desplegado: {archivo_local} → {dest_full}"
        return f"❌ Error SCP: {r.stderr}"
    except Exception as e:
        return f"❌ Error: {e}"


@mcp.tool()
def wp_listar_paginas() -> str:
    """Listar todas las páginas publicadas de WordPress."""
    import subprocess
    if not HOSTINGER_PASS:
        return "❌ HOSTINGER_PASS no configurada en .env"
    cmd = f"sshpass -p '{HOSTINGER_PASS}' ssh -o StrictHostKeyChecking=no -o PreferredAuthentications=password -o PubkeyAuthentication=no -p {HOSTINGER_PORT} {HOSTINGER_USER}@{HOSTINGER_HOST} 'cd domains/nosvers.com/public_html && wp --path=. post list --post_type=page --post_status=publish --fields=ID,post_title,post_name --format=table 2>/dev/null'"
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        lines = [l for l in r.stdout.split('\n') if l.strip() and 'Success' not in l and 'cache' not in l.lower()]
        return '\n'.join(lines) if lines else "No pages found"
    except Exception as e:
        return f"❌ Error: {e}"


@mcp.tool()
def fotos_inventario() -> str:
    """Inventario completo de fotos disponibles en todas las fuentes."""
    api_key = os.getenv('GOOGLE_API_KEY', '')
    result = "📸 **Inventario de fotos NosVers**\n\n"
    
    # Drive folders
    folders = {}
    for key, val in os.environ.items():
        if (key.startswith('DRIVE_FOLDER_') or key.startswith('DRIVE_LEGACY_')) and val and len(val) > 10:
            name = key.replace('DRIVE_FOLDER_', '').replace('DRIVE_LEGACY_', '').lower()
            if name != 'id':
                folders[name] = val
    
    result += "**Google Drive:**\n"
    total = 0
    if api_key:
        for name, fid in sorted(folders.items()):
            try:
                url = f"https://www.googleapis.com/drive/v3/files?q='{fid}'+in+parents+and+mimeType+contains+'image'&key={api_key}&fields=files(id)&pageSize=100"
                r = req.get(url, timeout=10)
                count = len(r.json().get('files', []))
                total += count
                result += f"  📁 {name}: {count} images\n"
            except:
                result += f"  📁 {name}: error\n"
    else:
        result += "  ⚠️ GOOGLE_API_KEY no configurada\n"
    
    # Local uploads
    uploads = Path('/home/nosvers/uploads')
    local_count = 0
    if uploads.exists():
        for d in uploads.iterdir():
            if d.is_dir():
                count = len(list(d.glob('*.*')))
                if count > 0:
                    result += f"\n**Local ({d.name}):** {count} files"
                    local_count += count
    
    result += f"\n\n**Total:** {total + local_count} images disponibles"
    return result


# ══════════════════════════════════════════════════════════
#  CLAUDIO JARVIS — Fase 1 (Proyecto 005)
#  Familia · finanzas · compras · menús · coche · documentos · salud · casa
# ══════════════════════════════════════════════════════════
#
# Bloque protegido: si claudio_tools falla al importar, MCP arranca igual
# con los tools NosVers intactos y solo se loguea un warning.

try:
    from claudio_tools import (
        identidad as _cl_identidad,
        familia as _cl_familia,
        finanzas as _cl_finanzas,
        compras as _cl_compras,
        menus as _cl_menus,
        coche as _cl_coche,
        casa as _cl_casa,
        documentos as _cl_documentos,
        salud as _cl_salud,
    )

    # ── claudio identidad ──────────────────────────────────────
    @mcp.tool()
    def claudio_recordar(autor: str, hecho: str, importancia: int = 5) -> str:
        """Guarda un hecho personal en claudio/memorias/{autor}/YYYY-MM.md.

        Args:
            autor: angel | africa | compartido | bris
            hecho: texto a recordar (1 línea preferida)
            importancia: 1-10 (default 5)
        """
        return _cl_identidad.claudio_recordar(autor, hecho, importancia)

    @mcp.tool()
    def claudio_contexto(autor: str, query: str, limite: int = 10) -> str:
        """Busca memorias relevantes del autor que matchean la query.

        Args:
            autor: angel | africa | compartido | bris
            query: término o frase (case-insensitive, ignora acentos)
            limite: máx resultados (default 10)
        """
        return _cl_identidad.claudio_contexto(autor, query, limite)

    # ── familia ───────────────────────────────────────────────
    @mcp.tool()
    def recordatorio_crear(
        texto: str,
        fecha: str,
        autor: str,
        prioridad: int = 3,
    ) -> str:
        """Crea un recordatorio fechado en familia/recordatorios/.

        Args:
            texto: descripción del recordatorio
            fecha: 'YYYY-MM-DD', 'hoy' o 'mañana'
            autor: angel | africa | compartido
            prioridad: 1 (bajo) a 10 (urgente), default 3
        """
        return _cl_familia.recordatorio_crear(texto, fecha, autor, prioridad)

    @mcp.tool()
    def recordatorios_listar(
        periodo: str = "proximos_7_dias",
        autor: str = "",
    ) -> str:
        """Lista recordatorios activos.

        Args:
            periodo: hoy | mañana | proximos_7_dias | proximos_30_dias | todos
            autor: filtrar por autor (vacío = todos)
        """
        return _cl_familia.recordatorios_listar(periodo, autor)

    @mcp.tool()
    def recordatorio_completar(id_o_slug: str) -> str:
        """Marca un recordatorio como hecho y lo mueve a completados/.

        Args:
            id_o_slug: nombre del archivo sin .md (ej '2026-06-12-cumpleanos-lucia')
        """
        return _cl_familia.recordatorio_completar(id_o_slug)

    @mcp.tool()
    def familia_cumpleanos_listar(meses: int = 12) -> str:
        """Lista cumpleaños de los próximos N meses (lee familia/cumpleanos.md).

        Args:
            meses: 1-12 (default 12)
        """
        return _cl_familia.familia_cumpleanos_listar(meses)

    # ── finanzas ──────────────────────────────────────────────
    @mcp.tool()
    def gasto_anotar(
        monto_eur: float,
        concepto: str,
        categoria: str,
        autor: str,
    ) -> str:
        """Apunta un gasto en finanzas/gastos/YYYY-MM.md.

        Args:
            monto_eur: cantidad en euros
            concepto: descripción corta (ej "gasolina coche")
            categoria: alimentacion|transporte|coche|hogar|ocio|salud|nosvers|ropa|regalos|viajes|otros
            autor: angel | africa (obligatorio)
        """
        return _cl_finanzas.gasto_anotar(monto_eur, concepto, categoria, autor)

    @mcp.tool()
    def gastos_resumen(periodo: str = "mes_actual", categoria: str = "") -> str:
        """Agrega gastos del periodo, por categoría.

        Args:
            periodo: mes_actual | mes_anterior | YYYY-MM | ultimos_30_dias
            categoria: vacío (todas) o una de las categorías válidas
        """
        return _cl_finanzas.gastos_resumen(periodo, categoria)

    @mcp.tool()
    def recurrente_alertar(dias: int = 7) -> str:
        """Lee finanzas/recurrentes.yaml y devuelve cargos próximos en N días.

        Args:
            dias: ventana de alerta (default 7)
        """
        return _cl_finanzas.recurrente_alertar(dias)

    # ── compras ───────────────────────────────────────────────
    @mcp.tool()
    def lista_compras_anadir(
        item: str,
        autor: str,
        cantidad: str = "",
        urgente: bool = False,
    ) -> str:
        """Añade un item a compras/lista_actual.md.

        Args:
            item: producto a comprar
            autor: angel | africa
            cantidad: opcional (ej "1kg", "2 botes")
            urgente: si True prefija ⚠️
        """
        return _cl_compras.lista_compras_añadir(item, autor, cantidad, urgente)

    @mcp.tool()
    def lista_compras_ver() -> str:
        """Devuelve la lista de la compra vigente."""
        return _cl_compras.lista_compras_ver()

    @mcp.tool()
    def lista_compras_completar(item: str) -> str:
        """Marca un item como comprado (lo quita de la lista y lo archiva).

        Args:
            item: nombre completo o parte (case-insensitive)
        """
        return _cl_compras.lista_compras_completar(item)

    @mcp.tool()
    def despensa_estado() -> str:
        """Devuelve el contenido de compras/despensa.yaml por categoría."""
        return _cl_compras.despensa_estado()

    # ── menús ─────────────────────────────────────────────────
    @mcp.tool()
    def menu_sugerir(dia: str = "", ingredientes_disponibles: str = "") -> str:
        """Sugiere recetas filtrando por ingredientes disponibles.

        Args:
            dia: 'YYYY-MM-DD' o vacío (hoy)
            ingredientes_disponibles: CSV (ej "tomate, cebolla, huevo")
        """
        return _cl_menus.menu_sugerir(dia, ingredientes_disponibles)

    @mcp.tool()
    def receta_guardar(
        nombre: str,
        ingredientes: str,
        pasos: str,
        fuente: str = "",
    ) -> str:
        """Guarda una receta en menus/recetas/.

        Args:
            nombre: nombre de la receta
            ingredientes: CSV
            pasos: texto con los pasos
            fuente: origen (ej "abuela", "internet")
        """
        return _cl_menus.receta_guardar(nombre, ingredientes, pasos, fuente)

    # ── coche ─────────────────────────────────────────────────
    @mcp.tool()
    def coche_estado() -> str:
        """Resumen del coche (ITV, seguro, kilómetros) leído de coche/INDEX.md."""
        return _cl_coche.coche_estado()

    @mcp.tool()
    def coche_evento(
        tipo: str,
        fecha: str,
        monto_eur: float = 0.0,
        notas: str = "",
        autor: str = "angel",
    ) -> str:
        """Registra un evento del coche y actualiza INDEX.md si procede.

        Args:
            tipo: gasolina | mantenimiento | itv | seguro | multa | reparacion | lavado | neumaticos | otros
            fecha: 'YYYY-MM-DD' o 'hoy'
            monto_eur: gasto en euros (0 si no aplica)
            notas: detalles libres
            autor: angel | africa
        """
        return _cl_coche.coche_evento(tipo, fecha, monto_eur, notas, autor)

    # ── casa ──────────────────────────────────────────────────
    @mcp.tool()
    def casa_mantenimiento_anotar(
        tarea: str,
        fecha: str = "",
        proximo: str = "",
        autor: str = "angel",
    ) -> str:
        """Apunta una tarea de mantenimiento en casa/mantenimiento.md.

        Args:
            tarea: qué se hizo / se hará
            fecha: 'YYYY-MM-DD' o 'hoy' (default hoy)
            proximo: fecha estimada de la próxima vez (opcional)
            autor: angel | africa
        """
        return _cl_casa.casa_mantenimiento_anotar(tarea, fecha, proximo, autor)

    # ── documentos ────────────────────────────────────────────
    @mcp.tool()
    def documento_anotar(
        tipo: str,
        contenido_texto: str,
        fecha: str,
        fuente: str,
        autor: str,
    ) -> str:
        """Guarda un documento en documentos/<tipo>/.

        Args:
            tipo: factura | contrato | seguro | impuesto
            contenido_texto: cuerpo del documento (texto plano)
            fecha: 'YYYY-MM-DD' del documento
            fuente: emisor (ej "EDF", "AXA")
            autor: angel | africa
        """
        return _cl_documentos.documento_anotar(
            tipo, contenido_texto, fecha, fuente, autor
        )

    @mcp.tool()
    def documentos_buscar(query: str, limite: int = 20) -> str:
        """Búsqueda en documentos/ (grep recursivo, case-insensitive).

        Args:
            query: término o frase
            limite: máx resultados (default 20)
        """
        return _cl_documentos.documentos_buscar(query, limite)

    # ── salud ─────────────────────────────────────────────────
    @mcp.tool()
    def medicacion_recordar() -> str:
        """Devuelve qué medicación toca hoy (lee salud/medicacion.yaml)."""
        return _cl_salud.medicacion_recordar()

    @mcp.tool()
    def cita_medica_anotar(
        quien: str,
        especialista: str,
        fecha: str,
        notas: str = "",
        autor: str = "",
    ) -> str:
        """Apunta una cita médica en salud/citas/.

        Args:
            quien: angel | africa | bris
            especialista: ej "veterinario", "ginecóloga"
            fecha: 'YYYY-MM-DD' o 'YYYY-MM-DD HH:MM'
            notas: detalles libres
            autor: angel | africa (OBLIGATORIO en salud)
        """
        return _cl_salud.cita_medica_anotar(quien, especialista, fecha, notas, autor)

    log.info("claudio_tools: 22 tools nuevos registrados (familia/finanzas/compras/menus/coche/casa/documentos/salud/identidad)")

except Exception as _cl_err:  # pragma: no cover
    log.warning(f"claudio_tools no cargado: {_cl_err}")

