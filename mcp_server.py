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
    uvicorn.run(app, host="0.0.0.0", port=8765, log_level="warning")
